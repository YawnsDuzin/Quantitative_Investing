"""
Preset Screening Strategies
프리셋 스크리닝 전략

자주 사용되는 스크리닝 전략을 미리 정의합니다.
"""

from typing import Dict, List, Optional, Type
from ..screener import StockScreener, ScreenerBuilder


class BasePreset:
    """프리셋 전략 기본 클래스"""

    name: str = "Base Preset"
    description: str = "기본 프리셋"

    @classmethod
    def create(cls, **kwargs) -> StockScreener:
        """프리셋 스크리너 생성"""
        raise NotImplementedError

    @classmethod
    def get_description(cls) -> str:
        """프리셋 설명 반환"""
        return cls.description


class ValueInvestingPreset(BasePreset):
    """
    가치 투자 전략

    저평가된 우량 기업을 찾습니다.
    - 낮은 PER (10 이하)
    - 낮은 PBR (1.0 이하)
    - 높은 ROE (10% 이상)
    - 적정 부채비율 (100% 이하)
    - 일정 규모 이상 시가총액
    """

    name = "가치 투자"
    description = "저평가된 우량 기업 발굴 (낮은 PER/PBR, 높은 ROE)"

    @classmethod
    def create(
        cls,
        max_per: float = 10.0,
        max_pbr: float = 1.0,
        min_roe: float = 10.0,
        max_debt_ratio: float = 100.0,
        min_market_cap: float = 1e11,  # 1000억
        limit: int = 30
    ) -> StockScreener:
        """
        Args:
            max_per: 최대 PER
            max_pbr: 최대 PBR
            min_roe: 최소 ROE (%)
            max_debt_ratio: 최대 부채비율 (%)
            min_market_cap: 최소 시가총액
            limit: 결과 개수 제한
        """
        return (ScreenerBuilder(cls.name)
            .per_below(max_per)
            .pbr_below(max_pbr)
            .roe_above(min_roe)
            .debt_ratio_below(max_debt_ratio)
            .market_cap_above(min_market_cap)
            .exclude_administrative()
            .sort_by('per', ascending=True)
            .limit(limit)
            .build())


class GrowthInvestingPreset(BasePreset):
    """
    성장 투자 전략

    고성장 기업을 찾습니다.
    - 높은 EPS 성장률 (20% 이상)
    - 높은 매출 성장률 (15% 이상)
    - 높은 ROE (15% 이상)
    - 일정 규모 이상 시가총액
    """

    name = "성장 투자"
    description = "고성장 기업 발굴 (높은 EPS/매출 성장률)"

    @classmethod
    def create(
        cls,
        min_eps_growth: float = 20.0,
        min_revenue_growth: float = 15.0,
        min_roe: float = 15.0,
        min_market_cap: float = 5e10,  # 500억
        limit: int = 30
    ) -> StockScreener:
        """
        Args:
            min_eps_growth: 최소 EPS 성장률 (%)
            min_revenue_growth: 최소 매출 성장률 (%)
            min_roe: 최소 ROE (%)
            min_market_cap: 최소 시가총액
            limit: 결과 개수 제한
        """
        return (ScreenerBuilder(cls.name)
            .eps_growth_above(min_eps_growth)
            .revenue_growth_above(min_revenue_growth)
            .roe_above(min_roe)
            .market_cap_above(min_market_cap)
            .exclude_administrative()
            .sort_by('eps_growth', ascending=False)
            .limit(limit)
            .build())


