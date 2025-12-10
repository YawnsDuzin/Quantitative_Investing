"""
Screening routes - Stock screening functionality
"""
import json
import threading
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from web import db
from web.models.screening import ScreeningResult, SavedScreener

screening_bp = Blueprint('screening', __name__)

# Available preset strategies
PRESET_STRATEGIES = {
    'value': {
        'name': 'value',
        'display_name': '가치주 발굴',
        'description': '저PER, 저PBR 종목을 발굴하여 저평가된 가치주를 찾습니다.',
        'parameters': [
            {'name': 'max_per', 'display_name': '최대 PER', 'type': 'float', 'default': 10.0, 'min': 0, 'max': 100},
            {'name': 'max_pbr', 'display_name': '최대 PBR', 'type': 'float', 'default': 1.0, 'min': 0, 'max': 10},
            {'name': 'min_roe', 'display_name': '최소 ROE (%)', 'type': 'float', 'default': 5.0, 'min': 0, 'max': 100},
        ]
    },
    'growth': {
        'name': 'growth',
        'display_name': '성장주 발굴',
        'description': '높은 매출 성장률과 이익 성장률을 보이는 성장주를 발굴합니다.',
        'parameters': [
            {'name': 'min_revenue_growth', 'display_name': '최소 매출 성장률 (%)', 'type': 'float', 'default': 15.0, 'min': 0, 'max': 500},
            {'name': 'min_profit_growth', 'display_name': '최소 이익 성장률 (%)', 'type': 'float', 'default': 20.0, 'min': 0, 'max': 500},
            {'name': 'max_per', 'display_name': '최대 PER', 'type': 'float', 'default': 30.0, 'min': 0, 'max': 200},
        ]
    },
    'dividend': {
        'name': 'dividend',
        'display_name': '배당주 발굴',
        'description': '안정적인 배당을 지급하는 고배당 종목을 발굴합니다.',
        'parameters': [
            {'name': 'min_dividend_yield', 'display_name': '최소 배당수익률 (%)', 'type': 'float', 'default': 3.0, 'min': 0, 'max': 20},
            {'name': 'min_payout_ratio', 'display_name': '최소 배당성향 (%)', 'type': 'float', 'default': 20.0, 'min': 0, 'max': 100},
            {'name': 'max_payout_ratio', 'display_name': '최대 배당성향 (%)', 'type': 'float', 'default': 80.0, 'min': 0, 'max': 100},
        ]
    },
    'momentum': {
        'name': 'momentum',
        'display_name': '모멘텀 전략',
        'description': '상승 추세에 있는 강한 모멘텀 종목을 발굴합니다.',
        'parameters': [
            {'name': 'min_return_1m', 'display_name': '최소 1개월 수익률 (%)', 'type': 'float', 'default': 5.0, 'min': -100, 'max': 500},
            {'name': 'min_return_3m', 'display_name': '최소 3개월 수익률 (%)', 'type': 'float', 'default': 10.0, 'min': -100, 'max': 500},
            {'name': 'above_ma20', 'display_name': '20일 이평선 위', 'type': 'bool', 'default': True},
        ]
    },
    'quality': {
        'name': 'quality',
        'display_name': '퀄리티 전략',
        'description': '재무 건전성이 우수한 고품질 기업을 발굴합니다.',
        'parameters': [
            {'name': 'min_roe', 'display_name': '최소 ROE (%)', 'type': 'float', 'default': 15.0, 'min': 0, 'max': 100},
            {'name': 'max_debt_ratio', 'display_name': '최대 부채비율 (%)', 'type': 'float', 'default': 100.0, 'min': 0, 'max': 500},
            {'name': 'min_current_ratio', 'display_name': '최소 유동비율 (%)', 'type': 'float', 'default': 100.0, 'min': 0, 'max': 500},
        ]
    },
    'small_value': {
        'name': 'small_value',
        'display_name': '소형 가치주',
        'description': '시가총액이 작으면서 저평가된 소형 가치주를 발굴합니다.',
        'parameters': [
            {'name': 'max_market_cap', 'display_name': '최대 시가총액 (억원)', 'type': 'float', 'default': 3000.0, 'min': 0, 'max': 100000},
            {'name': 'max_per', 'display_name': '최대 PER', 'type': 'float', 'default': 10.0, 'min': 0, 'max': 100},
            {'name': 'max_pbr', 'display_name': '최대 PBR', 'type': 'float', 'default': 1.0, 'min': 0, 'max': 10},
        ]
    },
    'garp': {
        'name': 'garp',
        'display_name': 'GARP 전략',
        'description': '합리적인 가격의 성장주(Growth at Reasonable Price)를 발굴합니다.',
        'parameters': [
            {'name': 'max_peg', 'display_name': '최대 PEG', 'type': 'float', 'default': 1.5, 'min': 0, 'max': 10},
            {'name': 'min_growth', 'display_name': '최소 성장률 (%)', 'type': 'float', 'default': 10.0, 'min': 0, 'max': 500},
            {'name': 'max_per', 'display_name': '최대 PER', 'type': 'float', 'default': 25.0, 'min': 0, 'max': 200},
        ]
    },
    'contrarian': {
        'name': 'contrarian',
        'display_name': '역발상 전략',
        'description': '과매도 구간에서 반등을 기대할 수 있는 종목을 발굴합니다.',
        'parameters': [
            {'name': 'max_rsi', 'display_name': '최대 RSI', 'type': 'float', 'default': 30.0, 'min': 0, 'max': 100},
            {'name': 'min_drop_1m', 'display_name': '1개월 최소 하락률 (%)', 'type': 'float', 'default': -15.0, 'min': -100, 'max': 0},
            {'name': 'min_roe', 'display_name': '최소 ROE (%)', 'type': 'float', 'default': 5.0, 'min': 0, 'max': 100},
        ]
    },
    'dual_momentum': {
        'name': 'dual_momentum',
        'display_name': '듀얼 모멘텀',
        'description': '절대 모멘텀과 상대 모멘텀을 결합한 전략입니다.',
        'parameters': [
            {'name': 'lookback_period', 'display_name': '모멘텀 기간 (월)', 'type': 'int', 'default': 12, 'min': 1, 'max': 36},
            {'name': 'top_n', 'display_name': '상위 종목 수', 'type': 'int', 'default': 20, 'min': 1, 'max': 100},
        ]
    },
    'composite': {
        'name': 'composite',
        'display_name': '통합 스코어',
        'description': '가치, 품질, 모멘텀을 종합한 통합 점수로 종목을 발굴합니다.',
        'parameters': [
            {'name': 'value_weight', 'display_name': '가치 비중 (%)', 'type': 'float', 'default': 40.0, 'min': 0, 'max': 100},
            {'name': 'quality_weight', 'display_name': '품질 비중 (%)', 'type': 'float', 'default': 30.0, 'min': 0, 'max': 100},
            {'name': 'momentum_weight', 'display_name': '모멘텀 비중 (%)', 'type': 'float', 'default': 30.0, 'min': 0, 'max': 100},
            {'name': 'top_n', 'display_name': '상위 종목 수', 'type': 'int', 'default': 30, 'min': 1, 'max': 100},
        ]
    }
}

