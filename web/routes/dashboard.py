"""
Dashboard routes - main user dashboard
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from web.models import BacktestResult, Portfolio
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard"""
    # Get recent backtests
    recent_backtests = BacktestResult.query.filter_by(user_id=current_user.id)\
        .order_by(BacktestResult.created_at.desc())\
        .limit(5).all()

    # Get user portfolios
    portfolios = Portfolio.query.filter_by(user_id=current_user.id)\
        .order_by(Portfolio.updated_at.desc()).all()

    # Calculate summary statistics
    total_backtests = BacktestResult.query.filter_by(user_id=current_user.id).count()

    best_backtest = BacktestResult.query.filter_by(user_id=current_user.id)\
        .filter(BacktestResult.sharpe_ratio.isnot(None))\
        .order_by(BacktestResult.sharpe_ratio.desc())\
        .first()

    # Calculate total portfolio value
    total_portfolio_value = sum(
        p.current_value or p.initial_capital for p in portfolios
    )

    return render_template('dashboard/index.html',
                         recent_backtests=recent_backtests,
                         portfolios=portfolios,
                         total_backtests=total_backtests,
                         best_backtest=best_backtest,
                         total_portfolio_value=total_portfolio_value)


@dashboard_bp.route('/summary')
@login_required
def summary():
    """Dashboard summary data (AJAX)"""
    # Recent performance data
    backtests = BacktestResult.query.filter_by(user_id=current_user.id)\
        .filter(BacktestResult.status == 'completed')\
        .order_by(BacktestResult.created_at.desc())\
        .limit(10).all()

    data = {
        'backtests': [bt.to_dict() for bt in backtests],
        'portfolios': [p.to_dict() for p in current_user.portfolios.all()],
        'strategies': [s.to_dict() for s in current_user.strategies.all()]
    }

    return jsonify(data)


@dashboard_bp.route('/performance')
@login_required
def performance():
    """Performance overview page"""
    backtests = BacktestResult.query.filter_by(user_id=current_user.id)\
        .filter(BacktestResult.status == 'completed')\
        .order_by(BacktestResult.created_at.desc()).all()

    return render_template('dashboard/performance.html', backtests=backtests)


@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Analytics page"""
    # Get all completed backtests for analysis
    backtests = BacktestResult.query.filter_by(user_id=current_user.id)\
        .filter(BacktestResult.status == 'completed').all()

    # Strategy performance comparison
    strategy_stats = {}
    for bt in backtests:
        if bt.strategy_name not in strategy_stats:
            strategy_stats[bt.strategy_name] = {
                'count': 0,
                'avg_return': 0,
                'avg_sharpe': 0,
                'returns': [],
                'sharpes': []
            }
        stats = strategy_stats[bt.strategy_name]
        stats['count'] += 1
        if bt.annual_return:
            stats['returns'].append(bt.annual_return)
        if bt.sharpe_ratio:
            stats['sharpes'].append(bt.sharpe_ratio)

    # Calculate averages
    for name, stats in strategy_stats.items():
        if stats['returns']:
            stats['avg_return'] = sum(stats['returns']) / len(stats['returns'])
        if stats['sharpes']:
            stats['avg_sharpe'] = sum(stats['sharpes']) / len(stats['sharpes'])

    return render_template('dashboard/analytics.html',
                         backtests=backtests,
                         strategy_stats=strategy_stats)