class MomentumPreset(BasePreset):
    """
    모멘텀 투자 전략

    강한 상승 추세의 종목을 찾습니다.
    - 주가가 200일 이동평균 위
    - 주가가 50일 이동평균 위
    - RSI 50 이상 (상승 추세)
    - 평균 대비 높은 거래량
    """

    name = "모멘텀"
    description = "강한 상승 추세 종목 발굴 (이동평균 돌파, RSI 상승)"

    @classmethod
    def create(
        cls,
        min_volume_ratio: float = 1.5,
        min_rsi: float = 50.0,
        max_rsi: float = 70.0,
        min_market_cap: float = 1e11,
        limit: int = 30
    ) -> StockScreener:
        """
        Args:
            min_volume_ratio: 최소 거래량 비율
            min_rsi: 최소 RSI
            max_rsi: 최대 RSI (과매수 제외)
            min_market_cap: 최소 시가총액
            limit: 결과 개수 제한
        """
        return (ScreenerBuilder(cls.name)
            .price_above_sma(200)
            .price_above_sma(50)
            .rsi_between(min_rsi, max_rsi)
            .volume_ratio_above(min_volume_ratio)
            .market_cap_above(min_market_cap)
            .exclude_administrative()
            .sort_by('rsi', ascending=False)
            .limit(limit)
            .build())


class DividendPreset(BasePreset):
    """
    배당 투자 전략

    안정적인 고배당 종목을 찾습니다.
    - 높은 배당수익률 (3% 이상)
    - 낮은 부채비율 (재무 안정)
    - 흑자 기업 (PER 양수)
    - 일정 규모 이상 시가총액
    """

    name = "배당 투자"
    description = "안정적인 고배당주 발굴 (높은 배당수익률, 재무 안정)"

    @classmethod
    def create(
        cls,
        min_dividend_yield: float = 3.0,
        max_debt_ratio: float = 100.0,
        min_market_cap: float = 5e11,  # 5000억
        limit: int = 30
    ) -> StockScreener:
        """
        Args:
            min_dividend_yield: 최소 배당수익률 (%)
            max_debt_ratio: 최대 부채비율 (%)
            min_market_cap: 최소 시가총액
            limit: 결과 개수 제한
        """
        return (ScreenerBuilder(cls.name)
            .dividend_yield_above(min_dividend_yield)
            .debt_ratio_below(max_debt_ratio)
            .per_above(0)  # 흑자 기업
            .market_cap_above(min_market_cap)
            .exclude_administrative()
            .sort_by('dividend_yield', ascending=False)
            .limit(limit)
            .build())


class SmallCapValuePreset(BasePreset):
    """
    소형 가치주 전략

    저평가된 소형주를 찾습니다.
    - 소형주 (시가총액 1000억 이하)
    - 낮은 PER
    - 낮은 PBR
    - 적정 부채비율
    """

    name = "소형 가치주"
    description = "저평가된 소형주 발굴 (소형주 + 가치)"

    @classmethod
    def create(
        cls,
        max_market_cap: float = 1e11,  # 1000억
        min_market_cap: float = 1e10,  # 100억
        max_per: float = 8.0,
        max_pbr: float = 0.8,
        max_debt_ratio: float = 80.0,
        limit: int = 30
    ) -> StockScreener:
        """
        Args:
            max_market_cap: 최대 시가총액
            min_market_cap: 최소 시가총액
            max_per: 최대 PER
            max_pbr: 최대 PBR
            max_debt_ratio: 최대 부채비율 (%)
            limit: 결과 개수 제한
        """
        return (ScreenerBuilder(cls.name)
            .market_cap_between(min_market_cap, max_market_cap)
            .per_below(max_per)
            .pbr_below(max_pbr)
            .debt_ratio_below(max_debt_ratio)
            .exclude_administrative()
            .sort_by('pbr', ascending=True)
            .limit(limit)
            .build())


class QualityPreset(BasePreset):
    """
    퀄리티 투자 전략

    재무적으로 우수한 기업을 찾습니다.
    - 높은 ROE (15% 이상)
    - 높은 ROA (8% 이상)
    - 낮은 부채비율
    - 높은 영업이익률
    """

    name = "퀄리티 투자"
    description = "재무 우량 기업 발굴 (높은 ROE/ROA, 낮은 부채)"

    @classmethod
    def create(
        cls,
        min_roe: float = 15.0,
        min_roa: float = 8.0,
        max_debt_ratio: float = 80.0,
        min_market_cap: float = 1e11,
        limit: int = 30
    ) -> StockScreener:
        """
        Args:
            min_roe: 최소 ROE (%)
            min_roa: 최소 ROA (%)
            max_debt_ratio: 최대 부채비율 (%)
            min_market_cap: 최소 시가총액
            limit: 결과 개수 제한
        """
        return (ScreenerBuilder(cls.name)
            .roe_above(min_roe)
            .roa_above(min_roa)
            .debt_ratio_below(max_debt_ratio)
            .market_cap_above(min_market_cap)
            .exclude_administrative()
            .sort_by('roe', ascending=False)
            .limit(limit)
            .build())