# Available conditions by category
CONDITION_CATEGORIES = {
    'price': {
        'name': '가격 조건',
        'conditions': [
            {'class_name': 'PriceAbove', 'display_name': '현재가 이상', 'params': [{'name': 'threshold', 'type': 'float', 'default': 5000}]},
            {'class_name': 'PriceBelow', 'display_name': '현재가 이하', 'params': [{'name': 'threshold', 'type': 'float', 'default': 100000}]},
            {'class_name': 'PriceChange', 'display_name': '등락률 범위', 'params': [{'name': 'min_change', 'type': 'float', 'default': -5}, {'name': 'max_change', 'type': 'float', 'default': 5}]},
            {'class_name': 'NewHigh52W', 'display_name': '52주 신고가', 'params': []},
            {'class_name': 'NewLow52W', 'display_name': '52주 신저가', 'params': []},
            {'class_name': 'NearHigh52W', 'display_name': '52주 고점 근접', 'params': [{'name': 'threshold_pct', 'type': 'float', 'default': 5}]},
        ]
    },
    'technical': {
        'name': '기술적 조건',
        'conditions': [
            {'class_name': 'AboveMA', 'display_name': '이동평균선 위', 'params': [{'name': 'period', 'type': 'int', 'default': 20}]},
            {'class_name': 'BelowMA', 'display_name': '이동평균선 아래', 'params': [{'name': 'period', 'type': 'int', 'default': 20}]},
            {'class_name': 'GoldenCross', 'display_name': '골든크로스', 'params': [{'name': 'short_period', 'type': 'int', 'default': 5}, {'name': 'long_period', 'type': 'int', 'default': 20}]},
            {'class_name': 'DeadCross', 'display_name': '데드크로스', 'params': [{'name': 'short_period', 'type': 'int', 'default': 5}, {'name': 'long_period', 'type': 'int', 'default': 20}]},
            {'class_name': 'RSIBelow', 'display_name': 'RSI 이하 (과매도)', 'params': [{'name': 'threshold', 'type': 'float', 'default': 30}]},
            {'class_name': 'RSIAbove', 'display_name': 'RSI 이상 (과매수)', 'params': [{'name': 'threshold', 'type': 'float', 'default': 70}]},
            {'class_name': 'MACDBullish', 'display_name': 'MACD 상승 신호', 'params': []},
            {'class_name': 'MACDBearish', 'display_name': 'MACD 하락 신호', 'params': []},
            {'class_name': 'BollingerLower', 'display_name': '볼린저밴드 하단', 'params': [{'name': 'period', 'type': 'int', 'default': 20}]},
            {'class_name': 'BollingerUpper', 'display_name': '볼린저밴드 상단', 'params': [{'name': 'period', 'type': 'int', 'default': 20}]},
        ]
    },
    'fundamental': {
        'name': '펀더멘털 조건',
        'conditions': [
            {'class_name': 'PERBelow', 'display_name': 'PER 이하', 'params': [{'name': 'threshold', 'type': 'float', 'default': 15}]},
            {'class_name': 'PERAbove', 'display_name': 'PER 이상', 'params': [{'name': 'threshold', 'type': 'float', 'default': 5}]},
            {'class_name': 'PBRBelow', 'display_name': 'PBR 이하', 'params': [{'name': 'threshold', 'type': 'float', 'default': 1.0}]},
            {'class_name': 'PBRAbove', 'display_name': 'PBR 이상', 'params': [{'name': 'threshold', 'type': 'float', 'default': 0.5}]},
            {'class_name': 'ROEAbove', 'display_name': 'ROE 이상', 'params': [{'name': 'threshold', 'type': 'float', 'default': 10}]},
            {'class_name': 'ROAAbove', 'display_name': 'ROA 이상', 'params': [{'name': 'threshold', 'type': 'float', 'default': 5}]},
            {'class_name': 'DividendYieldAbove', 'display_name': '배당수익률 이상', 'params': [{'name': 'threshold', 'type': 'float', 'default': 3}]},
            {'class_name': 'DebtRatioBelow', 'display_name': '부채비율 이하', 'params': [{'name': 'threshold', 'type': 'float', 'default': 100}]},
            {'class_name': 'CurrentRatioAbove', 'display_name': '유동비율 이상', 'params': [{'name': 'threshold', 'type': 'float', 'default': 100}]},
            {'class_name': 'RevenueGrowthAbove', 'display_name': '매출성장률 이상', 'params': [{'name': 'threshold', 'type': 'float', 'default': 10}]},
        ]
    },
    'market': {
        'name': '시장 조건',
        'conditions': [
            {'class_name': 'MarketCapAbove', 'display_name': '시가총액 이상 (억원)', 'params': [{'name': 'threshold', 'type': 'float', 'default': 1000}]},
            {'class_name': 'MarketCapBelow', 'display_name': '시가총액 이하 (억원)', 'params': [{'name': 'threshold', 'type': 'float', 'default': 10000}]},
            {'class_name': 'VolumeAbove', 'display_name': '거래량 이상', 'params': [{'name': 'threshold', 'type': 'int', 'default': 100000}]},
            {'class_name': 'VolumeRatioAbove', 'display_name': '거래량 비율 이상', 'params': [{'name': 'ratio', 'type': 'float', 'default': 2.0}]},
            {'class_name': 'TurnoverAbove', 'display_name': '거래대금 이상 (억원)', 'params': [{'name': 'threshold', 'type': 'float', 'default': 10}]},
            {'class_name': 'InKOSPI', 'display_name': 'KOSPI 종목', 'params': []},
            {'class_name': 'InKOSDAQ', 'display_name': 'KOSDAQ 종목', 'params': []},
            {'class_name': 'ExcludeAdministrative', 'display_name': '관리종목 제외', 'params': []},
        ]
    }
}


