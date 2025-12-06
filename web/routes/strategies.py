"""
Strategy management routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from web import db
from web.models import SavedStrategy
from web.forms.strategy import StrategyForm

strategies_bp = Blueprint('strategies', __name__)


# Default strategy templates
DEFAULT_STRATEGIES = {
    'momentum': {
        'name': '모멘텀 전략',
        'description': '과거 12개월 수익률이 높은 종목에 투자하는 전략',
        'factor_weights': {'momentum': 1.0, 'value': 0, 'quality': 0, 'size': 0},
        'max_positions': 20,
        'rebalance_frequency': 'monthly'
    },
    'value': {
        'name': '가치 전략',
        'description': 'PBR, PER이 낮은 저평가 종목에 투자하는 전략',
        'factor_weights': {'momentum': 0, 'value': 1.0, 'quality': 0, 'size': 0},
        'max_positions': 20,
        'rebalance_frequency': 'quarterly'
    },
    'quality': {
        'name': '퀄리티 전략',
        'description': 'ROE가 높고 부채비율이 낮은 우량 종목에 투자하는 전략',
        'factor_weights': {'momentum': 0, 'value': 0, 'quality': 1.0, 'size': 0},
        'max_positions': 20,
        'rebalance_frequency': 'quarterly'
    },
    'multifactor': {
        'name': '멀티팩터 전략',
        'description': '모멘텀, 가치, 퀄리티, 사이즈 팩터를 결합한 전략',
        'factor_weights': {'momentum': 0.4, 'value': 0.3, 'quality': 0.2, 'size': 0.1},
        'max_positions': 20,
        'rebalance_frequency': 'monthly'
    },
    'size': {
        'name': '소형주 전략',
        'description': '시가총액이 작은 소형주에 투자하는 전략',
        'factor_weights': {'momentum': 0, 'value': 0, 'quality': 0, 'size': 1.0},
        'max_positions': 30,
        'rebalance_frequency': 'monthly'
    }
}


@strategies_bp.route('/')
@login_required
def index():
    """List all strategies"""
    # User's saved strategies
    user_strategies = SavedStrategy.query.filter_by(user_id=current_user.id)\
        .order_by(SavedStrategy.updated_at.desc()).all()

    # Public strategies from other users
    public_strategies = SavedStrategy.query.filter(
        SavedStrategy.is_public == True,
        SavedStrategy.user_id != current_user.id
    ).order_by(SavedStrategy.last_sharpe_ratio.desc()).limit(10).all()

    return render_template('strategies/index.html',
                         user_strategies=user_strategies,
                         public_strategies=public_strategies,
                         default_strategies=DEFAULT_STRATEGIES)


@strategies_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new strategy"""
    form = StrategyForm()

    if form.validate_on_submit():
        strategy = SavedStrategy(
            user_id=current_user.id,
            name=form.name.data,
            description=form.description.data,
            strategy_type=form.strategy_type.data,
            market=form.market.data,
            is_public=form.is_public.data
        )

        # Build configuration
        config = {
            'max_positions': form.max_positions.data,
            'min_positions': form.min_positions.data,
            'max_position_size': form.max_position_size.data / 100,  # Convert to decimal
            'stop_loss': form.stop_loss.data / 100 if form.stop_loss.data else None,
            'take_profit': form.take_profit.data / 100 if form.take_profit.data else None,
            'rebalance_frequency': form.rebalance_frequency.data,
            'equal_weight': form.equal_weight.data,
            'factor_weights': {
                'momentum': form.momentum_weight.data,
                'value': form.value_weight.data,
                'quality': form.quality_weight.data,
                'size': form.size_weight.data
            },
            'min_market_cap': form.min_market_cap.data * 100000000 if form.min_market_cap.data else None,  # 억원 -> 원
            'min_volume': form.min_volume.data * 100000000 if form.min_volume.data else None
        }
        strategy.config = config

        db.session.add(strategy)
        db.session.commit()
        flash('전략이 생성되었습니다.', 'success')
        return redirect(url_for('strategies.view', id=strategy.id))

    return render_template('strategies/create.html', form=form)


