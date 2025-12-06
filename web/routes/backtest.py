"""
Backtest routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from web import db
from web.models import BacktestResult, BacktestTrade, SavedStrategy
from web.forms.backtest import BacktestForm
from datetime import datetime
import json

backtest_bp = Blueprint('backtest', __name__)


@backtest_bp.route('/')
@login_required
def index():
    """List all backtests"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    backtests = BacktestResult.query.filter_by(user_id=current_user.id)\
        .order_by(BacktestResult.created_at.desc())\
        .paginate(page=page, per_page=per_page)

    return render_template('backtest/index.html', backtests=backtests)


@backtest_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create new backtest"""
    form = BacktestForm()

    # Add user's saved strategies to choices
    user_strategies = SavedStrategy.query.filter_by(user_id=current_user.id).all()
    extra_choices = [(f'custom_{s.id}', s.name) for s in user_strategies]
    form.strategy.choices = form.strategy.choices + extra_choices

    if form.validate_on_submit():
        # Create backtest result record
        backtest = BacktestResult(
            user_id=current_user.id,
            name=form.name.data,
            strategy_name=form.strategy.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            initial_capital=form.initial_capital.data,
            market=form.market.data,
            rebalance_frequency=form.rebalance_frequency.data,
            status='pending'
        )

        # Build parameters
        params = {
            'max_positions': form.max_positions.data,
            'commission': form.commission.data / 100,  # Convert to decimal
            'slippage': form.slippage.data / 100,
            'stop_loss': form.stop_loss.data / 100 if form.stop_loss.data else None,
            'factor_weights': {
                'momentum': form.momentum_weight.data,
                'value': form.value_weight.data,
                'quality': form.quality_weight.data,
                'size': form.size_weight.data
            }
        }
        backtest.parameters = params

        db.session.add(backtest)
        db.session.commit()

        flash('백테스트가 생성되었습니다. 실행 중...', 'info')
        return redirect(url_for('backtest.run', id=backtest.id))

    return render_template('backtest/new.html', form=form)


@backtest_bp.route('/<int:id>')
@login_required
def view(id):
    """View backtest results"""
    backtest = BacktestResult.query.get_or_404(id)

    if backtest.user_id != current_user.id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('backtest.index'))

    # Get trades
    trades = BacktestTrade.query.filter_by(backtest_id=id)\
        .order_by(BacktestTrade.date.desc()).all()

    return render_template('backtest/view.html', backtest=backtest, trades=trades)


@backtest_bp.route('/<int:id>/run')
@login_required
def run(id):
    """Run backtest (redirects to execution page)"""
    backtest = BacktestResult.query.get_or_404(id)

    if backtest.user_id != current_user.id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('backtest.index'))

    if backtest.status == 'completed':
        return redirect(url_for('backtest.view', id=id))

    return render_template('backtest/running.html', backtest=backtest)


@backtest_bp.route('/<int:id>/execute', methods=['POST'])
@login_required
def execute(id):
    """Execute backtest (AJAX endpoint)"""
    backtest = BacktestResult.query.get_or_404(id)

    if backtest.user_id != current_user.id:
        return jsonify({'error': '접근 권한이 없습니다.'}), 403

    try:
        backtest.status = 'running'
        db.session.commit()

        # Import and run the actual backtest
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        from src.strategies.quant_strategies import create_strategy
        from src.backtesting.backtester import Backtester
        from src.backtesting.performance_metrics import PerformanceMetrics
        from src.utils.database import get_db

        # Get parameters
        params = backtest.parameters

        # Get strategy name (remove 'custom_' prefix if present)
        strategy_name = backtest.strategy_name
        if strategy_name.startswith('custom_'):
            saved_strategy = SavedStrategy.query.get(int(strategy_name.split('_')[1]))
            if saved_strategy:
                strategy_name = saved_strategy.strategy_type
                params.update(saved_strategy.config)

        # Create strategy
        factor_weights = params.get('factor_weights', {})
        strategy = create_strategy(
            strategy_name,
            max_positions=params.get('max_positions', 20),
            factor_weights=factor_weights,
            stop_loss=params.get('stop_loss'),
            rebalancing_frequency=backtest.rebalance_frequency
        )

        # Get data from database
        quant_db = get_db()

        # Map market to database query
        if backtest.market == 'KR':
            markets = ['KOSPI', 'KOSDAQ']
        else:
            markets = ['NYSE', 'NASDAQ']

        # Get stock data
        data = quant_db.get_stock_prices(
            start_date=backtest.start_date.strftime('%Y-%m-%d'),
            end_date=backtest.end_date.strftime('%Y-%m-%d')
        )

        if data.empty:
            raise ValueError("데이터가 없습니다. 먼저 데이터를 수집해주세요.")

        # Run backtest
        backtester = Backtester(
            strategy=strategy,
            initial_capital=backtest.initial_capital,
            commission=params.get('commission', 0.0015),
            slippage=params.get('slippage', 0.001)
        )

        results = backtester.run(data)

        # Calculate performance metrics
        metrics = PerformanceMetrics(results['portfolio_value'])

        # Update backtest record
        backtest.total_return = metrics.total_return()
        backtest.annual_return = metrics.annual_return()
        backtest.volatility = metrics.volatility()
        backtest.sharpe_ratio = metrics.sharpe_ratio()
        backtest.sortino_ratio = metrics.sortino_ratio()
        backtest.max_drawdown = metrics.max_drawdown()
        backtest.calmar_ratio = metrics.calmar_ratio()
        backtest.win_rate = metrics.win_rate()
        backtest.profit_factor = metrics.profit_factor()

        # Store portfolio values
        portfolio_values = results['portfolio_value'].to_dict()
        backtest.portfolio_values = portfolio_values

        # Store trades
        trades_df = backtester.get_trades_df()
        for _, trade in trades_df.iterrows():
            bt_trade = BacktestTrade(
                backtest_id=backtest.id,
                date=trade['date'],
                symbol=trade['symbol'],
                action=trade['action'],
                shares=trade['shares'],
                price=trade['price'],
                value=trade['value'],
                commission=trade.get('commission', 0)
            )
            db.session.add(bt_trade)

        backtest.status = 'completed'
        db.session.commit()

        return jsonify({
            'status': 'completed',
            'redirect': url_for('backtest.view', id=id)
        })

    except Exception as e:
        backtest.status = 'failed'
        backtest.error_message = str(e)
        db.session.commit()
        return jsonify({
            'status': 'failed',
            'error': str(e)
        }), 500


@backtest_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete backtest"""
    backtest = BacktestResult.query.get_or_404(id)

    if backtest.user_id != current_user.id:
        flash('삭제 권한이 없습니다.', 'error')
        return redirect(url_for('backtest.index'))

    db.session.delete(backtest)
    db.session.commit()
    flash('백테스트가 삭제되었습니다.', 'success')
    return redirect(url_for('backtest.index'))


