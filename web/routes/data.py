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

        # Get stock count by market
        kr_count = len(db.get_all_symbols(market='KOSPI')) + len(db.get_all_symbols(market='KOSDAQ'))
        us_count = len(db.get_all_symbols(market='NYSE')) + len(db.get_all_symbols(market='NASDAQ'))

        # Get date range of data
        prices_df = db.get_stock_prices()
        if not prices_df.empty:
            data_start = prices_df['date'].min()
            data_end = prices_df['date'].max()
            total_records = len(prices_df)
        else:
            data_start = None
            data_end = None
            total_records = 0

        db_info = {
            'kr_stocks': kr_count,
            'us_stocks': us_count,
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
    """Collect Korean stock data (AJAX)"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.data_collection.kr_stock_collector import KoreanStockCollector

        collector = KoreanStockCollector()

        # Get parameters from request
        market = request.json.get('market', 'KOSPI')
        start_date = request.json.get('start_date', '2020-01-01')
        end_date = request.json.get('end_date', datetime.now().strftime('%Y-%m-%d'))

        # Collect stock list
        stocks = collector.get_stock_list(market=market)

        if not stocks:
            return jsonify({'error': '종목 목록을 가져올 수 없습니다.'}), 400

        # Limit to first 50 for demo (can be adjusted)
        stock_codes = stocks['Code'].tolist()[:50]

        # Collect data
        result = collector.collect_multiple_stocks(
            stock_codes,
            start_date=start_date,
            end_date=end_date,
            save_to_db=True
        )

        return jsonify({
            'status': 'success',
            'collected': len(stock_codes),
            'message': f'{len(stock_codes)}개 종목 데이터 수집 완료'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/collect/us', methods=['POST'])
@login_required
def collect_us():
    """Collect US stock data (AJAX)"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.data_collection.us_stock_collector import USStockCollector

        collector = USStockCollector()

        # Get parameters from request
        index = request.json.get('index', 'SP500')  # SP500 or NASDAQ100
        start_date = request.json.get('start_date', '2020-01-01')
        end_date = request.json.get('end_date', datetime.now().strftime('%Y-%m-%d'))

        # Get tickers
        if index == 'SP500':
            tickers = collector.get_sp500_tickers()[:50]  # Limit for demo
        else:
            tickers = collector.get_nasdaq100_tickers()[:50]

        if not tickers:
            return jsonify({'error': '종목 목록을 가져올 수 없습니다.'}), 400

        # Collect data
        result = collector.download_bulk_data(
            tickers,
            start_date=start_date,
            end_date=end_date,
            save_to_db=True
        )

        return jsonify({
            'status': 'success',
            'collected': len(tickers),
            'message': f'{len(tickers)}개 종목 데이터 수집 완료'
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