class TurnaroundPreset(BasePreset):
    """
    턴어라운드 전략

    실적 개선이 기대되는 종목을 찾습니다.
    - 52주 저점 근처
    - RSI 과매도 구간
    - 최근 거래량 증가
    """

    name = "턴어라운드"
    description = "실적 개선 기대 종목 발굴 (저점 매수 기회)"

    @classmethod
    def create(
        cls,
        near_low_percent: float = 20.0,
        max_rsi: float = 35.0,
        min_volume_ratio: float = 2.0,
        min_market_cap: float = 5e10,
        limit: int = 30
    ) -> StockScreener:
        """
        Args:
            near_low_percent: 52주 저가 대비 허용 범위 (%)
            max_rsi: 최대 RSI
            min_volume_ratio: 최소 거래량 비율
            min_market_cap: 최소 시가총액
            limit: 결과 개수 제한
        """
        from ..conditions.price_conditions import NearLowPercent
        from ..conditions.technical_conditions import RSIOversold
        from ..conditions.price_conditions import VolumeRatio
        from ..conditions.fundamental_conditions import MarketCapAbove
        from ..conditions.market_conditions import ExcludeAdministrative

        screener = StockScreener(cls.name)
        screener.add_condition(NearLowPercent(near_low_percent))
        screener.add_condition(RSIOversold(max_rsi))
        screener.add_condition(VolumeRatio(min_ratio=min_volume_ratio))
        screener.add_condition(MarketCapAbove(min_market_cap))
        screener.add_condition(ExcludeAdministrative())
        screener.set_sort('rsi', ascending=True)
        screener.set_limit(limit)

        return screener


class OversoldBouncePreset(BasePreset):
    """
    과매도 반등 전략

    기술적 과매도 상태에서 반등이 기대되는 종목을 찾습니다.
    - RSI 30 이하
    - 볼린저밴드 하단 이탈
    - 일정 규모 이상 거래량
    """

    name = "과매도 반등"
    description = "과매도 반등 기대 종목 발굴 (기술적 저점)"

    @classmethod
    def create(
        cls,
        max_rsi: float = 30.0,
        min_volume: float = 100000,
        min_market_cap: float = 1e11,
        limit: int = 30
    ) -> StockScreener:
        """
        Args:
            max_rsi: 최대 RSI
            min_volume: 최소 거래량
            min_market_cap: 최소 시가총액
            limit: 결과 개수 제한
        """
        return (ScreenerBuilder(cls.name)
            .rsi_below(max_rsi)
            .bollinger_below_lower()
            .volume_above(min_volume)
            .market_cap_above(min_market_cap)
            .exclude_administrative()
            .sort_by('rsi', ascending=True)
            .limit(limit)
            .build())


class BreakoutPreset(BasePreset):
    """
    돌파 전략

    주요 저항선을 돌파하는 종목을 찾습니다.
    - 52주 신고가 돌파 또는 근접
    - 골든크로스
    - 높은 거래량
    """

    name = "돌파"
    description = "주요 저항 돌파 종목 발굴 (신고가, 골든크로스)"

    @classmethod
    def create(
        cls,
        near_high_percent: float = 5.0,
        min_volume_ratio: float = 2.0,
        min_market_cap: float = 1e11,
        limit: int = 30
    ) -> StockScreener:
        """
        Args:
            near_high_percent: 52주 고가 대비 허용 범위 (%)
            min_volume_ratio: 최소 거래량 비율
            min_market_cap: 최소 시가총액
            limit: 결과 개수 제한
        """
        from ..conditions.price_conditions import NearHighPercent
        from ..conditions.technical_conditions import GoldenCross
        from ..conditions.price_conditions import VolumeRatio
        from ..conditions.fundamental_conditions import MarketCapAbove
        from ..conditions.market_conditions import ExcludeAdministrative

        screener = StockScreener(cls.name)
        screener.add_condition(NearHighPercent(near_high_percent))
        screener.add_condition(GoldenCross())
        screener.add_condition(VolumeRatio(min_ratio=min_volume_ratio))
        screener.add_condition(MarketCapAbove(min_market_cap))
        screener.add_condition(ExcludeAdministrative())
        screener.set_sort('close', ascending=False)
        screener.set_limit(limit)

        return screener