@screening_bp.route('/')
@login_required
def index():
    """Screening main page"""
    # Get recent screening results
    recent_results = ScreeningResult.query.filter_by(user_id=current_user.id)\
        .order_by(ScreeningResult.created_at.desc())\
        .limit(10).all()

    # Get saved screeners
    saved_screeners = SavedScreener.query.filter_by(user_id=current_user.id)\
        .order_by(SavedScreener.updated_at.desc()).all()

    return render_template('screening/index.html',
                         recent_results=recent_results,
                         saved_screeners=saved_screeners,
                         presets=PRESET_STRATEGIES)


@screening_bp.route('/preset')
@login_required
def preset():
    """Preset screening page"""
    return render_template('screening/preset.html',
                         presets=PRESET_STRATEGIES)


@screening_bp.route('/custom')
@login_required
def custom():
    """Custom screening page"""
    return render_template('screening/custom.html',
                         categories=CONDITION_CATEGORIES)


@screening_bp.route('/results/<int:result_id>')
@login_required
def results(result_id):
    """View screening results"""
    result = ScreeningResult.query.filter_by(
        id=result_id, user_id=current_user.id
    ).first_or_404()

    return render_template('screening/results.html', result=result)


@screening_bp.route('/history')
@login_required
def history():
    """Screening history"""
    page = request.args.get('page', 1, type=int)
    results = ScreeningResult.query.filter_by(user_id=current_user.id)\
        .order_by(ScreeningResult.created_at.desc())\
        .paginate(page=page, per_page=20)

    return render_template('screening/history.html', results=results)


