"""
Price Conditions
가격 관련 조건 클래스

주가, 거래량 등 가격 관련 조건을 정의합니다.
"""

from typing import Optional
import pandas as pd
import numpy as np

from .base_condition import BaseCondition, ThresholdCondition, RangeCondition


class PriceAbove(ThresholdCondition):
    """
    주가가 특정 값 이상인 조건

    Example:
        >>> cond = PriceAbove(10000)
        >>> # 주가가 10,000원 이상인 종목
    """

    def __init__(self, threshold: float, column: str = 'close'):
        """
        Args:
            threshold: 최소 주가
            column: 가격 컬럼명 (기본: 'close')
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"주가 >= {threshold:,}",
            description=f"주가가 {threshold:,}원 이상"
        )


class PriceBelow(ThresholdCondition):
    """
    주가가 특정 값 이하인 조건

    Example:
        >>> cond = PriceBelow(50000)
        >>> # 주가가 50,000원 이하인 종목
    """

    def __init__(self, threshold: float, column: str = 'close'):
        """
        Args:
            threshold: 최대 주가
            column: 가격 컬럼명 (기본: 'close')
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='<=',
            name=f"주가 <= {threshold:,}",
            description=f"주가가 {threshold:,}원 이하"
        )


class PriceBetween(RangeCondition):
    """
    주가가 특정 범위 내에 있는 조건

    Example:
        >>> cond = PriceBetween(10000, 50000)
        >>> # 주가가 10,000원 ~ 50,000원 사이인 종목
    """

    def __init__(
        self,
        min_price: float,
        max_price: float,
        column: str = 'close'
    ):
        """
        Args:
            min_price: 최소 주가
            max_price: 최대 주가
            column: 가격 컬럼명 (기본: 'close')
        """
        super().__init__(
            column=column,
            min_value=min_price,
            max_value=max_price,
            name=f"주가 {min_price:,} ~ {max_price:,}",
            description=f"주가가 {min_price:,}원 ~ {max_price:,}원 범위"
        )


class PriceChangePercent(BaseCondition):
    """
    일간 가격 변동률 조건

    Example:
        >>> cond = PriceChangePercent(min_change=3.0)
        >>> # 당일 3% 이상 상승한 종목

        >>> cond = PriceChangePercent(max_change=-3.0)
        >>> # 당일 3% 이상 하락한 종목
    """

    def __init__(
        self,
        min_change: Optional[float] = None,
        max_change: Optional[float] = None,
        column: str = 'change_pct'
    ):
        """
        Args:
            min_change: 최소 변동률 (%)
            max_change: 최대 변동률 (%)
            column: 변동률 컬럼명 (기본: 'change_pct')
        """
        if min_change is not None and max_change is not None:
            name = f"변동률 {min_change}% ~ {max_change}%"
            desc = f"일간 변동률이 {min_change}% ~ {max_change}% 범위"
        elif min_change is not None:
            name = f"변동률 >= {min_change}%"
            desc = f"일간 변동률이 {min_change}% 이상"
        elif max_change is not None:
            name = f"변동률 <= {max_change}%"
            desc = f"일간 변동률이 {max_change}% 이하"
        else:
            name = "변동률"
            desc = "모든 변동률"

        super().__init__(name, desc)
        self.min_change = min_change
        self.max_change = max_change
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        values = data[self.column]
        result = pd.Series([True] * len(data), index=data.index)

        if self.min_change is not None:
            result = result & (values >= self.min_change)
        if self.max_change is not None:
            result = result & (values <= self.max_change)

        return result


class Above52WeekHigh(BaseCondition):
    """
    52주 신고가 돌파 조건

    Example:
        >>> cond = Above52WeekHigh()
        >>> # 52주 신고가를 돌파한 종목
    """

    def __init__(self, high_column: str = 'high_52w', close_column: str = 'close'):
        """
        Args:
            high_column: 52주 고가 컬럼명
            close_column: 현재가 컬럼명
        """
        super().__init__(
            name="52주 신고가",
            description="현재가가 52주 고가를 돌파"
        )
        self.high_column = high_column
        self.close_column = close_column
        self._required_columns = [high_column, close_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.close_column] >= data[self.high_column]


class Below52WeekLow(BaseCondition):
    """
    52주 신저가 하회 조건

    Example:
        >>> cond = Below52WeekLow()
        >>> # 52주 신저가를 하회한 종목
    """

    def __init__(self, low_column: str = 'low_52w', close_column: str = 'close'):
        """
        Args:
            low_column: 52주 저가 컬럼명
            close_column: 현재가 컬럼명
        """
        super().__init__(
            name="52주 신저가",
            description="현재가가 52주 저가를 하회"
        )
        self.low_column = low_column
        self.close_column = close_column
        self._required_columns = [low_column, close_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.close_column] <= data[self.low_column]


