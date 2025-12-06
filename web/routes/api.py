"""
API routes for AJAX operations
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from web import db
from web.models import BacktestResult, Portfolio, SavedStrategy
import sys
from pathlib import Path

api_bp = Blueprint('api', __name__)


@api_bp.route('/theme', methods=['POST'])
@login_required
def set_theme():
    """Set user theme preference"""
    theme = request.json.get('theme', 'light')
    if theme in ['light', 'dark']:
        current_user.theme = theme
        db.session.commit()
        return jsonify({'status': 'success', 'theme': theme})
    return jsonify({'error': 'Invalid theme'}), 400


@api_bp.route('/dashboard/stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics"""
    stats = {
        'total_backtests': BacktestResult.query.filter_by(user_id=current_user.id).count(),
        'completed_backtests': BacktestResult.query.filter_by(
            user_id=current_user.id, status='completed').count(),
        'total_portfolios': Portfolio.query.filter_by(user_id=current_user.id).count(),
        'total_strategies': SavedStrategy.query.filter_by(user_id=current_user.id).count()
    }

    # Best performing backtest
    best = BacktestResult.query.filter_by(user_id=current_user.id)\
        .filter(BacktestResult.sharpe_ratio.isnot(None))\
        .order_by(BacktestResult.sharpe_ratio.desc()).first()

    if best:
        stats['best_strategy'] = {
            'name': best.name,
            'sharpe_ratio': best.sharpe_ratio,
            'annual_return': best.annual_return
        }

    return jsonify(stats)