# === API Endpoints ===

@screening_bp.route('/api/presets')
@login_required
def api_presets():
    """Get available preset strategies"""
    return jsonify({
        'success': True,
        'presets': list(PRESET_STRATEGIES.values())
    })


@screening_bp.route('/api/presets/<preset_name>')
@login_required
def api_preset_info(preset_name):
    """Get preset strategy details"""
    if preset_name not in PRESET_STRATEGIES:
        return jsonify({'success': False, 'error': '프리셋을 찾을 수 없습니다.'}), 404

    return jsonify({
        'success': True,
        'preset': PRESET_STRATEGIES[preset_name]
    })


@screening_bp.route('/api/conditions')
@login_required
def api_conditions():
    """Get available conditions"""
    return jsonify({
        'success': True,
        'categories': CONDITION_CATEGORIES
    })


@screening_bp.route('/api/run/preset', methods=['POST'])
@login_required
def api_run_preset():
    """Run preset screening"""
    data = request.get_json()

    preset_name = data.get('preset_name')
    market = data.get('market', 'KR')
    params = data.get('params', {})

    if preset_name not in PRESET_STRATEGIES:
        return jsonify({'success': False, 'error': '프리셋을 찾을 수 없습니다.'}), 400

    preset = PRESET_STRATEGIES[preset_name]

    # Create screening result record
    result = ScreeningResult(
        user_id=current_user.id,
        name=f"{preset['display_name']} 스크리닝",
        description=preset['description'],
        market=market,
        screening_type='preset',
        preset_name=preset_name,
        parameters_json=json.dumps(params),
        status='pending'
    )
    db.session.add(result)
    db.session.commit()

    # Run screening in background
    thread = threading.Thread(
        target=_run_screening_task,
        args=(result.id, 'preset', preset_name, market, params)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'result_id': result.id,
        'message': '스크리닝이 시작되었습니다.'
    })


