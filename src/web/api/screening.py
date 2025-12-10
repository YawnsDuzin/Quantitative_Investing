"""
Screening API
종목 스크리닝 API

스크리닝 조건 설정, 실행, 결과 조회를 제공합니다.
"""

from flask import Blueprint, jsonify, request
from typing import Any, Dict, List, Optional
import pandas as pd
import time

from ..task_manager import task_manager, TaskContext
from .. import socketio

screening_bp = Blueprint('screening', __name__)


# ===== 프리셋 관련 API =====

@screening_bp.route('/presets', methods=['GET'])
def list_presets():
    """사용 가능한 프리셋 전략 목록"""
    try:
        from src.screening import list_preset_strategies
        presets = list_preset_strategies()
        return jsonify({
            'success': True,
            'presets': presets
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@screening_bp.route('/presets/<preset_name>/info', methods=['GET'])
def get_preset_info(preset_name: str):
    """프리셋 상세 정보"""
    preset_info = {
        'value': {
            'name': '가치 투자',
            'description': '저평가된 우량 기업 발굴 (낮은 PER/PBR, 높은 ROE)',
            'parameters': [
                {'name': 'max_per', 'type': 'float', 'default': 10.0, 'description': '최대 PER'},
                {'name': 'max_pbr', 'type': 'float', 'default': 1.0, 'description': '최대 PBR'},
                {'name': 'min_roe', 'type': 'float', 'default': 10.0, 'description': '최소 ROE (%)'},
                {'name': 'max_debt_ratio', 'type': 'float', 'default': 100.0, 'description': '최대 부채비율 (%)'},
                {'name': 'min_market_cap', 'type': 'float', 'default': 1e11, 'description': '최소 시가총액'},
                {'name': 'limit', 'type': 'int', 'default': 30, 'description': '결과 개수'}
            ]
        },
        'growth': {
            'name': '성장 투자',
            'description': '고성장 기업 발굴 (높은 EPS/매출 성장률)',
            'parameters': [
                {'name': 'min_eps_growth', 'type': 'float', 'default': 20.0, 'description': '최소 EPS 성장률 (%)'},
                {'name': 'min_revenue_growth', 'type': 'float', 'default': 15.0, 'description': '최소 매출 성장률 (%)'},
                {'name': 'min_roe', 'type': 'float', 'default': 15.0, 'description': '최소 ROE (%)'},
                {'name': 'min_market_cap', 'type': 'float', 'default': 5e10, 'description': '최소 시가총액'},
                {'name': 'limit', 'type': 'int', 'default': 30, 'description': '결과 개수'}
            ]
        },
        'momentum': {
            'name': '모멘텀',
            'description': '강한 상승 추세 종목 발굴',
            'parameters': [
                {'name': 'min_volume_ratio', 'type': 'float', 'default': 1.5, 'description': '최소 거래량 비율'},
                {'name': 'min_rsi', 'type': 'float', 'default': 50.0, 'description': '최소 RSI'},
                {'name': 'max_rsi', 'type': 'float', 'default': 70.0, 'description': '최대 RSI'},
                {'name': 'min_market_cap', 'type': 'float', 'default': 1e11, 'description': '최소 시가총액'},
                {'name': 'limit', 'type': 'int', 'default': 30, 'description': '결과 개수'}
            ]
        },
        'dividend': {
            'name': '배당 투자',
            'description': '안정적인 고배당주 발굴',
            'parameters': [
                {'name': 'min_dividend_yield', 'type': 'float', 'default': 3.0, 'description': '최소 배당수익률 (%)'},
                {'name': 'max_debt_ratio', 'type': 'float', 'default': 100.0, 'description': '최대 부채비율 (%)'},
                {'name': 'min_market_cap', 'type': 'float', 'default': 5e11, 'description': '최소 시가총액'},
                {'name': 'limit', 'type': 'int', 'default': 30, 'description': '결과 개수'}
            ]
        },
        'small_cap_value': {
            'name': '소형 가치주',
            'description': '저평가된 소형주 발굴',
            'parameters': [
                {'name': 'max_market_cap', 'type': 'float', 'default': 1e11, 'description': '최대 시가총액'},
                {'name': 'min_market_cap', 'type': 'float', 'default': 1e10, 'description': '최소 시가총액'},
                {'name': 'max_per', 'type': 'float', 'default': 8.0, 'description': '최대 PER'},
                {'name': 'max_pbr', 'type': 'float', 'default': 0.8, 'description': '최대 PBR'},
                {'name': 'limit', 'type': 'int', 'default': 30, 'description': '결과 개수'}
            ]
        },
        'quality': {
            'name': '퀄리티 투자',
            'description': '재무 우량 기업 발굴',
            'parameters': [
                {'name': 'min_roe', 'type': 'float', 'default': 15.0, 'description': '최소 ROE (%)'},
                {'name': 'min_roa', 'type': 'float', 'default': 8.0, 'description': '최소 ROA (%)'},
                {'name': 'max_debt_ratio', 'type': 'float', 'default': 80.0, 'description': '최대 부채비율 (%)'},
                {'name': 'min_market_cap', 'type': 'float', 'default': 1e11, 'description': '최소 시가총액'},
                {'name': 'limit', 'type': 'int', 'default': 30, 'description': '결과 개수'}
            ]
        },
        'turnaround': {
            'name': '턴어라운드',
            'description': '실적 개선 기대 종목 발굴',
            'parameters': [
                {'name': 'near_low_percent', 'type': 'float', 'default': 20.0, 'description': '52주 저가 대비 (%)'},
                {'name': 'max_rsi', 'type': 'float', 'default': 35.0, 'description': '최대 RSI'},
                {'name': 'min_volume_ratio', 'type': 'float', 'default': 2.0, 'description': '최소 거래량 비율'},
                {'name': 'min_market_cap', 'type': 'float', 'default': 5e10, 'description': '최소 시가총액'},
                {'name': 'limit', 'type': 'int', 'default': 30, 'description': '결과 개수'}
            ]
        },
        'oversold_bounce': {
            'name': '과매도 반등',
            'description': '과매도 반등 기대 종목 발굴',
            'parameters': [
                {'name': 'max_rsi', 'type': 'float', 'default': 30.0, 'description': '최대 RSI'},
                {'name': 'min_volume', 'type': 'float', 'default': 100000, 'description': '최소 거래량'},
                {'name': 'min_market_cap', 'type': 'float', 'default': 1e11, 'description': '최소 시가총액'},
                {'name': 'limit', 'type': 'int', 'default': 30, 'description': '결과 개수'}
            ]
        },
        'breakout': {
            'name': '돌파',
            'description': '주요 저항 돌파 종목 발굴',
            'parameters': [
                {'name': 'near_high_percent', 'type': 'float', 'default': 5.0, 'description': '52주 고가 대비 (%)'},
                {'name': 'min_volume_ratio', 'type': 'float', 'default': 2.0, 'description': '최소 거래량 비율'},
                {'name': 'min_market_cap', 'type': 'float', 'default': 1e11, 'description': '최소 시가총액'},
                {'name': 'limit', 'type': 'int', 'default': 30, 'description': '결과 개수'}
            ]
        },
        'income': {
            'name': '인컴 투자',
            'description': '안정적 수입 추구 (고배당 대형주)',
            'parameters': [
                {'name': 'min_dividend_yield', 'type': 'float', 'default': 2.5, 'description': '최소 배당수익률 (%)'},
                {'name': 'min_market_cap', 'type': 'float', 'default': 1e12, 'description': '최소 시가총액'},
                {'name': 'max_debt_ratio', 'type': 'float', 'default': 80.0, 'description': '최대 부채비율 (%)'},
                {'name': 'limit', 'type': 'int', 'default': 30, 'description': '결과 개수'}
            ]
        }
    }

    if preset_name not in preset_info:
        return jsonify({
            'success': False,
            'error': f'프리셋을 찾을 수 없습니다: {preset_name}'
        }), 404

    return jsonify({
        'success': True,
        'preset': preset_info[preset_name]
    })


# ===== 조건 관련 API =====

@screening_bp.route('/conditions', methods=['GET'])
def list_conditions():
    """사용 가능한 조건 클래스 목록"""
    conditions = {
        'price': [
            {'name': 'PriceAbove', 'description': '주가 >= 값', 'params': ['threshold']},
            {'name': 'PriceBelow', 'description': '주가 <= 값', 'params': ['threshold']},
            {'name': 'PriceBetween', 'description': '주가 범위', 'params': ['min_price', 'max_price']},
            {'name': 'PriceChangePercent', 'description': '변동률 조건', 'params': ['min_change', 'max_change']},
            {'name': 'Above52WeekHigh', 'description': '52주 신고가 돌파', 'params': []},
            {'name': 'Below52WeekLow', 'description': '52주 신저가 하회', 'params': []},
            {'name': 'VolumeAbove', 'description': '거래량 >= 값', 'params': ['threshold']},
            {'name': 'VolumeRatio', 'description': '거래량 비율', 'params': ['min_ratio', 'max_ratio']},
        ],
        'technical': [
            {'name': 'PriceAboveSMA', 'description': '주가 > SMA', 'params': ['period']},
            {'name': 'PriceBelowSMA', 'description': '주가 < SMA', 'params': ['period']},
            {'name': 'GoldenCross', 'description': '골든크로스', 'params': ['short_period', 'long_period']},
            {'name': 'DeathCross', 'description': '데드크로스', 'params': ['short_period', 'long_period']},
            {'name': 'RSIOverbought', 'description': 'RSI 과매수', 'params': ['threshold']},
            {'name': 'RSIOversold', 'description': 'RSI 과매도', 'params': ['threshold']},
            {'name': 'MACDCondition', 'description': 'MACD 조건', 'params': ['signal']},
            {'name': 'BollingerBandCondition', 'description': '볼린저밴드', 'params': ['position']},
            {'name': 'ADXCondition', 'description': 'ADX 추세 강도', 'params': ['min_value', 'max_value']},
        ],
        'fundamental': [
            {'name': 'MarketCapAbove', 'description': '시가총액 >= 값', 'params': ['threshold']},
            {'name': 'MarketCapBelow', 'description': '시가총액 <= 값', 'params': ['threshold']},
            {'name': 'PERBelow', 'description': 'PER <= 값', 'params': ['threshold']},
            {'name': 'PBRBelow', 'description': 'PBR <= 값', 'params': ['threshold']},
            {'name': 'DividendYieldAbove', 'description': '배당수익률 >= 값', 'params': ['threshold']},
            {'name': 'ROEAbove', 'description': 'ROE >= 값', 'params': ['threshold']},
            {'name': 'DebtRatioBelow', 'description': '부채비율 <= 값', 'params': ['threshold']},
            {'name': 'EPSGrowthAbove', 'description': 'EPS 성장률 >= 값', 'params': ['threshold']},
        ],
        'market': [
            {'name': 'MarketIs', 'description': '특정 시장', 'params': ['market']},
            {'name': 'SectorIs', 'description': '특정 섹터', 'params': ['sector']},
            {'name': 'ExcludeAdministrative', 'description': '관리종목 제외', 'params': []},
            {'name': 'ExcludeETF', 'description': 'ETF 제외', 'params': []},
            {'name': 'IndexMember', 'description': '지수 구성종목', 'params': ['index_name']},
        ]
    }

    return jsonify({
        'success': True,
        'conditions': conditions
    })


# ===== 스크리닝 실행 API =====

@screening_bp.route('/run/preset', methods=['POST'])
def run_preset_screening():
    """프리셋 전략으로 스크리닝 실행"""
    data = request.get_json() or {}
    preset_name = data.get('preset', 'value')
    params = data.get('params', {})
    market = data.get('market', 'KR')  # KR 또는 US

    # 작업 생성
    task = task_manager.create_task(f"스크리닝: {preset_name}")

    # 진행 상황 WebSocket 콜백 등록
    def emit_progress(t):
        socketio.emit('task_progress', t.to_dict(), namespace='/screening')

    task_manager.add_progress_callback(task.id, emit_progress)

    # 백그라운드 실행
    task_manager.run_task(
        task,
        _run_preset_screening_task,
        preset_name=preset_name,
        params=params,
        market=market
    )

    return jsonify({
        'success': True,
        'task_id': task.id,
        'message': '스크리닝 작업이 시작되었습니다'
    })


@screening_bp.route('/run/custom', methods=['POST'])
def run_custom_screening():
    """커스텀 조건으로 스크리닝 실행"""
    data = request.get_json() or {}
    conditions = data.get('conditions', [])
    sort_by = data.get('sort_by', 'market_cap')
    sort_ascending = data.get('sort_ascending', False)
    limit = data.get('limit', 50)
    market = data.get('market', 'KR')

    if not conditions:
        return jsonify({
            'success': False,
            'error': '조건을 지정해주세요'
        }), 400

    # 작업 생성
    task = task_manager.create_task("커스텀 스크리닝")

    # 진행 상황 WebSocket 콜백 등록
    def emit_progress(t):
        socketio.emit('task_progress', t.to_dict(), namespace='/screening')

    task_manager.add_progress_callback(task.id, emit_progress)

    # 백그라운드 실행
    task_manager.run_task(
        task,
        _run_custom_screening_task,
        conditions=conditions,
        sort_by=sort_by,
        sort_ascending=sort_ascending,
        limit=limit,
        market=market
    )

    return jsonify({
        'success': True,
        'task_id': task.id,
        'message': '스크리닝 작업이 시작되었습니다'
    })


# ===== 스크리닝 작업 함수 =====

def _run_preset_screening_task(
    ctx: TaskContext,
    preset_name: str,
    params: Dict[str, Any],
    market: str
) -> Dict[str, Any]:
    """프리셋 스크리닝 실행 (백그라운드)"""

    ctx.log(f"프리셋 '{preset_name}' 스크리닝 시작")
    ctx.update_progress(0, 100, "초기화 중...")

    # 1. 데이터 로드 (30%)
    ctx.log("주식 데이터 로드 중...")
    ctx.update_progress(5, 100, "데이터 로드 중...")

    data = _load_stock_data(ctx, market)
    if data is None or data.empty:
        raise Exception("데이터를 로드할 수 없습니다")

    ctx.update_progress(30, 100, f"{len(data)}개 종목 데이터 로드 완료")
    ctx.log(f"{len(data)}개 종목 데이터 로드 완료")

    ctx.check_cancelled()

    # 2. 스크리너 생성 (40%)
    ctx.update_progress(35, 100, "스크리너 생성 중...")
    ctx.log(f"프리셋 '{preset_name}' 스크리너 생성")

    try:
        from src.screening import get_preset_strategy
        screener = get_preset_strategy(preset_name, **params)
    except Exception as e:
        raise Exception(f"프리셋 생성 실패: {str(e)}")

    ctx.update_progress(40, 100, "스크리너 생성 완료")

    ctx.check_cancelled()

    # 3. 스크리닝 실행 (80%)
    ctx.update_progress(45, 100, "스크리닝 실행 중...")
    ctx.log("조건 필터링 실행 중...")

    try:
        results = screener.screen(data)
    except ValueError as e:
        # 필요한 컬럼이 없는 경우 샘플 데이터로 시뮬레이션
        ctx.log(f"경고: {str(e)} - 샘플 데이터로 시뮬레이션")
        results = _simulate_screening(data, preset_name, params)

    ctx.update_progress(80, 100, f"{len(results)}개 종목 필터링 완료")
    ctx.log(f"{len(results)}개 종목 조건 충족")

    ctx.check_cancelled()

    # 4. 결과 정리 (100%)
    ctx.update_progress(90, 100, "결과 정리 중...")

    result_data = _format_results(results)

    ctx.update_progress(100, 100, "완료")
    ctx.log("스크리닝 완료")

    return {
        'preset': preset_name,
        'params': params,
        'total_stocks': len(data),
        'filtered_stocks': len(results),
        'results': result_data
    }


def _run_custom_screening_task(
    ctx: TaskContext,
    conditions: List[Dict],
    sort_by: str,
    sort_ascending: bool,
    limit: int,
    market: str
) -> Dict[str, Any]:
    """커스텀 스크리닝 실행 (백그라운드)"""

    ctx.log("커스텀 스크리닝 시작")
    ctx.update_progress(0, 100, "초기화 중...")

    # 1. 데이터 로드
    ctx.log("주식 데이터 로드 중...")
    ctx.update_progress(5, 100, "데이터 로드 중...")

    data = _load_stock_data(ctx, market)
    if data is None or data.empty:
        raise Exception("데이터를 로드할 수 없습니다")

    ctx.update_progress(30, 100, f"{len(data)}개 종목 데이터 로드 완료")
    ctx.log(f"{len(data)}개 종목 데이터 로드 완료")

    ctx.check_cancelled()

    # 2. 조건 파싱 및 스크리너 생성
    ctx.update_progress(35, 100, "조건 파싱 중...")
    ctx.log(f"{len(conditions)}개 조건 파싱")

    from src.screening import ScreenerBuilder
    builder = ScreenerBuilder("커스텀 스크리너")

    for i, cond in enumerate(conditions):
        ctx.check_cancelled()
        ctx.update_progress(35 + (i / len(conditions) * 10), 100, f"조건 {i+1}/{len(conditions)} 적용 중...")

        try:
            _apply_condition(builder, cond)
            ctx.log(f"조건 적용: {cond.get('type')}")
        except Exception as e:
            ctx.log(f"조건 적용 실패: {cond.get('type')} - {str(e)}")

    builder.sort_by(sort_by, ascending=sort_ascending)
    builder.limit(limit)

    ctx.update_progress(45, 100, "스크리너 생성 완료")

    ctx.check_cancelled()

    # 3. 스크리닝 실행
    ctx.update_progress(50, 100, "스크리닝 실행 중...")
    ctx.log("조건 필터링 실행 중...")

    try:
        results = builder.screen(data)
    except ValueError as e:
        ctx.log(f"경고: {str(e)} - 기본 필터링 적용")
        results = data.head(limit)

    ctx.update_progress(80, 100, f"{len(results)}개 종목 필터링 완료")
    ctx.log(f"{len(results)}개 종목 조건 충족")

    ctx.check_cancelled()

    # 4. 결과 정리
    ctx.update_progress(90, 100, "결과 정리 중...")

    result_data = _format_results(results)

    ctx.update_progress(100, 100, "완료")
    ctx.log("스크리닝 완료")

    return {
        'conditions_count': len(conditions),
        'total_stocks': len(data),
        'filtered_stocks': len(results),
        'results': result_data
    }


def _load_stock_data(ctx: TaskContext, market: str) -> pd.DataFrame:
    """주식 데이터 로드"""
    try:
        # 데이터베이스에서 로드 시도
        from src.utils.database import DatabaseManager
        db = DatabaseManager()
        data = db.get_latest_stock_data(market=market)
        if data is not None and not data.empty:
            return data
    except Exception as e:
        ctx.log(f"DB 로드 실패: {str(e)}")

    # 샘플 데이터 생성 (데모용)
    ctx.log("샘플 데이터 생성 중...")
    return _generate_sample_data(market)


def _generate_sample_data(market: str) -> pd.DataFrame:
    """샘플 데이터 생성 (데모용)"""
    import numpy as np

    if market == 'KR':
        symbols = [
            ('005930', '삼성전자'), ('000660', 'SK하이닉스'), ('035420', 'NAVER'),
            ('051910', 'LG화학'), ('006400', '삼성SDI'), ('035720', '카카오'),
            ('005380', '현대차'), ('000270', '기아'), ('068270', '셀트리온'),
            ('207940', '삼성바이오로직스'), ('005490', 'POSCO홀딩스'),
            ('012330', '현대모비스'), ('055550', '신한지주'), ('105560', 'KB금융'),
            ('003670', '포스코퓨처엠'), ('066570', 'LG전자'), ('028260', '삼성물산'),
            ('096770', 'SK이노베이션'), ('034730', 'SK'), ('003550', 'LG'),
            ('373220', 'LG에너지솔루션'), ('000810', '삼성화재'), ('032830', '삼성생명'),
            ('018260', '삼성에스디에스'), ('090430', '아모레퍼시픽'),
        ]
    else:
        symbols = [
            ('AAPL', 'Apple Inc.'), ('MSFT', 'Microsoft'), ('GOOGL', 'Alphabet'),
            ('AMZN', 'Amazon'), ('NVDA', 'NVIDIA'), ('META', 'Meta'),
            ('TSLA', 'Tesla'), ('BRK.B', 'Berkshire'), ('JPM', 'JPMorgan'),
            ('V', 'Visa'), ('UNH', 'UnitedHealth'), ('JNJ', 'Johnson & Johnson'),
            ('WMT', 'Walmart'), ('PG', 'Procter & Gamble'), ('MA', 'Mastercard'),
        ]

    np.random.seed(42)
    n = len(symbols)

    data = pd.DataFrame({
        'symbol': [s[0] for s in symbols],
        'name': [s[1] for s in symbols],
        'close': np.random.uniform(10000, 500000, n) if market == 'KR' else np.random.uniform(50, 500, n),
        'open': np.random.uniform(10000, 500000, n) if market == 'KR' else np.random.uniform(50, 500, n),
        'high': np.random.uniform(10000, 500000, n) if market == 'KR' else np.random.uniform(50, 500, n),
        'low': np.random.uniform(10000, 500000, n) if market == 'KR' else np.random.uniform(50, 500, n),
        'volume': np.random.uniform(100000, 10000000, n).astype(int),
        'market_cap': np.random.uniform(1e10, 5e14, n),
        'per': np.random.uniform(5, 50, n),
        'pbr': np.random.uniform(0.5, 5, n),
        'roe': np.random.uniform(5, 30, n),
        'roa': np.random.uniform(2, 15, n),
        'dividend_yield': np.random.uniform(0, 5, n),
        'debt_ratio': np.random.uniform(20, 200, n),
        'rsi': np.random.uniform(20, 80, n),
        'change_pct': np.random.uniform(-5, 5, n),
        'market': market,
    })

    return data


def _simulate_screening(
    data: pd.DataFrame,
    preset_name: str,
    params: Dict
) -> pd.DataFrame:
    """간단한 스크리닝 시뮬레이션"""
    result = data.copy()
    limit = params.get('limit', 30)

    # 프리셋별 간단한 필터링
    if preset_name == 'value':
        max_per = params.get('max_per', 10)
        max_pbr = params.get('max_pbr', 1.0)
        if 'per' in result.columns:
            result = result[result['per'] <= max_per]
        if 'pbr' in result.columns:
            result = result[result['pbr'] <= max_pbr]
        if 'per' in result.columns:
            result = result.sort_values('per')

    elif preset_name == 'growth':
        if 'roe' in result.columns:
            result = result.sort_values('roe', ascending=False)

    elif preset_name == 'momentum':
        if 'rsi' in result.columns:
            result = result[(result['rsi'] >= 50) & (result['rsi'] <= 70)]
            result = result.sort_values('rsi', ascending=False)

    elif preset_name == 'dividend':
        if 'dividend_yield' in result.columns:
            result = result.sort_values('dividend_yield', ascending=False)

    elif preset_name in ['quality', 'income']:
        if 'roe' in result.columns:
            result = result.sort_values('roe', ascending=False)

    else:
        if 'market_cap' in result.columns:
            result = result.sort_values('market_cap', ascending=False)

    return result.head(limit)


def _apply_condition(builder, condition: Dict) -> None:
    """조건 적용"""
    cond_type = condition.get('type', '')
    params = condition.get('params', {})

    # 가격 조건
    if cond_type == 'PriceAbove':
        builder.price_above(params.get('threshold', 0))
    elif cond_type == 'PriceBelow':
        builder.price_below(params.get('threshold', 999999999))
    elif cond_type == 'VolumeAbove':
        builder.volume_above(params.get('threshold', 0))

    # 기술적 조건
    elif cond_type == 'RSIOversold':
        builder.rsi_below(params.get('threshold', 30))
    elif cond_type == 'RSIOverbought':
        builder.rsi_above(params.get('threshold', 70))
    elif cond_type == 'PriceAboveSMA':
        builder.price_above_sma(params.get('period', 200))
    elif cond_type == 'GoldenCross':
        builder.golden_cross(params.get('short_period', 50), params.get('long_period', 200))

    # 펀더멘털 조건
    elif cond_type == 'MarketCapAbove':
        builder.market_cap_above(params.get('threshold', 0))
    elif cond_type == 'MarketCapBelow':
        builder.market_cap_below(params.get('threshold', 999999999999999))
    elif cond_type == 'PERBelow':
        builder.per_below(params.get('threshold', 999))
    elif cond_type == 'PBRBelow':
        builder.pbr_below(params.get('threshold', 999))
    elif cond_type == 'ROEAbove':
        builder.roe_above(params.get('threshold', 0))
    elif cond_type == 'DividendYieldAbove':
        builder.dividend_yield_above(params.get('threshold', 0))
    elif cond_type == 'DebtRatioBelow':
        builder.debt_ratio_below(params.get('threshold', 999))

    # 시장 조건
    elif cond_type == 'ExcludeAdministrative':
        builder.exclude_administrative()
    elif cond_type == 'ExcludeETF':
        builder.exclude_etf()


def _format_results(df: pd.DataFrame) -> List[Dict]:
    """결과 포맷팅"""
    if df.empty:
        return []

    # 필요한 컬럼만 선택
    columns = ['symbol', 'name', 'close', 'change_pct', 'volume', 'market_cap',
               'per', 'pbr', 'roe', 'dividend_yield', 'rsi']
    available_cols = [c for c in columns if c in df.columns]

    result_df = df[available_cols].copy()

    # NaN을 None으로 변환
    result_df = result_df.where(pd.notnull(result_df), None)

    return result_df.to_dict(orient='records')


# ===== WebSocket 이벤트 =====

@socketio.on('connect', namespace='/screening')
def handle_connect():
    """WebSocket 연결"""
    print('Client connected to /screening namespace')


@socketio.on('disconnect', namespace='/screening')
def handle_disconnect():
    """WebSocket 연결 해제"""
    print('Client disconnected from /screening namespace')


@socketio.on('subscribe_task', namespace='/screening')
def handle_subscribe_task(data):
    """작업 구독"""
    task_id = data.get('task_id')
    if task_id:
        task = task_manager.get_task(task_id)
        if task:
            socketio.emit('task_progress', task.to_dict(), namespace='/screening')
