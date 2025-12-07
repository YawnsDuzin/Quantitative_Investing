"""
Data collection and management routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import sys
from pathlib import Path

data_bp = Blueprint('data', __name__)


@data_bp.route('/')
@login_required
def index():
    """Data management dashboard"""
    # Get database info
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.utils.database import get_db

        db = get_db()

        # Get stock count by market from stock_prices table (more reliable)
        market_counts = db.execute_query("""
            SELECT market, COUNT(DISTINCT symbol) as count
            FROM stock_prices
            WHERE market IS NOT NULL
            GROUP BY market
        """)

        kospi_count = 0
        kosdaq_count = 0
        sp500_count = 0
        nasdaq100_count = 0
        if not market_counts.empty:
            for _, row in market_counts.iterrows():
                market = row['market']
                count = row['count']
                if market == 'KOSPI':
                    kospi_count = count
                elif market == 'KOSDAQ':
                    kosdaq_count = count
                elif market == 'S&P500':
                    sp500_count = count
                elif market == 'NASDAQ100':
                    nasdaq100_count = count
                elif market in ['NYSE', 'US']:
                    # Legacy US market data - count as S&P500
                    sp500_count += count
                elif market in ['NASDAQ', 'NMS', 'NGM', 'NCM']:
                    # Legacy NASDAQ data - count as NASDAQ100
                    nasdaq100_count += count

        # Get date range and total records
        stats = db.execute_query("""
            SELECT COUNT(*) as total, MIN(date) as data_start, MAX(date) as data_end
            FROM stock_prices
        """)

        if not stats.empty and stats.iloc[0]['total'] > 0:
            total_records = stats.iloc[0]['total']
            data_start = stats.iloc[0]['data_start']
            data_end = stats.iloc[0]['data_end']
        else:
            total_records = 0
            data_start = None
            data_end = None

        db_info = {
            'kospi_stocks': kospi_count,
            'kosdaq_stocks': kosdaq_count,
            'sp500_stocks': sp500_count,
            'nasdaq100_stocks': nasdaq100_count,
            'data_start': data_start,
            'data_end': data_end,
            'total_records': total_records
        }
    except Exception as e:
        db_info = {
            'error': str(e)
        }

    return render_template('data/index.html', db_info=db_info)


@data_bp.route('/kr-stocks')
@login_required
def kr_stocks():
    """Korean stocks data page"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.utils.database import get_db

        db = get_db()
        stocks = db.get_stock_info()
        kr_stocks = stocks[stocks['market'].isin(['KOSPI', 'KOSDAQ'])] if not stocks.empty else []

    except Exception as e:
        kr_stocks = []
        flash(f'데이터 로드 오류: {str(e)}', 'error')

    return render_template('data/kr_stocks.html', stocks=kr_stocks)