@screening_bp.route('/api/run/custom', methods=['POST'])
@login_required
def api_run_custom():
    """Run custom screening"""
    data = request.get_json()

    conditions = data.get('conditions', [])
    market = data.get('market', 'KR')
    combine_mode = data.get('combine_mode', 'AND')
    name = data.get('name', '커스텀 스크리닝')

    if not conditions:
        return jsonify({'success': False, 'error': '조건을 하나 이상 선택하세요.'}), 400

    # Create screening result record
    result = ScreeningResult(
        user_id=current_user.id,
        name=name,
        market=market,
        screening_type='custom',
        conditions_json=json.dumps(conditions),
        parameters_json=json.dumps({'combine_mode': combine_mode}),
        status='pending'
    )
    db.session.add(result)
    db.session.commit()

    # Run screening in background
    thread = threading.Thread(
        target=_run_screening_task,
        args=(result.id, 'custom', None, market, {'conditions': conditions, 'combine_mode': combine_mode})
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'result_id': result.id,
        'message': '스크리닝이 시작되었습니다.'
    })


@screening_bp.route('/api/status/<int:result_id>')
@login_required
def api_status(result_id):
    """Get screening status"""
    result = ScreeningResult.query.filter_by(
        id=result_id, user_id=current_user.id
    ).first()

    if not result:
        return jsonify({'success': False, 'error': '결과를 찾을 수 없습니다.'}), 404

    return jsonify({
        'success': True,
        'status': result.status,
        'progress': result.progress,
        'current_step': result.current_step,
        'error_message': result.error_message
    })


@screening_bp.route('/api/results/<int:result_id>')
@login_required
def api_results(result_id):
    """Get screening results"""
    result = ScreeningResult.query.filter_by(
        id=result_id, user_id=current_user.id
    ).first()

    if not result:
        return jsonify({'success': False, 'error': '결과를 찾을 수 없습니다.'}), 404

    return jsonify({
        'success': True,
        'result': result.to_dict()
    })


@screening_bp.route('/api/save', methods=['POST'])
@login_required
def api_save_screener():
    """Save screener configuration"""
    data = request.get_json()

    screener = SavedScreener(
        user_id=current_user.id,
        name=data.get('name', '저장된 스크리너'),
        description=data.get('description'),
        market=data.get('market', 'KR'),
        screening_type=data.get('screening_type', 'custom'),
        preset_name=data.get('preset_name'),
        conditions_json=json.dumps(data.get('conditions', [])),
        parameters_json=json.dumps(data.get('parameters', {}))
    )
    db.session.add(screener)
    db.session.commit()

    return jsonify({
        'success': True,
        'screener_id': screener.id,
        'message': '스크리너가 저장되었습니다.'
    })


@screening_bp.route('/api/saved/<int:screener_id>', methods=['DELETE'])
@login_required
def api_delete_screener(screener_id):
    """Delete saved screener"""
    screener = SavedScreener.query.filter_by(
        id=screener_id, user_id=current_user.id
    ).first()

    if not screener:
        return jsonify({'success': False, 'error': '스크리너를 찾을 수 없습니다.'}), 404

    db.session.delete(screener)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '스크리너가 삭제되었습니다.'
    })