@backtest_bp.route('/<int:id>/chart-data')
@login_required
def chart_data(id):
    """Get chart data for backtest (AJAX)"""
    backtest = BacktestResult.query.get_or_404(id)

    if backtest.user_id != current_user.id:
        return jsonify({'error': '접근 권한이 없습니다.'}), 403

    portfolio_values = backtest.portfolio_values
    if not portfolio_values:
        return jsonify({'error': '포트폴리오 데이터가 없습니다.'}), 404

    # Format for charts
    labels = list(portfolio_values.keys())
    values = list(portfolio_values.values())

    # Calculate returns
    initial = values[0] if values else 1
    returns = [(v / initial - 1) * 100 for v in values]

    return jsonify({
        'labels': labels,
        'portfolio_values': values,
        'returns': returns
    })


@backtest_bp.route('/compare')
@login_required
def compare():
    """Compare multiple backtests"""
    # Get backtest IDs from query string
    ids = request.args.getlist('ids', type=int)

    if len(ids) < 2:
        flash('비교하려면 최소 2개의 백테스트를 선택해주세요.', 'warning')
        return redirect(url_for('backtest.index'))

    backtests = BacktestResult.query.filter(
        BacktestResult.id.in_(ids),
        BacktestResult.user_id == current_user.id
    ).all()

    return render_template('backtest/compare.html', backtests=backtests)