class NearHighPercent(BaseCondition):
    """
    52주 고가 대비 N% 이내 조건

    Example:
        >>> cond = NearHighPercent(percent=5)
        >>> # 52주 고가 대비 5% 이내인 종목
    """

    def __init__(
        self,
        percent: float = 5.0,
        high_column: str = 'high_52w',
        close_column: str = 'close'
    ):
        """
        Args:
            percent: 고가 대비 허용 범위 (%)
            high_column: 52주 고가 컬럼명
            close_column: 현재가 컬럼명
        """
        super().__init__(
            name=f"52주 고가 대비 {percent}% 이내",
            description=f"현재가가 52주 고가의 {100-percent}% ~ 100% 범위"
        )
        self.percent = percent
        self.high_column = high_column
        self.close_column = close_column
        self._required_columns = [high_column, close_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        high = data[self.high_column]
        close = data[self.close_column]

        # 고가 대비 현재가 비율
        ratio = (high - close) / high * 100
        return ratio <= self.percent


class NearLowPercent(BaseCondition):
    """
    52주 저가 대비 N% 이내 조건

    Example:
        >>> cond = NearLowPercent(percent=10)
        >>> # 52주 저가 대비 10% 이내인 종목
    """

    def __init__(
        self,
        percent: float = 10.0,
        low_column: str = 'low_52w',
        close_column: str = 'close'
    ):
        """
        Args:
            percent: 저가 대비 허용 범위 (%)
            low_column: 52주 저가 컬럼명
            close_column: 현재가 컬럼명
        """
        super().__init__(
            name=f"52주 저가 대비 {percent}% 이내",
            description=f"현재가가 52주 저가의 100% ~ {100+percent}% 범위"
        )
        self.percent = percent
        self.low_column = low_column
        self.close_column = close_column
        self._required_columns = [low_column, close_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        low = data[self.low_column]
        close = data[self.close_column]

        # 저가 대비 현재가 비율
        ratio = (close - low) / low * 100
        return ratio <= self.percent


class GapUp(BaseCondition):
    """
    갭상승 조건 (시가가 전일 종가보다 N% 이상 높음)

    Example:
        >>> cond = GapUp(percent=2.0)
        >>> # 2% 이상 갭상승한 종목
    """

    def __init__(
        self,
        percent: float = 1.0,
        open_column: str = 'open',
        prev_close_column: str = 'prev_close'
    ):
        """
        Args:
            percent: 최소 갭 비율 (%)
            open_column: 시가 컬럼명
            prev_close_column: 전일 종가 컬럼명
        """
        super().__init__(
            name=f"갭상승 >= {percent}%",
            description=f"시가가 전일 종가 대비 {percent}% 이상 상승"
        )
        self.percent = percent
        self.open_column = open_column
        self.prev_close_column = prev_close_column
        self._required_columns = [open_column, prev_close_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        gap_pct = (data[self.open_column] - data[self.prev_close_column]) / data[self.prev_close_column] * 100
        return gap_pct >= self.percent


class GapDown(BaseCondition):
    """
    갭하락 조건 (시가가 전일 종가보다 N% 이상 낮음)

    Example:
        >>> cond = GapDown(percent=2.0)
        >>> # 2% 이상 갭하락한 종목
    """

    def __init__(
        self,
        percent: float = 1.0,
        open_column: str = 'open',
        prev_close_column: str = 'prev_close'
    ):
        """
        Args:
            percent: 최소 갭 비율 (%)
            open_column: 시가 컬럼명
            prev_close_column: 전일 종가 컬럼명
        """
        super().__init__(
            name=f"갭하락 >= {percent}%",
            description=f"시가가 전일 종가 대비 {percent}% 이상 하락"
        )
        self.percent = percent
        self.open_column = open_column
        self.prev_close_column = prev_close_column
        self._required_columns = [open_column, prev_close_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        gap_pct = (data[self.prev_close_column] - data[self.open_column]) / data[self.prev_close_column] * 100
        return gap_pct >= self.percent


class VolumeAbove(ThresholdCondition):
    """
    거래량이 특정 값 이상인 조건

    Example:
        >>> cond = VolumeAbove(1000000)
        >>> # 거래량이 100만주 이상인 종목
    """

    def __init__(self, threshold: float, column: str = 'volume'):
        """
        Args:
            threshold: 최소 거래량
            column: 거래량 컬럼명 (기본: 'volume')
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"거래량 >= {threshold:,.0f}",
            description=f"거래량이 {threshold:,.0f}주 이상"
        )


class VolumeBelow(ThresholdCondition):
    """
    거래량이 특정 값 이하인 조건

    Example:
        >>> cond = VolumeBelow(100000)
        >>> # 거래량이 10만주 이하인 종목
    """

    def __init__(self, threshold: float, column: str = 'volume'):
        """
        Args:
            threshold: 최대 거래량
            column: 거래량 컬럼명 (기본: 'volume')
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='<=',
            name=f"거래량 <= {threshold:,.0f}",
            description=f"거래량이 {threshold:,.0f}주 이하"
        )


class VolumeRatio(BaseCondition):
    """
    거래량 비율 조건 (평균 거래량 대비)

    Example:
        >>> cond = VolumeRatio(min_ratio=2.0)
        >>> # 평균 거래량의 2배 이상인 종목
    """

    def __init__(
        self,
        min_ratio: Optional[float] = None,
        max_ratio: Optional[float] = None,
        volume_column: str = 'volume',
        avg_volume_column: str = 'avg_volume'
    ):
        """
        Args:
            min_ratio: 최소 거래량 비율
            max_ratio: 최대 거래량 비율
            volume_column: 거래량 컬럼명
            avg_volume_column: 평균 거래량 컬럼명
        """
        if min_ratio is not None and max_ratio is not None:
            name = f"거래량 비율 {min_ratio}x ~ {max_ratio}x"
        elif min_ratio is not None:
            name = f"거래량 비율 >= {min_ratio}x"
        elif max_ratio is not None:
            name = f"거래량 비율 <= {max_ratio}x"
        else:
            name = "거래량 비율"

        super().__init__(name, f"평균 거래량 대비 비율 조건")
        self.min_ratio = min_ratio
        self.max_ratio = max_ratio
        self.volume_column = volume_column
        self.avg_volume_column = avg_volume_column
        self._required_columns = [volume_column, avg_volume_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        ratio = data[self.volume_column] / data[self.avg_volume_column]
        result = pd.Series([True] * len(data), index=data.index)

        if self.min_ratio is not None:
            result = result & (ratio >= self.min_ratio)
        if self.max_ratio is not None:
            result = result & (ratio <= self.max_ratio)

        return result


class AverageVolumeAbove(ThresholdCondition):
    """
    평균 거래량이 특정 값 이상인 조건

    Example:
        >>> cond = AverageVolumeAbove(500000)
        >>> # 평균 거래량이 50만주 이상인 종목
    """

    def __init__(self, threshold: float, column: str = 'avg_volume'):
        """
        Args:
            threshold: 최소 평균 거래량
            column: 평균 거래량 컬럼명 (기본: 'avg_volume')
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"평균 거래량 >= {threshold:,.0f}",
            description=f"평균 거래량이 {threshold:,.0f}주 이상"
        )


class TradingValueAbove(ThresholdCondition):
    """
    거래대금이 특정 값 이상인 조건

    Example:
        >>> cond = TradingValueAbove(1e9)
        >>> # 거래대금이 10억원 이상인 종목
    """

    def __init__(self, threshold: float, column: str = 'trading_value'):
        """
        Args:
            threshold: 최소 거래대금 (원)
            column: 거래대금 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"거래대금 >= {threshold/1e8:.0f}억",
            description=f"거래대금이 {threshold/1e8:.0f}억원 이상"
        )


class ConsecutiveUpDays(BaseCondition):
    """
    N일 연속 상승 조건

    Example:
        >>> cond = ConsecutiveUpDays(days=3)
        >>> # 3일 연속 상승한 종목
    """

    def __init__(self, days: int = 3, column: str = 'consecutive_up'):
        """
        Args:
            days: 연속 상승 일수
            column: 연속 상승일 컬럼명
        """
        super().__init__(
            name=f"{days}일 연속 상승",
            description=f"{days}일 연속으로 주가가 상승"
        )
        self.days = days
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.column] >= self.days


class ConsecutiveDownDays(BaseCondition):
    """
    N일 연속 하락 조건

    Example:
        >>> cond = ConsecutiveDownDays(days=3)
        >>> # 3일 연속 하락한 종목
    """

    def __init__(self, days: int = 3, column: str = 'consecutive_down'):
        """
        Args:
            days: 연속 하락 일수
            column: 연속 하락일 컬럼명
        """
        super().__init__(
            name=f"{days}일 연속 하락",
            description=f"{days}일 연속으로 주가가 하락"
        )
        self.days = days
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.column] >= self.days


class PriceReturnPeriod(BaseCondition):
    """
    특정 기간 수익률 조건

    Example:
        >>> cond = PriceReturnPeriod(period='1M', min_return=10)
        >>> # 1개월 수익률이 10% 이상인 종목
    """

    def __init__(
        self,
        period: str = '1M',
        min_return: Optional[float] = None,
        max_return: Optional[float] = None
    ):
        """
        Args:
            period: 기간 ('1W', '1M', '3M', '6M', '1Y')
            min_return: 최소 수익률 (%)
            max_return: 최대 수익률 (%)
        """
        period_names = {
            '1W': '1주',
            '1M': '1개월',
            '3M': '3개월',
            '6M': '6개월',
            '1Y': '1년'
        }
        period_name = period_names.get(period, period)

        if min_return is not None and max_return is not None:
            name = f"{period_name} 수익률 {min_return}% ~ {max_return}%"
        elif min_return is not None:
            name = f"{period_name} 수익률 >= {min_return}%"
        elif max_return is not None:
            name = f"{period_name} 수익률 <= {max_return}%"
        else:
            name = f"{period_name} 수익률"

        super().__init__(name, f"{period_name} 수익률 조건")
        self.period = period
        self.min_return = min_return
        self.max_return = max_return
        self.column = f'return_{period.lower()}'
        self._required_columns = [self.column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        values = data[self.column]
        result = pd.Series([True] * len(data), index=data.index)

        if self.min_return is not None:
            result = result & (values >= self.min_return)
        if self.max_return is not None:
            result = result & (values <= self.max_return)

        return result