def _run_screening_task(result_id, screening_type, preset_name, market, params):
    """Background task to run screening"""
    from flask import current_app
    from web import create_app

    # Create app context for background thread
    app = create_app()
    with app.app_context():
        result = ScreeningResult.query.get(result_id)
        if not result:
            return

        try:
            result.status = 'running'
            result.started_at = datetime.utcnow()
            result.progress = 0
            result.current_step = '데이터 로딩 중...'
            db.session.commit()

            # Generate sample data for demo
            import random
            import time

            # Simulate progress
            stocks_data = _generate_sample_stocks(market)
            total_stocks = len(stocks_data)
            result.total_stocks = total_stocks
            result.progress = 20
            result.current_step = f'{total_stocks}개 종목 분석 중...'
            db.session.commit()

            time.sleep(0.5)

            # Apply filtering (simulated)
            result.progress = 50
            result.current_step = '조건 필터링 중...'
            db.session.commit()

            time.sleep(0.5)

            # Filter stocks (demo: random selection)
            if screening_type == 'preset':
                filtered_stocks = _apply_preset_filter(stocks_data, preset_name, params)
            else:
                filtered_stocks = _apply_custom_filter(stocks_data, params)

            result.progress = 80
            result.current_step = '결과 정렬 중...'
            db.session.commit()

            time.sleep(0.3)

            # Finalize
            result.filtered_count = len(filtered_stocks)
            result.results_json = json.dumps(filtered_stocks)
            result.progress = 100
            result.current_step = '완료'
            result.status = 'completed'
            result.completed_at = datetime.utcnow()
            db.session.commit()

        except Exception as e:
            result.status = 'failed'
            result.error_message = str(e)
            result.completed_at = datetime.utcnow()
            db.session.commit()


def _generate_sample_stocks(market):
    """Generate sample stock data for demo"""
    import random

    if market == 'KR':
        stocks = [
            {'code': '005930', 'name': '삼성전자', 'sector': '전기전자'},
            {'code': '000660', 'name': 'SK하이닉스', 'sector': '전기전자'},
            {'code': '035420', 'name': 'NAVER', 'sector': 'IT'},
            {'code': '035720', 'name': '카카오', 'sector': 'IT'},
            {'code': '051910', 'name': 'LG화학', 'sector': '화학'},
            {'code': '006400', 'name': '삼성SDI', 'sector': '전기전자'},
            {'code': '068270', 'name': '셀트리온', 'sector': '의약품'},
            {'code': '105560', 'name': 'KB금융', 'sector': '금융'},
            {'code': '055550', 'name': '신한지주', 'sector': '금융'},
            {'code': '096770', 'name': 'SK이노베이션', 'sector': '화학'},
            {'code': '003670', 'name': '포스코홀딩스', 'sector': '철강'},
            {'code': '028260', 'name': '삼성물산', 'sector': '건설'},
            {'code': '012330', 'name': '현대모비스', 'sector': '자동차'},
            {'code': '005380', 'name': '현대차', 'sector': '자동차'},
            {'code': '000270', 'name': '기아', 'sector': '자동차'},
            {'code': '066570', 'name': 'LG전자', 'sector': '전기전자'},
            {'code': '034730', 'name': 'SK', 'sector': '지주'},
            {'code': '018260', 'name': '삼성에스디에스', 'sector': 'IT'},
            {'code': '017670', 'name': 'SK텔레콤', 'sector': '통신'},
            {'code': '030200', 'name': 'KT', 'sector': '통신'},
        ]
    else:
        stocks = [
            {'code': 'AAPL', 'name': 'Apple Inc.', 'sector': 'Technology'},
            {'code': 'MSFT', 'name': 'Microsoft Corp.', 'sector': 'Technology'},
            {'code': 'GOOGL', 'name': 'Alphabet Inc.', 'sector': 'Technology'},
            {'code': 'AMZN', 'name': 'Amazon.com Inc.', 'sector': 'Consumer'},
            {'code': 'NVDA', 'name': 'NVIDIA Corp.', 'sector': 'Technology'},
            {'code': 'META', 'name': 'Meta Platforms', 'sector': 'Technology'},
            {'code': 'TSLA', 'name': 'Tesla Inc.', 'sector': 'Automotive'},
            {'code': 'JPM', 'name': 'JPMorgan Chase', 'sector': 'Finance'},
            {'code': 'V', 'name': 'Visa Inc.', 'sector': 'Finance'},
            {'code': 'JNJ', 'name': 'Johnson & Johnson', 'sector': 'Healthcare'},
        ]

    # Add random metrics
    for stock in stocks:
        stock.update({
            'price': random.randint(10000, 500000) if market == 'KR' else round(random.uniform(50, 500), 2),
            'change_rate': round(random.uniform(-5, 5), 2),
            'market_cap': random.randint(10000, 500000) * 100000000,  # 억원 단위
            'volume': random.randint(100000, 10000000),
            'per': round(random.uniform(5, 30), 2),
            'pbr': round(random.uniform(0.5, 3.0), 2),
            'roe': round(random.uniform(5, 25), 2),
            'dividend_yield': round(random.uniform(0, 5), 2),
            'debt_ratio': round(random.uniform(20, 150), 2),
            'rsi': round(random.uniform(20, 80), 2),
        })

    return stocks


