"""
Stock Screener
주식 스크리너

다양한 조건을 조합하여 종목을 필터링하는 메인 클래스입니다.
"""

from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
import pandas as pd
import numpy as np
import json

from .conditions.base_condition import BaseCondition, AndCondition


class StockScreener:
    """
    주식 스크리너

    여러 조건을 조합하여 종목을 필터링합니다.

    Example:
        >>> from src.screening import StockScreener, PriceAbove, RSIOversold

        >>> # 스크리너 생성
        >>> screener = StockScreener()

        >>> # 조건 추가
        >>> screener.add_condition(PriceAbove(10000))
        >>> screener.add_condition(RSIOversold(30))

        >>> # 스크리닝 실행
        >>> results = screener.screen(data)
    """

    def __init__(self, name: str = "Custom Screener"):
        """
        Args:
            name: 스크리너 이름
        """
        self.name = name
        self._conditions: List[BaseCondition] = []
        self._sort_by: Optional[str] = None
        self._sort_ascending: bool = True
        self._limit: Optional[int] = None
        self._created_at = datetime.now()

    @property
    def conditions(self) -> List[BaseCondition]:
        """등록된 조건 목록"""
        return self._conditions.copy()

    @property
    def required_columns(self) -> List[str]:
        """모든 조건에 필요한 컬럼 목록"""
        columns = set()
        for condition in self._conditions:
            columns.update(condition.required_columns)
        return list(columns)

    def add_condition(self, condition: BaseCondition) -> 'StockScreener':
        """
        조건 추가

        Args:
            condition: 추가할 조건

        Returns:
            self (체이닝 지원)
        """
        self._conditions.append(condition)
        return self

    def add_conditions(self, *conditions: BaseCondition) -> 'StockScreener':
        """
        여러 조건 추가

        Args:
            *conditions: 추가할 조건들

        Returns:
            self (체이닝 지원)
        """
        for condition in conditions:
            self._conditions.append(condition)
        return self

    def remove_condition(self, index: int) -> 'StockScreener':
        """
        조건 제거

        Args:
            index: 제거할 조건의 인덱스

        Returns:
            self (체이닝 지원)
        """
        if 0 <= index < len(self._conditions):
            self._conditions.pop(index)
        return self

    def clear_conditions(self) -> 'StockScreener':
        """
        모든 조건 제거

        Returns:
            self (체이닝 지원)
        """
        self._conditions.clear()
        return self

    def set_sort(
        self,
        column: str,
        ascending: bool = True
    ) -> 'StockScreener':
        """
        정렬 설정

        Args:
            column: 정렬할 컬럼
            ascending: 오름차순 여부 (기본: True)

        Returns:
            self (체이닝 지원)
        """
        self._sort_by = column
        self._sort_ascending = ascending
        return self

    def set_limit(self, limit: int) -> 'StockScreener':
        """
        결과 개수 제한 설정

        Args:
            limit: 최대 결과 개수

        Returns:
            self (체이닝 지원)
        """
        self._limit = limit
        return self

    def screen(
        self,
        data: pd.DataFrame,
        return_mask: bool = False
    ) -> Union[pd.DataFrame, pd.Series]:
        """
        스크리닝 실행

        Args:
            data: 스크리닝할 데이터
            return_mask: True이면 boolean mask 반환, False이면 필터링된 데이터 반환

        Returns:
            필터링된 데이터프레임 또는 boolean Series
        """
        if data.empty:
            return pd.Series(dtype=bool) if return_mask else data

        if not self._conditions:
            mask = pd.Series([True] * len(data), index=data.index)
        else:
            # 모든 조건을 AND로 결합
            combined = self._conditions[0]
            for condition in self._conditions[1:]:
                combined = combined & condition

            mask = combined.evaluate(data)

        if return_mask:
            return mask

        # 필터링
        result = data[mask].copy()

        # 정렬
        if self._sort_by and self._sort_by in result.columns:
            result = result.sort_values(
                self._sort_by,
                ascending=self._sort_ascending
            )

        # 개수 제한
        if self._limit:
            result = result.head(self._limit)

        return result

    def get_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        스크리닝 통계 정보 반환

        Args:
            data: 원본 데이터

        Returns:
            통계 딕셔너리
        """
        mask = self.screen(data, return_mask=True)
        total = len(data)
        passed = mask.sum()

        stats = {
            'total_stocks': total,
            'passed_stocks': int(passed),
            'filtered_out': total - int(passed),
            'pass_rate': passed / total * 100 if total > 0 else 0,
            'conditions_count': len(self._conditions),
            'conditions': [str(c) for c in self._conditions]
        }

        # 각 조건별 통과율
        condition_stats = []
        for condition in self._conditions:
            try:
                cond_mask = condition.evaluate(data)
                condition_stats.append({
                    'name': condition.name,
                    'passed': int(cond_mask.sum()),
                    'pass_rate': cond_mask.sum() / total * 100 if total > 0 else 0
                })
            except Exception as e:
                condition_stats.append({
                    'name': condition.name,
                    'error': str(e)
                })

        stats['condition_stats'] = condition_stats

        return stats

    def to_dict(self) -> Dict[str, Any]:
        """스크리너를 딕셔너리로 변환"""
        return {
            'name': self.name,
            'conditions': [c.to_dict() for c in self._conditions],
            'sort_by': self._sort_by,
            'sort_ascending': self._sort_ascending,
            'limit': self._limit,
            'created_at': self._created_at.isoformat()
        }

    def to_json(self) -> str:
        """스크리너를 JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def __repr__(self) -> str:
        return f"StockScreener(name='{self.name}', conditions={len(self._conditions)})"

    def __str__(self) -> str:
        lines = [f"스크리너: {self.name}", f"조건 수: {len(self._conditions)}"]
        for i, condition in enumerate(self._conditions, 1):
            lines.append(f"  {i}. {condition}")
        return '\n'.join(lines)


