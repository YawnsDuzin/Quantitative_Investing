"""
Settings and configuration routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
import yaml
from pathlib import Path

settings_bp = Blueprint('settings', __name__)

CONFIG_PATH = Path(__file__).parent.parent.parent / 'config' / 'config.yaml'


def load_config():
    """Load configuration from YAML file"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        return {'error': str(e)}


def save_config(config):
    """Save configuration to YAML file"""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        return False


@settings_bp.route('/')
@login_required
def index():
    """Settings dashboard"""
    config = load_config()
    return render_template('settings/index.html', config=config)


@settings_bp.route('/data-collection', methods=['GET', 'POST'])
@login_required
def data_collection():
    """Data collection settings"""
    config = load_config()

    if request.method == 'POST':
        try:
            # Update data collection settings
            config['data_collection'] = {
                'kr_stock': {
                    'market': request.form.getlist('kr_markets'),
                    'min_market_cap': int(request.form.get('kr_min_market_cap', 50000000000)),
                    'exclude_sectors': request.form.getlist('kr_exclude_sectors')
                },
                'us_stock': {
                    'market': request.form.getlist('us_markets'),
                    'min_market_cap': int(request.form.get('us_min_market_cap', 1000000000)),
                    'exclude_sectors': request.form.getlist('us_exclude_sectors')
                },
                'update_schedule': {
                    'daily': request.form.get('daily_update_time', '09:00'),
                    'fundamental': request.form.get('fundamental_frequency', 'weekly')
                },
                'start_date': request.form.get('start_date', '2018-01-01'),
                'end_date': request.form.get('end_date') or None
            }

            if save_config(config):
                flash('데이터 수집 설정이 저장되었습니다.', 'success')
            else:
                flash('설정 저장에 실패했습니다.', 'error')

        except Exception as e:
            flash(f'오류: {str(e)}', 'error')

        return redirect(url_for('settings.data_collection'))

    return render_template('settings/data_collection.html',
                         config=config.get('data_collection', {}))


@settings_bp.route('/strategy', methods=['GET', 'POST'])
@login_required
def strategy():
    """Strategy settings"""
    config = load_config()

    if request.method == 'POST':
        try:
            config['strategy'] = {
                'rebalancing_frequency': request.form.get('rebalancing_frequency', 'monthly'),
                'rebalancing_day': int(request.form.get('rebalancing_day', 1)),
                'max_positions': int(request.form.get('max_positions', 20)),
                'min_positions': int(request.form.get('min_positions', 10)),
                'equal_weight': request.form.get('equal_weight') == 'on',
                'stop_loss': float(request.form.get('stop_loss', 0.15)),
                'take_profit': float(request.form.get('take_profit')) if request.form.get('take_profit') else None,
                'max_position_size': float(request.form.get('max_position_size', 0.1)),
                'factor_weights': {
                    'momentum': float(request.form.get('momentum_weight', 0.4)),
                    'value': float(request.form.get('value_weight', 0.3)),
                    'quality': float(request.form.get('quality_weight', 0.2)),
                    'size': float(request.form.get('size_weight', 0.1))
                }
            }

            if save_config(config):
                flash('전략 설정이 저장되었습니다.', 'success')
            else:
                flash('설정 저장에 실패했습니다.', 'error')

        except Exception as e:
            flash(f'오류: {str(e)}', 'error')

        return redirect(url_for('settings.strategy'))

    return render_template('settings/strategy.html',
                         config=config.get('strategy', {}))


@settings_bp.route('/backtesting', methods=['GET', 'POST'])
@login_required
def backtesting():
    """Backtesting settings"""
    config = load_config()

    if request.method == 'POST':
        try:
            config['backtesting'] = {
                'initial_capital': int(request.form.get('initial_capital', 100000000)),
                'commission': float(request.form.get('commission', 0.0015)),
                'slippage': float(request.form.get('slippage', 0.001)),
                'benchmark': request.form.get('benchmark', 'SPY'),
                'risk_free_rate': float(request.form.get('risk_free_rate', 0.03))
            }

            if save_config(config):
                flash('백테스팅 설정이 저장되었습니다.', 'success')
            else:
                flash('설정 저장에 실패했습니다.', 'error')

        except Exception as e:
            flash(f'오류: {str(e)}', 'error')

        return redirect(url_for('settings.backtesting'))

    return render_template('settings/backtesting.html',
                         config=config.get('backtesting', {}))