def _apply_preset_filter(stocks, preset_name, params):
    """Apply preset filter to stocks"""
    filtered = []

    for stock in stocks:
        passed = True

        if preset_name == 'value':
            if stock['per'] > params.get('max_per', 10):
                passed = False
            if stock['pbr'] > params.get('max_pbr', 1.0):
                passed = False
            if stock['roe'] < params.get('min_roe', 5):
                passed = False

        elif preset_name == 'growth':
            if stock['per'] > params.get('max_per', 30):
                passed = False
            # Simplified for demo

        elif preset_name == 'dividend':
            if stock['dividend_yield'] < params.get('min_dividend_yield', 3):
                passed = False

        elif preset_name == 'momentum':
            if stock['change_rate'] < params.get('min_return_1m', 5):
                passed = False

        elif preset_name == 'quality':
            if stock['roe'] < params.get('min_roe', 15):
                passed = False
            if stock['debt_ratio'] > params.get('max_debt_ratio', 100):
                passed = False

        elif preset_name == 'contrarian':
            if stock['rsi'] > params.get('max_rsi', 30):
                passed = False

        # For other presets, use random selection for demo
        else:
            import random
            passed = random.random() > 0.6

        if passed:
            filtered.append(stock)

    return filtered


def _apply_custom_filter(stocks, params):
    """Apply custom filter to stocks"""
    conditions = params.get('conditions', [])
    combine_mode = params.get('combine_mode', 'AND')
    filtered = []

    for stock in stocks:
        results = []

        for cond in conditions:
            class_name = cond.get('class_name', '')
            cond_params = cond.get('params', {})
            passed = True

            # Simplified condition checking for demo
            if 'PER' in class_name:
                threshold = cond_params.get('threshold', 15)
                if 'Below' in class_name:
                    passed = stock['per'] <= threshold
                else:
                    passed = stock['per'] >= threshold

            elif 'PBR' in class_name:
                threshold = cond_params.get('threshold', 1.0)
                if 'Below' in class_name:
                    passed = stock['pbr'] <= threshold
                else:
                    passed = stock['pbr'] >= threshold

            elif 'ROE' in class_name:
                threshold = cond_params.get('threshold', 10)
                passed = stock['roe'] >= threshold

            elif 'MarketCap' in class_name:
                threshold = cond_params.get('threshold', 1000) * 100000000
                if 'Below' in class_name:
                    passed = stock['market_cap'] <= threshold
                else:
                    passed = stock['market_cap'] >= threshold

            elif 'RSI' in class_name:
                threshold = cond_params.get('threshold', 30)
                if 'Below' in class_name:
                    passed = stock['rsi'] <= threshold
                else:
                    passed = stock['rsi'] >= threshold

            results.append(passed)

        # Combine results
        if combine_mode == 'AND':
            if all(results):
                filtered.append(stock)
        else:  # OR
            if any(results):
                filtered.append(stock)

    return filtered