@data_bp.route('/us-stocks')
@login_required
def us_stocks():
    """US stocks data page"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.utils.database import get_db

        db = get_db()
        stocks = db.get_stock_info()
        us_stocks = stocks[stocks['market'].isin(['NYSE', 'NASDAQ'])] if not stocks.empty else []

    except Exception as e:
        us_stocks = []
        flash(f'데이터 로드 오류: {str(e)}', 'error')

    return render_template('data/us_stocks.html', stocks=us_stocks)


@data_bp.route('/collect/kr', methods=['POST'])
@login_required
def collect_kr():
    """Collect Korean stock data (AJAX) - runs in background"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.data_collection.kr_stock_collector import KoreanStockCollector
        from src.utils.task_manager import get_task_manager

        collector = KoreanStockCollector()
        task_manager = get_task_manager()

        # Get parameters from request
        market = request.json.get('market', 'KOSPI')
        start_date = request.json.get('start_date', '2020-01-01')
        end_date = request.json.get('end_date', datetime.now().strftime('%Y-%m-%d'))

        # Collect stock list
        stocks = collector.get_stock_list(market=market)

        if stocks.empty:
            return jsonify({'error': '종목 목록을 가져올 수 없습니다.'}), 400

        # pykrx uses 'symbol' column, FDR uses 'Code'
        code_col = 'symbol' if 'symbol' in stocks.columns else 'Code'
        # Get limit from request, default to all stocks (no limit)
        limit = request.json.get('limit', 0)
        stock_codes = stocks[code_col].tolist()
        if limit > 0:
            stock_codes = stock_codes[:limit]

        # Create background task
        task_id = task_manager.create_task('kr_stock_collection', total_items=len(stock_codes))

        # Get stock names for stock_info table
        name_col = 'name' if 'name' in stocks.columns else 'Name'
        stock_names = dict(zip(stocks[code_col].tolist(),
                               stocks[name_col].tolist() if name_col in stocks.columns else stocks[code_col].tolist()))

        # Define background collection function
        def collect_stocks_background(task_id, codes, start, end, mkt, names):
            from src.data_collection.kr_stock_collector import KoreanStockCollector
            from src.utils.task_manager import get_task_manager
            from src.utils.database import get_db
            from sqlalchemy import text
            from datetime import datetime
            import time

            collector = KoreanStockCollector()
            tm = get_task_manager()
            db = get_db()

            # Pre-fetch sector mapping for efficiency (optional - can be slow)
            sector_mapping = {}
            try:
                tm.update_task(task_id, current_item='업종 정보 로딩 중...')
                sector_mapping = collector.get_sector_mapping(market=mkt)
            except Exception:
                pass  # Continue without sector info if it fails

            collected_count = 0
            for i, code in enumerate(codes):
                # Check if task was cancelled
                task = tm.get_task(task_id)
                if task and task['status'] == 'cancelled':
                    return f'취소됨: {collected_count}개 수집 완료'

                tm.update_task(task_id, current_item=code, completed_items=i)

                try:
                    df = collector.get_price_data(code, start, end)
                    if not df.empty:
                        df['market'] = mkt
                        db.save_stock_prices(df, if_exists='append')

                        # Get stock name and sector
                        stock_name = names.get(code, code)
                        sector = sector_mapping.get(code)

                        # Save to stock_info table with sector
                        with db.engine.begin() as conn:
                            conn.execute(text("""
                                INSERT OR REPLACE INTO stock_info
                                (symbol, name, market, sector, last_updated)
                                VALUES (:symbol, :name, :market, :sector, :last_updated)
                            """), {
                                'symbol': code,
                                'name': stock_name,
                                'market': mkt,
                                'sector': sector,
                                'last_updated': datetime.now().isoformat()
                            })

                        collected_count += 1
                except Exception as e:
                    pass  # Skip failed stocks

                time.sleep(0.1)  # Rate limiting

            tm.update_task(task_id, completed_items=len(codes))
            return f'{collected_count}개 종목 데이터 수집 완료'

        # Run in background
        task_manager.run_in_background(
            task_id,
            collect_stocks_background,
            stock_codes, start_date, end_date, market, stock_names
        )

        return jsonify({
            'status': 'started',
            'task_id': task_id,
            'total': len(stock_codes),
            'message': f'{len(stock_codes)}개 종목 데이터 수집 시작'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/collect/us', methods=['POST'])
@login_required
def collect_us():
    """Collect US stock data (AJAX) - runs in background"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.data_collection.us_stock_collector import USStockCollector
        from src.utils.task_manager import get_task_manager

        collector = USStockCollector()
        task_manager = get_task_manager()

        # Get parameters from request
        index = request.json.get('index', 'SP500')  # SP500 or NASDAQ100
        start_date = request.json.get('start_date', '2020-01-01')
        end_date = request.json.get('end_date', datetime.now().strftime('%Y-%m-%d'))

        # Get tickers
        try:
            limit = request.json.get('limit', 0)
            if index == 'SP500':
                tickers = collector.get_sp500_tickers()
            else:
                tickers = collector.get_nasdaq100_tickers()
            if limit > 0:
                tickers = tickers[:limit]
        except Exception as e:
            return jsonify({'error': f'종목 목록을 가져올 수 없습니다: {str(e)}'}), 400

        if not tickers:
            return jsonify({'error': '종목 목록을 가져올 수 없습니다.'}), 400

        # Create background task
        task_id = task_manager.create_task('us_stock_collection', total_items=len(tickers))

        # Define background collection function
        def collect_stocks_background(task_id, ticker_list, start, end, idx):
            from src.data_collection.us_stock_collector import USStockCollector
            from src.utils.task_manager import get_task_manager
            from src.utils.database import get_db
            from sqlalchemy import text
            from datetime import datetime
            import time

            collector = USStockCollector()
            tm = get_task_manager()
            db = get_db()

            # Use index name (SP500 or NASDAQ100) as market identifier
            market_name = 'S&P500' if idx == 'SP500' else 'NASDAQ100'

            collected_count = 0
            for i, ticker in enumerate(ticker_list):
                # Check if task was cancelled
                task = tm.get_task(task_id)
                if task and task['status'] == 'cancelled':
                    return f'취소됨: {collected_count}개 수집 완료'

                tm.update_task(task_id, current_item=ticker, completed_items=i)

                try:
                    df = collector.get_price_data(ticker, start, end)
                    if not df.empty:
                        # Override market with index name
                        df['market'] = market_name
                        db.save_stock_prices(df, if_exists='append')

                        # Get stock info (name, sector, industry) from yfinance
                        stock_info = collector.get_stock_info(ticker)
                        stock_name = stock_info.get('name', ticker)
                        sector = stock_info.get('sector')
                        industry = stock_info.get('industry')

                        # Save to stock_info table with index-based market
                        with db.engine.begin() as conn:
                            conn.execute(text("""
                                INSERT OR REPLACE INTO stock_info
                                (symbol, name, market, sector, industry, last_updated)
                                VALUES (:symbol, :name, :market, :sector, :industry, :last_updated)
                            """), {
                                'symbol': ticker,
                                'name': stock_name,
                                'market': market_name,
                                'sector': sector,
                                'industry': industry,
                                'last_updated': datetime.now().isoformat()
                            })

                        collected_count += 1
                except Exception as e:
                    pass  # Skip failed stocks

                # Rate limiting - longer delay to avoid 429 errors from yfinance
                time.sleep(1.0)

            tm.update_task(task_id, completed_items=len(ticker_list))
            return f'{collected_count}개 종목 데이터 수집 완료'

        # Run in background
        task_manager.run_in_background(
            task_id,
            collect_stocks_background,
            tickers, start_date, end_date, index
        )

        return jsonify({
            'status': 'started',
            'task_id': task_id,
            'total': len(tickers),
            'message': f'{len(tickers)}개 종목 데이터 수집 시작'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/stock/<symbol>')
@login_required
def stock_detail(symbol):
    """Stock detail page"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.utils.database import get_db

        db = get_db()

        # Get stock info
        info = db.get_stock_info(symbol)
        if info.empty:
            flash('종목을 찾을 수 없습니다.', 'error')
            return redirect(url_for('data.index'))

        # Get price data
        prices = db.get_stock_prices(symbol)

        # Get fundamentals
        fundamentals = db.get_fundamentals(symbol)

        return render_template('data/stock_detail.html',
                             info=info.iloc[0] if not info.empty else {},
                             prices=prices,
                             fundamentals=fundamentals)

    except Exception as e:
        flash(f'데이터 로드 오류: {str(e)}', 'error')
        return redirect(url_for('data.index'))


@data_bp.route('/stock/<symbol>/chart-data')
@login_required
def stock_chart_data(symbol):
    """Get stock chart data (AJAX)"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.utils.database import get_db

        db = get_db()
        prices = db.get_stock_prices(symbol)

        if prices.empty:
            return jsonify({'error': '데이터가 없습니다.'}), 404

        # Format for charts
        data = {
            'dates': prices['date'].dt.strftime('%Y-%m-%d').tolist(),
            'open': prices['open'].tolist(),
            'high': prices['high'].tolist(),
            'low': prices['low'].tolist(),
            'close': prices['close'].tolist(),
            'volume': prices['volume'].tolist()
        }

        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/update-all', methods=['POST'])
@login_required
def update_all():
    """Update all stock data"""
    # This would typically be a background task
    flash('데이터 업데이트가 시작되었습니다. 시간이 걸릴 수 있습니다.', 'info')
    return redirect(url_for('data.index'))


@data_bp.route('/export/<symbol>')
@login_required
def export_stock(symbol):
    """Export stock data as CSV"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.utils.database import get_db
        from flask import Response

        db = get_db()
        prices = db.get_stock_prices(symbol)

        if prices.empty:
            flash('데이터가 없습니다.', 'error')
            return redirect(url_for('data.index'))

        csv_data = prices.to_csv(index=False)

        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename={symbol}_data.csv'}
        )

    except Exception as e:
        flash(f'내보내기 오류: {str(e)}', 'error')
        return redirect(url_for('data.index'))