class ScreenerBuilder:
    """
    스크리너 빌더 (Fluent API)

    체이닝 방식으로 스크리너를 구성할 수 있습니다.

    Example:
        >>> from src.screening import ScreenerBuilder

        >>> screener = (ScreenerBuilder("가치주 스크리너")
        ...     .price_above(5000)
        ...     .per_below(15)
        ...     .pbr_below(1.0)
        ...     .roe_above(10)
        ...     .market_cap_above(1e11)
        ...     .exclude_administrative()
        ...     .sort_by('per', ascending=True)
        ...     .limit(20)
        ...     .build())
        ...
        >>> results = screener.screen(data)
    """

    def __init__(self, name: str = "Custom Screener"):
        """
        Args:
            name: 스크리너 이름
        """
        self._screener = StockScreener(name)

    # ===== 가격 조건 =====

    def price_above(self, threshold: float) -> 'ScreenerBuilder':
        """주가가 특정 값 이상"""
        from .conditions.price_conditions import PriceAbove
        self._screener.add_condition(PriceAbove(threshold))
        return self

    def price_below(self, threshold: float) -> 'ScreenerBuilder':
        """주가가 특정 값 이하"""
        from .conditions.price_conditions import PriceBelow
        self._screener.add_condition(PriceBelow(threshold))
        return self

    def price_between(self, min_price: float, max_price: float) -> 'ScreenerBuilder':
        """주가가 특정 범위"""
        from .conditions.price_conditions import PriceBetween
        self._screener.add_condition(PriceBetween(min_price, max_price))
        return self

    def price_change_above(self, percent: float) -> 'ScreenerBuilder':
        """일간 변동률이 특정 값 이상"""
        from .conditions.price_conditions import PriceChangePercent
        self._screener.add_condition(PriceChangePercent(min_change=percent))
        return self

    def price_change_below(self, percent: float) -> 'ScreenerBuilder':
        """일간 변동률이 특정 값 이하"""
        from .conditions.price_conditions import PriceChangePercent
        self._screener.add_condition(PriceChangePercent(max_change=percent))
        return self

    def above_52week_high(self) -> 'ScreenerBuilder':
        """52주 신고가 돌파"""
        from .conditions.price_conditions import Above52WeekHigh
        self._screener.add_condition(Above52WeekHigh())
        return self

    def below_52week_low(self) -> 'ScreenerBuilder':
        """52주 신저가 하회"""
        from .conditions.price_conditions import Below52WeekLow
        self._screener.add_condition(Below52WeekLow())
        return self

    def volume_above(self, threshold: float) -> 'ScreenerBuilder':
        """거래량이 특정 값 이상"""
        from .conditions.price_conditions import VolumeAbove
        self._screener.add_condition(VolumeAbove(threshold))
        return self

    def volume_ratio_above(self, ratio: float) -> 'ScreenerBuilder':
        """거래량 비율이 특정 값 이상"""
        from .conditions.price_conditions import VolumeRatio
        self._screener.add_condition(VolumeRatio(min_ratio=ratio))
        return self

    # ===== 기술적 지표 조건 =====

    def price_above_sma(self, period: int) -> 'ScreenerBuilder':
        """주가가 SMA 위"""
        from .conditions.technical_conditions import PriceAboveSMA
        self._screener.add_condition(PriceAboveSMA(period))
        return self

    def price_below_sma(self, period: int) -> 'ScreenerBuilder':
        """주가가 SMA 아래"""
        from .conditions.technical_conditions import PriceBelowSMA
        self._screener.add_condition(PriceBelowSMA(period))
        return self

    def golden_cross(
        self,
        short_period: int = 50,
        long_period: int = 200
    ) -> 'ScreenerBuilder':
        """골든크로스"""
        from .conditions.technical_conditions import GoldenCross
        self._screener.add_condition(GoldenCross(short_period, long_period))
        return self

    def death_cross(
        self,
        short_period: int = 50,
        long_period: int = 200
    ) -> 'ScreenerBuilder':
        """데드크로스"""
        from .conditions.technical_conditions import DeathCross
        self._screener.add_condition(DeathCross(short_period, long_period))
        return self

    def rsi_above(self, threshold: float) -> 'ScreenerBuilder':
        """RSI가 특정 값 이상"""
        from .conditions.technical_conditions import RSIOverbought
        self._screener.add_condition(RSIOverbought(threshold))
        return self

    def rsi_below(self, threshold: float) -> 'ScreenerBuilder':
        """RSI가 특정 값 이하"""
        from .conditions.technical_conditions import RSIOversold
        self._screener.add_condition(RSIOversold(threshold))
        return self

    def rsi_between(self, min_val: float, max_val: float) -> 'ScreenerBuilder':
        """RSI가 특정 범위"""
        from .conditions.technical_conditions import RSICondition
        self._screener.add_condition(RSICondition(min_value=min_val, max_value=max_val))
        return self

    def macd_bullish(self) -> 'ScreenerBuilder':
        """MACD > Signal"""
        from .conditions.technical_conditions import MACDCondition
        self._screener.add_condition(MACDCondition(signal='bullish'))
        return self

    def macd_bearish(self) -> 'ScreenerBuilder':
        """MACD < Signal"""
        from .conditions.technical_conditions import MACDCondition
        self._screener.add_condition(MACDCondition(signal='bearish'))
        return self

    def bollinger_below_lower(self) -> 'ScreenerBuilder':
        """볼린저밴드 하단 이탈"""
        from .conditions.technical_conditions import BollingerBandCondition
        self._screener.add_condition(BollingerBandCondition(position='below_lower'))
        return self

    def bollinger_above_upper(self) -> 'ScreenerBuilder':
        """볼린저밴드 상단 돌파"""
        from .conditions.technical_conditions import BollingerBandCondition
        self._screener.add_condition(BollingerBandCondition(position='above_upper'))
        return self

    def adx_above(self, threshold: float = 25) -> 'ScreenerBuilder':
        """ADX가 특정 값 이상 (강한 추세)"""
        from .conditions.technical_conditions import ADXCondition
        self._screener.add_condition(ADXCondition(min_value=threshold))
        return self

    # ===== 펀더멘털 조건 =====

    def market_cap_above(self, threshold: float) -> 'ScreenerBuilder':
        """시가총액이 특정 값 이상"""
        from .conditions.fundamental_conditions import MarketCapAbove
        self._screener.add_condition(MarketCapAbove(threshold))
        return self

    def market_cap_below(self, threshold: float) -> 'ScreenerBuilder':
        """시가총액이 특정 값 이하"""
        from .conditions.fundamental_conditions import MarketCapBelow
        self._screener.add_condition(MarketCapBelow(threshold))
        return self

    def market_cap_between(
        self,
        min_cap: float,
        max_cap: float
    ) -> 'ScreenerBuilder':
        """시가총액이 특정 범위"""
        from .conditions.fundamental_conditions import MarketCapBetween
        self._screener.add_condition(MarketCapBetween(min_cap, max_cap))
        return self

    def per_above(self, threshold: float) -> 'ScreenerBuilder':
        """PER이 특정 값 이상"""
        from .conditions.fundamental_conditions import PERAbove
        self._screener.add_condition(PERAbove(threshold))
        return self

    def per_below(self, threshold: float) -> 'ScreenerBuilder':
        """PER이 특정 값 이하"""
        from .conditions.fundamental_conditions import PERBelow
        self._screener.add_condition(PERBelow(threshold))
        return self

    def per_between(self, min_per: float, max_per: float) -> 'ScreenerBuilder':
        """PER이 특정 범위"""
        from .conditions.fundamental_conditions import PERBetween
        self._screener.add_condition(PERBetween(min_per, max_per))
        return self

    def pbr_above(self, threshold: float) -> 'ScreenerBuilder':
        """PBR이 특정 값 이상"""
        from .conditions.fundamental_conditions import PBRAbove
        self._screener.add_condition(PBRAbove(threshold))
        return self

    def pbr_below(self, threshold: float) -> 'ScreenerBuilder':
        """PBR이 특정 값 이하"""
        from .conditions.fundamental_conditions import PBRBelow
        self._screener.add_condition(PBRBelow(threshold))
        return self

    def pbr_between(self, min_pbr: float, max_pbr: float) -> 'ScreenerBuilder':
        """PBR이 특정 범위"""
        from .conditions.fundamental_conditions import PBRBetween
        self._screener.add_condition(PBRBetween(min_pbr, max_pbr))
        return self

    def dividend_yield_above(self, threshold: float) -> 'ScreenerBuilder':
        """배당수익률이 특정 값 이상"""
        from .conditions.fundamental_conditions import DividendYieldAbove
        self._screener.add_condition(DividendYieldAbove(threshold))
        return self

    def roe_above(self, threshold: float) -> 'ScreenerBuilder':
        """ROE가 특정 값 이상"""
        from .conditions.fundamental_conditions import ROEAbove
        self._screener.add_condition(ROEAbove(threshold))
        return self

    def roa_above(self, threshold: float) -> 'ScreenerBuilder':
        """ROA가 특정 값 이상"""
        from .conditions.fundamental_conditions import ROAAbove
        self._screener.add_condition(ROAAbove(threshold))
        return self

    def debt_ratio_below(self, threshold: float) -> 'ScreenerBuilder':
        """부채비율이 특정 값 이하"""
        from .conditions.fundamental_conditions import DebtRatioBelow
        self._screener.add_condition(DebtRatioBelow(threshold))
        return self

    def eps_growth_above(self, threshold: float) -> 'ScreenerBuilder':
        """EPS 성장률이 특정 값 이상"""
        from .conditions.fundamental_conditions import EPSGrowthAbove
        self._screener.add_condition(EPSGrowthAbove(threshold))
        return self

    def revenue_growth_above(self, threshold: float) -> 'ScreenerBuilder':
        """매출 성장률이 특정 값 이상"""
        from .conditions.fundamental_conditions import RevenueGrowthAbove
        self._screener.add_condition(RevenueGrowthAbove(threshold))
        return self

    # ===== 시장/분류 조건 =====

    def market_is(self, market: Union[str, List[str]]) -> 'ScreenerBuilder':
        """특정 시장 종목"""
        from .conditions.market_conditions import MarketIs
        self._screener.add_condition(MarketIs(market))
        return self

    def sector_is(self, sector: Union[str, List[str]]) -> 'ScreenerBuilder':
        """특정 섹터 종목"""
        from .conditions.market_conditions import SectorIs
        self._screener.add_condition(SectorIs(sector))
        return self

    def industry_is(self, industry: Union[str, List[str]]) -> 'ScreenerBuilder':
        """특정 업종 종목"""
        from .conditions.market_conditions import IndustryIs
        self._screener.add_condition(IndustryIs(industry))
        return self

    def exclude_administrative(self) -> 'ScreenerBuilder':
        """관리종목 제외"""
        from .conditions.market_conditions import ExcludeAdministrative
        self._screener.add_condition(ExcludeAdministrative())
        return self

    def exclude_trading_halt(self) -> 'ScreenerBuilder':
        """거래정지 종목 제외"""
        from .conditions.market_conditions import ExcludeTradingHalt
        self._screener.add_condition(ExcludeTradingHalt())
        return self

    def exclude_etf(self) -> 'ScreenerBuilder':
        """ETF 제외"""
        from .conditions.market_conditions import ExcludeETF
        self._screener.add_condition(ExcludeETF())
        return self

    def only_etf(self) -> 'ScreenerBuilder':
        """ETF만"""
        from .conditions.market_conditions import OnlyETF
        self._screener.add_condition(OnlyETF())
        return self

    # ===== 커스텀 조건 =====

    def custom(self, condition: BaseCondition) -> 'ScreenerBuilder':
        """커스텀 조건 추가"""
        self._screener.add_condition(condition)
        return self

    def custom_func(
        self,
        name: str,
        func: Callable[[pd.DataFrame], pd.Series],
        required_columns: Optional[List[str]] = None
    ) -> 'ScreenerBuilder':
        """커스텀 함수 조건 추가"""
        from .conditions.base_condition import CustomCondition
        self._screener.add_condition(
            CustomCondition(name, func, required_columns)
        )
        return self

    # ===== 정렬 및 제한 =====

    def sort_by(self, column: str, ascending: bool = True) -> 'ScreenerBuilder':
        """정렬 설정"""
        self._screener.set_sort(column, ascending)
        return self

    def limit(self, n: int) -> 'ScreenerBuilder':
        """결과 개수 제한"""
        self._screener.set_limit(n)
        return self

    # ===== 빌드 =====

    def build(self) -> StockScreener:
        """스크리너 생성"""
        return self._screener

    def screen(self, data: pd.DataFrame) -> pd.DataFrame:
        """스크리닝 실행 (빌드 없이 바로 실행)"""
        return self._screener.screen(data)


def create_screener(name: str = "Custom Screener") -> ScreenerBuilder:
    """
    스크리너 빌더 생성 (단축 함수)

    Example:
        >>> from src.screening import create_screener
        >>> results = (create_screener("가치주")
        ...     .per_below(10)
        ...     .pbr_below(1.0)
        ...     .screen(data))
    """
    return ScreenerBuilder(name)
