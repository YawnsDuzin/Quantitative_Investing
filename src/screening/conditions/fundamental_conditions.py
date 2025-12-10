"""
Fundamental Conditions
펀더멘털 조건 클래스

시가총액, PER, PBR, 배당률 등 펀더멘털 관련 조건을 정의합니다.
"""

from typing import Optional
import pandas as pd
import numpy as np

from .base_condition import BaseCondition, ThresholdCondition, RangeCondition


class MarketCapAbove(ThresholdCondition):
    """
    시가총액이 특정 값 이상인 조건

    Example:
        >>> cond = MarketCapAbove(1e12)  # 1조원
        >>> # 시가총액 1조원 이상인 종목
    """

    def __init__(self, threshold: float, column: str = 'market_cap'):
        """
        Args:
            threshold: 최소 시가총액 (원)
            column: 시가총액 컬럼명
        """
        # 읽기 쉬운 형식으로 변환
        if threshold >= 1e12:
            threshold_str = f"{threshold/1e12:.1f}조"
        elif threshold >= 1e8:
            threshold_str = f"{threshold/1e8:.0f}억"
        else:
            threshold_str = f"{threshold:,.0f}"

        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"시가총액 >= {threshold_str}",
            description=f"시가총액이 {threshold_str}원 이상"
        )


class MarketCapBelow(ThresholdCondition):
    """
    시가총액이 특정 값 이하인 조건

    Example:
        >>> cond = MarketCapBelow(1e11)  # 1000억원
        >>> # 시가총액 1000억원 이하인 종목 (소형주)
    """

    def __init__(self, threshold: float, column: str = 'market_cap'):
        """
        Args:
            threshold: 최대 시가총액 (원)
            column: 시가총액 컬럼명
        """
        if threshold >= 1e12:
            threshold_str = f"{threshold/1e12:.1f}조"
        elif threshold >= 1e8:
            threshold_str = f"{threshold/1e8:.0f}억"
        else:
            threshold_str = f"{threshold:,.0f}"

        super().__init__(
            column=column,
            threshold=threshold,
            operator='<=',
            name=f"시가총액 <= {threshold_str}",
            description=f"시가총액이 {threshold_str}원 이하"
        )


class MarketCapBetween(RangeCondition):
    """
    시가총액이 특정 범위 내인 조건

    Example:
        >>> cond = MarketCapBetween(1e11, 1e12)
        >>> # 시가총액 1000억 ~ 1조원 사이인 중형주
    """

    def __init__(
        self,
        min_cap: float,
        max_cap: float,
        column: str = 'market_cap'
    ):
        """
        Args:
            min_cap: 최소 시가총액 (원)
            max_cap: 최대 시가총액 (원)
            column: 시가총액 컬럼명
        """
        def format_cap(cap):
            if cap >= 1e12:
                return f"{cap/1e12:.1f}조"
            elif cap >= 1e8:
                return f"{cap/1e8:.0f}억"
            else:
                return f"{cap:,.0f}"

        min_str = format_cap(min_cap)
        max_str = format_cap(max_cap)

        super().__init__(
            column=column,
            min_value=min_cap,
            max_value=max_cap,
            name=f"시가총액 {min_str} ~ {max_str}",
            description=f"시가총액이 {min_str}원 ~ {max_str}원 범위"
        )


class PERAbove(ThresholdCondition):
    """
    PER이 특정 값 이상인 조건

    Example:
        >>> cond = PERAbove(15)
        >>> # PER이 15배 이상인 종목 (고평가)
    """

    def __init__(self, threshold: float, column: str = 'per'):
        """
        Args:
            threshold: 최소 PER
            column: PER 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"PER >= {threshold}",
            description=f"PER이 {threshold}배 이상"
        )


class PERBelow(ThresholdCondition):
    """
    PER이 특정 값 이하인 조건

    Example:
        >>> cond = PERBelow(10)
        >>> # PER이 10배 이하인 종목 (저평가)
    """

    def __init__(self, threshold: float, column: str = 'per'):
        """
        Args:
            threshold: 최대 PER
            column: PER 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='<=',
            name=f"PER <= {threshold}",
            description=f"PER이 {threshold}배 이하"
        )