@strategies_bp.route('/<int:id>')
@login_required
def view(id):
    """View strategy details"""
    strategy = SavedStrategy.query.get_or_404(id)

    # Check access permission
    if strategy.user_id != current_user.id and not strategy.is_public:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('strategies.index'))

    return render_template('strategies/view.html', strategy=strategy)


@strategies_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit strategy"""
    strategy = SavedStrategy.query.get_or_404(id)

    # Check ownership
    if strategy.user_id != current_user.id:
        flash('수정 권한이 없습니다.', 'error')
        return redirect(url_for('strategies.index'))

    form = StrategyForm()

    if request.method == 'GET':
        # Pre-fill form with existing data
        form.name.data = strategy.name
        form.description.data = strategy.description
        form.strategy_type.data = strategy.strategy_type
        form.market.data = strategy.market
        form.is_public.data = strategy.is_public

        config = strategy.config
        form.max_positions.data = config.get('max_positions', 20)
        form.min_positions.data = config.get('min_positions', 10)
        form.max_position_size.data = config.get('max_position_size', 0.1) * 100
        form.stop_loss.data = (config.get('stop_loss', 0.15) or 0.15) * 100
        form.take_profit.data = (config.get('take_profit') or 0) * 100 if config.get('take_profit') else None
        form.rebalance_frequency.data = config.get('rebalance_frequency', 'monthly')
        form.equal_weight.data = config.get('equal_weight', True)

        weights = config.get('factor_weights', {})
        form.momentum_weight.data = weights.get('momentum', 0.4)
        form.value_weight.data = weights.get('value', 0.3)
        form.quality_weight.data = weights.get('quality', 0.2)
        form.size_weight.data = weights.get('size', 0.1)

    if form.validate_on_submit():
        strategy.name = form.name.data
        strategy.description = form.description.data
        strategy.strategy_type = form.strategy_type.data
        strategy.market = form.market.data
        strategy.is_public = form.is_public.data

        config = {
            'max_positions': form.max_positions.data,
            'min_positions': form.min_positions.data,
            'max_position_size': form.max_position_size.data / 100,
            'stop_loss': form.stop_loss.data / 100 if form.stop_loss.data else None,
            'take_profit': form.take_profit.data / 100 if form.take_profit.data else None,
            'rebalance_frequency': form.rebalance_frequency.data,
            'equal_weight': form.equal_weight.data,
            'factor_weights': {
                'momentum': form.momentum_weight.data,
                'value': form.value_weight.data,
                'quality': form.quality_weight.data,
                'size': form.size_weight.data
            }
        }
        strategy.config = config

        db.session.commit()
        flash('전략이 수정되었습니다.', 'success')
        return redirect(url_for('strategies.view', id=strategy.id))

    return render_template('strategies/edit.html', form=form, strategy=strategy)


@strategies_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete strategy"""
    strategy = SavedStrategy.query.get_or_404(id)

    if strategy.user_id != current_user.id:
        flash('삭제 권한이 없습니다.', 'error')
        return redirect(url_for('strategies.index'))

    db.session.delete(strategy)
    db.session.commit()
    flash('전략이 삭제되었습니다.', 'success')
    return redirect(url_for('strategies.index'))


@strategies_bp.route('/<int:id>/clone', methods=['POST'])
@login_required
def clone(id):
    """Clone a strategy"""
    original = SavedStrategy.query.get_or_404(id)

    # Check access permission
    if original.user_id != current_user.id and not original.is_public:
        flash('복제 권한이 없습니다.', 'error')
        return redirect(url_for('strategies.index'))

    # Create clone
    clone = SavedStrategy(
        user_id=current_user.id,
        name=f"{original.name} (복사본)",
        description=original.description,
        strategy_type=original.strategy_type,
        market=original.market,
        is_public=False
    )
    clone.config = original.config

    db.session.add(clone)
    db.session.commit()
    flash('전략이 복제되었습니다.', 'success')
    return redirect(url_for('strategies.edit', id=clone.id))