@api_bp.route('/portfolio-optimizer', methods=['POST'])
@login_required
def optimize_portfolio():
    """Run portfolio optimization"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.portfolio.portfolio_optimizer import PortfolioOptimizer
        from src.utils.database import get_db
        import pandas as pd
        import numpy as np

        data = request.json
        symbols = data.get('symbols', [])
        method = data.get('method', 'mean_variance')
        objective = data.get('objective', 'sharpe')

        if not symbols or len(symbols) < 2:
            return jsonify({'error': '최소 2개 이상의 종목을 선택해주세요.'}), 400

        # Get price data
        quant_db = get_db()
        all_prices = quant_db.get_stock_prices(symbols)

        if all_prices.empty:
            return jsonify({'error': '가격 데이터가 없습니다.'}), 400

        # Pivot to get returns
        prices_pivot = all_prices.pivot(index='date', columns='symbol', values='close')
        returns = prices_pivot.pct_change().dropna()

        # Run optimization
        optimizer = PortfolioOptimizer(returns)

        if method == 'equal_weight':
            weights = optimizer.optimize_equal_weights()
        else:
            weights = optimizer.optimize_mean_variance(objective=objective)

        metrics = optimizer.get_portfolio_metrics(weights)

        result = {
            'weights': {sym: float(w) for sym, w in zip(symbols, weights)},
            'expected_return': float(metrics['expected_return']),
            'volatility': float(metrics['volatility']),
            'sharpe_ratio': float(metrics['sharpe_ratio'])
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/stock-search')
@login_required
def stock_search():
    """Search stocks"""
    query = request.args.get('q', '')
    market = request.args.get('market', 'all')

    if len(query) < 1:
        return jsonify([])

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.utils.database import get_db

        db = get_db()
        stocks = db.get_stock_info()

        if stocks.empty:
            return jsonify([])

        # Filter by query
        mask = (
            stocks['symbol'].str.contains(query, case=False, na=False) |
            stocks['name'].str.contains(query, case=False, na=False)
        )

        if market != 'all':
            if market == 'KR':
                mask &= stocks['market'].isin(['KOSPI', 'KOSDAQ'])
            elif market == 'US':
                mask &= stocks['market'].isin(['NYSE', 'NASDAQ'])

        results = stocks[mask].head(20).to_dict('records')
        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/indicators/<symbol>')
@login_required
def get_indicators(symbol):
    """Get technical indicators for a stock"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.utils.database import get_db
        from src.data_processing.indicators import TechnicalIndicators

        quant_db = get_db()
        prices = quant_db.get_stock_prices(symbol)

        if prices.empty:
            return jsonify({'error': '데이터가 없습니다.'}), 404

        # Calculate indicators
        indicators = TechnicalIndicators(prices)

        result = {
            'sma_20': indicators.sma(20).iloc[-1] if len(indicators.sma(20)) > 0 else None,
            'sma_50': indicators.sma(50).iloc[-1] if len(indicators.sma(50)) > 0 else None,
            'sma_200': indicators.sma(200).iloc[-1] if len(indicators.sma(200)) > 0 else None,
            'rsi': indicators.rsi().iloc[-1] if len(indicators.rsi()) > 0 else None,
            'macd': indicators.macd()['macd'].iloc[-1] if 'macd' in indicators.macd() else None
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/factor-scores/<symbol>')
@login_required
def get_factor_scores(symbol):
    """Get factor scores for a stock"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.utils.database import get_db
        from src.data_processing.feature_engineering import FactorCalculator

        quant_db = get_db()
        prices = quant_db.get_stock_prices(symbol)
        fundamentals = quant_db.get_fundamentals(symbol)

        if prices.empty:
            return jsonify({'error': '데이터가 없습니다.'}), 404

        # Calculate factors
        calculator = FactorCalculator(prices, fundamentals)

        result = {
            'momentum': calculator.momentum_factor(),
            'value_pbr': calculator.value_pbr_factor() if not fundamentals.empty else None,
            'value_per': calculator.value_per_factor() if not fundamentals.empty else None,
            'quality_roe': calculator.quality_roe_factor() if not fundamentals.empty else None,
            'volatility': calculator.volatility_factor()
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/backtest/<int:id>/status')
@login_required
def backtest_status(id):
    """Get backtest status"""
    backtest = BacktestResult.query.get_or_404(id)

    if backtest.user_id != current_user.id:
        return jsonify({'error': '접근 권한이 없습니다.'}), 403

    return jsonify({
        'id': backtest.id,
        'status': backtest.status,
        'error': backtest.error_message
    })


@api_bp.route('/strategies/templates')
@login_required
def strategy_templates():
    """Get strategy templates"""
    templates = [
        {
            'id': 'momentum',
            'name': '모멘텀 전략',
            'description': '과거 12개월 수익률이 높은 종목에 투자',
            'factor_weights': {'momentum': 1.0, 'value': 0, 'quality': 0, 'size': 0}
        },
        {
            'id': 'value',
            'name': '가치 전략',
            'description': 'PBR, PER이 낮은 저평가 종목에 투자',
            'factor_weights': {'momentum': 0, 'value': 1.0, 'quality': 0, 'size': 0}
        },
        {
            'id': 'quality',
            'name': '퀄리티 전략',
            'description': 'ROE가 높고 부채비율이 낮은 우량 종목에 투자',
            'factor_weights': {'momentum': 0, 'value': 0, 'quality': 1.0, 'size': 0}
        },
        {
            'id': 'multifactor',
            'name': '멀티팩터 전략',
            'description': '모멘텀, 가치, 퀄리티, 사이즈 팩터를 결합',
            'factor_weights': {'momentum': 0.4, 'value': 0.3, 'quality': 0.2, 'size': 0.1}
        },
        {
            'id': 'size',
            'name': '소형주 전략',
            'description': '시가총액이 작은 소형주에 투자',
            'factor_weights': {'momentum': 0, 'value': 0, 'quality': 0, 'size': 1.0}
        }
    ]
    return jsonify(templates)


@api_bp.route('/market-overview')
@login_required
def market_overview():
    """Get market overview data"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.utils.database import get_db
        import pandas as pd

        quant_db = get_db()

        # Get recent market data
        overview = {
            'kr': {
                'kospi_stocks': len(quant_db.get_all_symbols(market='KOSPI')),
                'kosdaq_stocks': len(quant_db.get_all_symbols(market='KOSDAQ'))
            },
            'us': {
                'nyse_stocks': len(quant_db.get_all_symbols(market='NYSE')),
                'nasdaq_stocks': len(quant_db.get_all_symbols(market='NASDAQ'))
            }
        }

        return jsonify(overview)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