class PERBetween(RangeCondition):
    """
    PER이 특정 범위 내인 조건

    Example:
        >>> cond = PERBetween(5, 15)
        >>> # PER이 5~15배 사이인 종목
    """

    def __init__(
        self,
        min_per: float,
        max_per: float,
        column: str = 'per'
    ):
        """
        Args:
            min_per: 최소 PER
            max_per: 최대 PER
            column: PER 컬럼명
        """
        super().__init__(
            column=column,
            min_value=min_per,
            max_value=max_per,
            name=f"PER {min_per} ~ {max_per}",
            description=f"PER이 {min_per}배 ~ {max_per}배 범위"
        )


class PERPositive(BaseCondition):
    """
    PER이 양수인 조건 (흑자 기업)

    Example:
        >>> cond = PERPositive()
        >>> # 흑자 기업만 선택
    """

    def __init__(self, column: str = 'per'):
        super().__init__(
            name="PER > 0 (흑자)",
            description="PER이 양수인 흑자 기업"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.column] > 0


class PBRAbove(ThresholdCondition):
    """
    PBR이 특정 값 이상인 조건

    Example:
        >>> cond = PBRAbove(1.0)
        >>> # PBR이 1.0배 이상인 종목
    """

    def __init__(self, threshold: float, column: str = 'pbr'):
        """
        Args:
            threshold: 최소 PBR
            column: PBR 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"PBR >= {threshold}",
            description=f"PBR이 {threshold}배 이상"
        )


class PBRBelow(ThresholdCondition):
    """
    PBR이 특정 값 이하인 조건

    Example:
        >>> cond = PBRBelow(1.0)
        >>> # PBR이 1.0배 이하인 저평가 종목
    """

    def __init__(self, threshold: float, column: str = 'pbr'):
        """
        Args:
            threshold: 최대 PBR
            column: PBR 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='<=',
            name=f"PBR <= {threshold}",
            description=f"PBR이 {threshold}배 이하 (자산가치 대비 저평가)"
        )


class PBRBetween(RangeCondition):
    """
    PBR이 특정 범위 내인 조건

    Example:
        >>> cond = PBRBetween(0.5, 1.5)
        >>> # PBR이 0.5~1.5배 사이인 종목
    """

    def __init__(
        self,
        min_pbr: float,
        max_pbr: float,
        column: str = 'pbr'
    ):
        """
        Args:
            min_pbr: 최소 PBR
            max_pbr: 최대 PBR
            column: PBR 컬럼명
        """
        super().__init__(
            column=column,
            min_value=min_pbr,
            max_value=max_pbr,
            name=f"PBR {min_pbr} ~ {max_pbr}",
            description=f"PBR이 {min_pbr}배 ~ {max_pbr}배 범위"
        )


class DividendYieldAbove(ThresholdCondition):
    """
    배당수익률이 특정 값 이상인 조건

    Example:
        >>> cond = DividendYieldAbove(3.0)
        >>> # 배당수익률 3% 이상인 고배당주
    """

    def __init__(self, threshold: float, column: str = 'dividend_yield'):
        """
        Args:
            threshold: 최소 배당수익률 (%)
            column: 배당수익률 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"배당수익률 >= {threshold}%",
            description=f"배당수익률이 {threshold}% 이상"
        )


class DividendYieldBetween(RangeCondition):
    """
    배당수익률이 특정 범위 내인 조건

    Example:
        >>> cond = DividendYieldBetween(2.0, 5.0)
        >>> # 배당수익률 2~5% 사이인 종목
    """

    def __init__(
        self,
        min_yield: float,
        max_yield: float,
        column: str = 'dividend_yield'
    ):
        """
        Args:
            min_yield: 최소 배당수익률 (%)
            max_yield: 최대 배당수익률 (%)
            column: 배당수익률 컬럼명
        """
        super().__init__(
            column=column,
            min_value=min_yield,
            max_value=max_yield,
            name=f"배당수익률 {min_yield}% ~ {max_yield}%",
            description=f"배당수익률이 {min_yield}% ~ {max_yield}% 범위"
        )


class ROEAbove(ThresholdCondition):
    """
    ROE가 특정 값 이상인 조건

    Example:
        >>> cond = ROEAbove(15)
        >>> # ROE 15% 이상인 고수익 기업
    """

    def __init__(self, threshold: float, column: str = 'roe'):
        """
        Args:
            threshold: 최소 ROE (%)
            column: ROE 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"ROE >= {threshold}%",
            description=f"자기자본이익률이 {threshold}% 이상"
        )