@settings_bp.route('/database', methods=['GET', 'POST'])
@login_required
def database():
    """Database settings"""
    config = load_config()

    if request.method == 'POST':
        try:
            db_type = request.form.get('db_type', 'sqlite')
            config['database'] = {'type': db_type}

            if db_type == 'sqlite':
                config['database']['path'] = request.form.get('db_path', 'data/database/quant_investing.db')
            else:
                config['database']['host'] = request.form.get('db_host', 'localhost')
                config['database']['port'] = int(request.form.get('db_port', 5432 if db_type == 'postgresql' else 3306))
                config['database']['name'] = request.form.get('db_name', 'quant_investing')
                config['database']['user'] = request.form.get('db_user', '')
                config['database']['password'] = request.form.get('db_password', '')

            if save_config(config):
                flash('데이터베이스 설정이 저장되었습니다.', 'success')
            else:
                flash('설정 저장에 실패했습니다.', 'error')

        except Exception as e:
            flash(f'오류: {str(e)}', 'error')

        return redirect(url_for('settings.database'))

    return render_template('settings/database.html',
                         config=config.get('database', {}))


@settings_bp.route('/indicators', methods=['GET', 'POST'])
@login_required
def indicators():
    """Technical indicators settings"""
    config = load_config()

    if request.method == 'POST':
        try:
            config['indicators'] = {
                'sma_periods': [int(x) for x in request.form.get('sma_periods', '20,50,200').split(',')],
                'ema_periods': [int(x) for x in request.form.get('ema_periods', '12,26').split(',')],
                'rsi_period': int(request.form.get('rsi_period', 14)),
                'macd_fast': int(request.form.get('macd_fast', 12)),
                'macd_slow': int(request.form.get('macd_slow', 26)),
                'macd_signal': int(request.form.get('macd_signal', 9)),
                'bollinger_period': int(request.form.get('bollinger_period', 20)),
                'bollinger_std': int(request.form.get('bollinger_std', 2)),
                'atr_period': int(request.form.get('atr_period', 14))
            }

            if save_config(config):
                flash('지표 설정이 저장되었습니다.', 'success')
            else:
                flash('설정 저장에 실패했습니다.', 'error')

        except Exception as e:
            flash(f'오류: {str(e)}', 'error')

        return redirect(url_for('settings.indicators'))

    return render_template('settings/indicators.html',
                         config=config.get('indicators', {}))


@settings_bp.route('/notification', methods=['GET', 'POST'])
@login_required
def notification():
    """Notification settings"""
    config = load_config()

    if request.method == 'POST':
        try:
            config['notification'] = {
                'enabled': request.form.get('notification_enabled') == 'on',
                'telegram': {
                    'enabled': request.form.get('telegram_enabled') == 'on',
                    'bot_token': request.form.get('telegram_bot_token', ''),
                    'chat_id': request.form.get('telegram_chat_id', '')
                },
                'email': {
                    'enabled': request.form.get('email_enabled') == 'on',
                    'smtp_server': request.form.get('smtp_server', 'smtp.gmail.com'),
                    'smtp_port': int(request.form.get('smtp_port', 587)),
                    'sender': request.form.get('email_sender', ''),
                    'receiver': request.form.get('email_receiver', ''),
                    'password': request.form.get('email_password', '')
                }
            }

            if save_config(config):
                flash('알림 설정이 저장되었습니다.', 'success')
            else:
                flash('설정 저장에 실패했습니다.', 'error')

        except Exception as e:
            flash(f'오류: {str(e)}', 'error')

        return redirect(url_for('settings.notification'))

    return render_template('settings/notification.html',
                         config=config.get('notification', {}))


@settings_bp.route('/export')
@login_required
def export_config():
    """Export configuration as YAML"""
    from flask import Response

    config = load_config()
    yaml_content = yaml.dump(config, default_flow_style=False, allow_unicode=True)

    return Response(
        yaml_content,
        mimetype='text/yaml',
        headers={'Content-Disposition': 'attachment;filename=config.yaml'}
    )


@settings_bp.route('/import', methods=['POST'])
@login_required
def import_config():
    """Import configuration from YAML file"""
    if 'file' not in request.files:
        flash('파일을 선택해주세요.', 'error')
        return redirect(url_for('settings.index'))

    file = request.files['file']
    if file.filename == '':
        flash('파일을 선택해주세요.', 'error')
        return redirect(url_for('settings.index'))

    try:
        config = yaml.safe_load(file.read().decode('utf-8'))
        if save_config(config):
            flash('설정을 가져왔습니다.', 'success')
        else:
            flash('설정 저장에 실패했습니다.', 'error')
    except Exception as e:
        flash(f'파일 처리 오류: {str(e)}', 'error')

    return redirect(url_for('settings.index'))