class IncomePreset(BasePreset):
    """
    인컴 투자 전략 (배당 + 안정성)

    안정적인 수입을 원하는 투자자를 위한 전략
    - 높은 배당수익률
    - 대형주 (안정성)
    - 낮은 변동성
    """

    name = "인컴 투자"
    description = "안정적 수입 추구 (고배당 대형주)"

    @classmethod
    def create(
        cls,
        min_dividend_yield: float = 2.5,
        min_market_cap: float = 1e12,  # 1조원
        max_debt_ratio: float = 80.0,
        limit: int = 30
    ) -> StockScreener:
        """
        Args:
            min_dividend_yield: 최소 배당수익률 (%)
            min_market_cap: 최소 시가총액
            max_debt_ratio: 최대 부채비율 (%)
            limit: 결과 개수 제한
        """
        return (ScreenerBuilder(cls.name)
            .dividend_yield_above(min_dividend_yield)
            .market_cap_above(min_market_cap)
            .debt_ratio_below(max_debt_ratio)
            .per_above(0)  # 흑자 기업
            .exclude_administrative()
            .sort_by('dividend_yield', ascending=False)
            .limit(limit)
            .build())


# 프리셋 레지스트리
_PRESET_REGISTRY: Dict[str, Type[BasePreset]] = {
    'value': ValueInvestingPreset,
    'growth': GrowthInvestingPreset,
    'momentum': MomentumPreset,
    'dividend': DividendPreset,
    'small_cap_value': SmallCapValuePreset,
    'quality': QualityPreset,
    'turnaround': TurnaroundPreset,
    'oversold_bounce': OversoldBouncePreset,
    'breakout': BreakoutPreset,
    'income': IncomePreset,
}


def get_preset_strategy(name: str, **kwargs) -> StockScreener:
    """
    프리셋 전략으로 스크리너 생성

    Args:
        name: 프리셋 이름
            - 'value': 가치 투자
            - 'growth': 성장 투자
            - 'momentum': 모멘텀
            - 'dividend': 배당 투자
            - 'small_cap_value': 소형 가치주
            - 'quality': 퀄리티 투자
            - 'turnaround': 턴어라운드
            - 'oversold_bounce': 과매도 반등
            - 'breakout': 돌파
            - 'income': 인컴 투자
        **kwargs: 프리셋별 추가 파라미터

    Returns:
        StockScreener: 설정된 스크리너

    Example:
        >>> from src.screening import get_preset_strategy
        >>> screener = get_preset_strategy('value', max_per=8, max_pbr=0.8)
        >>> results = screener.screen(data)
    """
    name_lower = name.lower()

    if name_lower not in _PRESET_REGISTRY:
        available = ', '.join(_PRESET_REGISTRY.keys())
        raise ValueError(f"알 수 없는 프리셋: '{name}'. 사용 가능: {available}")

    preset_class = _PRESET_REGISTRY[name_lower]
    return preset_class.create(**kwargs)


def list_preset_strategies() -> List[Dict[str, str]]:
    """
    사용 가능한 프리셋 목록 반환

    Returns:
        프리셋 정보 리스트

    Example:
        >>> from src.screening import list_preset_strategies
        >>> presets = list_preset_strategies()
        >>> for p in presets:
        ...     print(f"{p['name']}: {p['description']}")
    """
    return [
        {
            'key': key,
            'name': preset_class.name,
            'description': preset_class.description
        }
        for key, preset_class in _PRESET_REGISTRY.items()
    ]