class ROEBetween(RangeCondition):
    """
    ROE가 특정 범위 내인 조건

    Example:
        >>> cond = ROEBetween(10, 30)
        >>> # ROE 10~30% 사이인 종목
    """

    def __init__(
        self,
        min_roe: float,
        max_roe: float,
        column: str = 'roe'
    ):
        """
        Args:
            min_roe: 최소 ROE (%)
            max_roe: 최대 ROE (%)
            column: ROE 컬럼명
        """
        super().__init__(
            column=column,
            min_value=min_roe,
            max_value=max_roe,
            name=f"ROE {min_roe}% ~ {max_roe}%",
            description=f"ROE가 {min_roe}% ~ {max_roe}% 범위"
        )


class ROAAbove(ThresholdCondition):
    """
    ROA가 특정 값 이상인 조건

    Example:
        >>> cond = ROAAbove(5)
        >>> # ROA 5% 이상인 기업
    """

    def __init__(self, threshold: float, column: str = 'roa'):
        """
        Args:
            threshold: 최소 ROA (%)
            column: ROA 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"ROA >= {threshold}%",
            description=f"총자산이익률이 {threshold}% 이상"
        )


class DebtRatioBelow(ThresholdCondition):
    """
    부채비율이 특정 값 이하인 조건

    Example:
        >>> cond = DebtRatioBelow(100)
        >>> # 부채비율 100% 이하인 재무건전 기업
    """

    def __init__(self, threshold: float, column: str = 'debt_ratio'):
        """
        Args:
            threshold: 최대 부채비율 (%)
            column: 부채비율 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='<=',
            name=f"부채비율 <= {threshold}%",
            description=f"부채비율이 {threshold}% 이하 (재무 안정)"
        )


class DebtRatioBetween(RangeCondition):
    """
    부채비율이 특정 범위 내인 조건

    Example:
        >>> cond = DebtRatioBetween(50, 150)
        >>> # 부채비율 50~150% 사이인 종목
    """

    def __init__(
        self,
        min_ratio: float,
        max_ratio: float,
        column: str = 'debt_ratio'
    ):
        """
        Args:
            min_ratio: 최소 부채비율 (%)
            max_ratio: 최대 부채비율 (%)
            column: 부채비율 컬럼명
        """
        super().__init__(
            column=column,
            min_value=min_ratio,
            max_value=max_ratio,
            name=f"부채비율 {min_ratio}% ~ {max_ratio}%",
            description=f"부채비율이 {min_ratio}% ~ {max_ratio}% 범위"
        )


class CurrentRatioAbove(ThresholdCondition):
    """
    유동비율이 특정 값 이상인 조건

    Example:
        >>> cond = CurrentRatioAbove(150)
        >>> # 유동비율 150% 이상인 기업 (단기 지급 능력 양호)
    """

    def __init__(self, threshold: float, column: str = 'current_ratio'):
        """
        Args:
            threshold: 최소 유동비율 (%)
            column: 유동비율 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"유동비율 >= {threshold}%",
            description=f"유동비율이 {threshold}% 이상 (단기 지급 능력 양호)"
        )


class EPSGrowthAbove(ThresholdCondition):
    """
    EPS 성장률이 특정 값 이상인 조건

    Example:
        >>> cond = EPSGrowthAbove(20)
        >>> # EPS 성장률 20% 이상인 고성장 기업
    """

    def __init__(self, threshold: float, column: str = 'eps_growth'):
        """
        Args:
            threshold: 최소 EPS 성장률 (%)
            column: EPS 성장률 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"EPS 성장률 >= {threshold}%",
            description=f"주당순이익 성장률이 {threshold}% 이상"
        )


class EPSGrowthBetween(RangeCondition):
    """
    EPS 성장률이 특정 범위 내인 조건

    Example:
        >>> cond = EPSGrowthBetween(10, 50)
        >>> # EPS 성장률 10~50% 사이인 종목
    """

    def __init__(
        self,
        min_growth: float,
        max_growth: float,
        column: str = 'eps_growth'
    ):
        """
        Args:
            min_growth: 최소 EPS 성장률 (%)
            max_growth: 최대 EPS 성장률 (%)
            column: EPS 성장률 컬럼명
        """
        super().__init__(
            column=column,
            min_value=min_growth,
            max_value=max_growth,
            name=f"EPS 성장률 {min_growth}% ~ {max_growth}%",
            description=f"EPS 성장률이 {min_growth}% ~ {max_growth}% 범위"
        )


class RevenueGrowthAbove(ThresholdCondition):
    """
    매출 성장률이 특정 값 이상인 조건

    Example:
        >>> cond = RevenueGrowthAbove(15)
        >>> # 매출 성장률 15% 이상인 기업
    """

    def __init__(self, threshold: float, column: str = 'revenue_growth'):
        """
        Args:
            threshold: 최소 매출 성장률 (%)
            column: 매출 성장률 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"매출 성장률 >= {threshold}%",
            description=f"매출액 성장률이 {threshold}% 이상"
        )


class RevenueGrowthBetween(RangeCondition):
    """
    매출 성장률이 특정 범위 내인 조건

    Example:
        >>> cond = RevenueGrowthBetween(5, 30)
        >>> # 매출 성장률 5~30% 사이인 종목
    """

    def __init__(
        self,
        min_growth: float,
        max_growth: float,
        column: str = 'revenue_growth'
    ):
        """
        Args:
            min_growth: 최소 매출 성장률 (%)
            max_growth: 최대 매출 성장률 (%)
            column: 매출 성장률 컬럼명
        """
        super().__init__(
            column=column,
            min_value=min_growth,
            max_value=max_growth,
            name=f"매출 성장률 {min_growth}% ~ {max_growth}%",
            description=f"매출 성장률이 {min_growth}% ~ {max_growth}% 범위"
        )


class OperatingMarginAbove(ThresholdCondition):
    """
    영업이익률이 특정 값 이상인 조건

    Example:
        >>> cond = OperatingMarginAbove(10)
        >>> # 영업이익률 10% 이상인 기업
    """

    def __init__(self, threshold: float, column: str = 'operating_margin'):
        """
        Args:
            threshold: 최소 영업이익률 (%)
            column: 영업이익률 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"영업이익률 >= {threshold}%",
            description=f"영업이익률이 {threshold}% 이상"
        )


class NetProfitMarginAbove(ThresholdCondition):
    """
    순이익률이 특정 값 이상인 조건

    Example:
        >>> cond = NetProfitMarginAbove(5)
        >>> # 순이익률 5% 이상인 기업
    """

    def __init__(self, threshold: float, column: str = 'net_profit_margin'):
        """
        Args:
            threshold: 최소 순이익률 (%)
            column: 순이익률 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"순이익률 >= {threshold}%",
            description=f"순이익률이 {threshold}% 이상"
        )


class PSRBelow(ThresholdCondition):
    """
    PSR(주가매출비율)이 특정 값 이하인 조건

    Example:
        >>> cond = PSRBelow(2.0)
        >>> # PSR 2.0배 이하인 저평가 종목
    """

    def __init__(self, threshold: float, column: str = 'psr'):
        """
        Args:
            threshold: 최대 PSR
            column: PSR 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='<=',
            name=f"PSR <= {threshold}",
            description=f"주가매출비율이 {threshold}배 이하"
        )


class EVtoEBITDABelow(ThresholdCondition):
    """
    EV/EBITDA가 특정 값 이하인 조건

    Example:
        >>> cond = EVtoEBITDABelow(10)
        >>> # EV/EBITDA 10배 이하인 저평가 종목
    """

    def __init__(self, threshold: float, column: str = 'ev_ebitda'):
        """
        Args:
            threshold: 최대 EV/EBITDA
            column: EV/EBITDA 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='<=',
            name=f"EV/EBITDA <= {threshold}",
            description=f"EV/EBITDA가 {threshold}배 이하 (기업가치 대비 저평가)"
        )


class PEGRatioBelow(ThresholdCondition):
    """
    PEG 비율이 특정 값 이하인 조건

    Example:
        >>> cond = PEGRatioBelow(1.0)
        >>> # PEG 1.0 이하인 성장 대비 저평가 종목
    """

    def __init__(self, threshold: float = 1.0, column: str = 'peg_ratio'):
        """
        Args:
            threshold: 최대 PEG 비율 (기본: 1.0)
            column: PEG 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='<=',
            name=f"PEG <= {threshold}",
            description=f"PEG 비율이 {threshold} 이하 (성장성 대비 저평가)"
        )


class FreeCashFlowPositive(BaseCondition):
    """
    잉여현금흐름이 양수인 조건

    Example:
        >>> cond = FreeCashFlowPositive()
        >>> # 잉여현금흐름이 양수인 기업
    """

    def __init__(self, column: str = 'free_cash_flow'):
        super().__init__(
            name="FCF > 0",
            description="잉여현금흐름이 양수"
        )
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.column] > 0
