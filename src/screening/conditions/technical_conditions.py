"""
Technical Indicator Conditions
기술적 지표 조건 클래스

이동평균선, RSI, MACD, 볼린저밴드 등 기술적 지표 관련 조건을 정의합니다.
"""

from typing import Optional, Literal
import pandas as pd
import numpy as np

from .base_condition import BaseCondition, ThresholdCondition, RangeCondition


class SMACondition(RangeCondition):
    """
    단순이동평균(SMA) 값 조건

    Example:
        >>> cond = SMACondition(period=20, min_value=10000)
        >>> # 20일 SMA가 10,000원 이상인 종목
    """

    def __init__(
        self,
        period: int,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ):
        """
        Args:
            period: 이동평균 기간
            min_value: 최소값
            max_value: 최대값
        """
        column = f'sma_{period}'
        super().__init__(
            column=column,
            min_value=min_value,
            max_value=max_value,
            name=f"SMA{period} 조건",
            description=f"{period}일 단순이동평균 조건"
        )
        self.period = period


class EMACondition(RangeCondition):
    """
    지수이동평균(EMA) 값 조건

    Example:
        >>> cond = EMACondition(period=12, min_value=10000)
        >>> # 12일 EMA가 10,000원 이상인 종목
    """

    def __init__(
        self,
        period: int,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ):
        """
        Args:
            period: 이동평균 기간
            min_value: 최소값
            max_value: 최대값
        """
        column = f'ema_{period}'
        super().__init__(
            column=column,
            min_value=min_value,
            max_value=max_value,
            name=f"EMA{period} 조건",
            description=f"{period}일 지수이동평균 조건"
        )
        self.period = period


class PriceAboveSMA(BaseCondition):
    """
    주가가 이동평균선 위에 있는 조건

    Example:
        >>> cond = PriceAboveSMA(period=200)
        >>> # 200일 이동평균선 위에 있는 종목
    """

    def __init__(
        self,
        period: int,
        price_column: str = 'close',
        ma_type: str = 'sma'
    ):
        """
        Args:
            period: 이동평균 기간
            price_column: 가격 컬럼명
            ma_type: 이동평균 유형 ('sma', 'ema')
        """
        ma_column = f'{ma_type}_{period}'
        super().__init__(
            name=f"주가 > {ma_type.upper()}{period}",
            description=f"주가가 {period}일 {ma_type.upper()} 위에 위치"
        )
        self.period = period
        self.price_column = price_column
        self.ma_column = ma_column
        self.ma_type = ma_type
        self._required_columns = [price_column, ma_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.price_column] > data[self.ma_column]


class PriceBelowSMA(BaseCondition):
    """
    주가가 이동평균선 아래에 있는 조건

    Example:
        >>> cond = PriceBelowSMA(period=200)
        >>> # 200일 이동평균선 아래에 있는 종목
    """

    def __init__(
        self,
        period: int,
        price_column: str = 'close',
        ma_type: str = 'sma'
    ):
        """
        Args:
            period: 이동평균 기간
            price_column: 가격 컬럼명
            ma_type: 이동평균 유형 ('sma', 'ema')
        """
        ma_column = f'{ma_type}_{period}'
        super().__init__(
            name=f"주가 < {ma_type.upper()}{period}",
            description=f"주가가 {period}일 {ma_type.upper()} 아래에 위치"
        )
        self.period = period
        self.price_column = price_column
        self.ma_column = ma_column
        self.ma_type = ma_type
        self._required_columns = [price_column, ma_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.price_column] < data[self.ma_column]


class GoldenCross(BaseCondition):
    """
    골든크로스 조건 (단기 이동평균이 장기 이동평균을 상향 돌파)

    Example:
        >>> cond = GoldenCross(short_period=50, long_period=200)
        >>> # 50일선이 200일선을 상향 돌파한 종목
    """

    def __init__(
        self,
        short_period: int = 50,
        long_period: int = 200,
        ma_type: str = 'sma',
        lookback: int = 5
    ):
        """
        Args:
            short_period: 단기 이동평균 기간
            long_period: 장기 이동평균 기간
            ma_type: 이동평균 유형 ('sma', 'ema')
            lookback: 크로스오버 확인 기간 (일)
        """
        super().__init__(
            name=f"골든크로스 ({short_period}/{long_period})",
            description=f"{short_period}일선이 {long_period}일선을 상향 돌파"
        )
        self.short_period = short_period
        self.long_period = long_period
        self.ma_type = ma_type
        self.lookback = lookback
        self.short_column = f'{ma_type}_{short_period}'
        self.long_column = f'{ma_type}_{long_period}'
        self._required_columns = [self.short_column, self.long_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)

        short_ma = data[self.short_column]
        long_ma = data[self.long_column]

        # 현재 단기 > 장기
        current_above = short_ma > long_ma

        # 골든크로스 컬럼이 있으면 사용
        if 'golden_cross' in data.columns:
            return data['golden_cross'].astype(bool)

        # 없으면 현재 상태만 반환
        return current_above


class DeathCross(BaseCondition):
    """
    데드크로스 조건 (단기 이동평균이 장기 이동평균을 하향 돌파)

    Example:
        >>> cond = DeathCross(short_period=50, long_period=200)
        >>> # 50일선이 200일선을 하향 돌파한 종목
    """

    def __init__(
        self,
        short_period: int = 50,
        long_period: int = 200,
        ma_type: str = 'sma',
        lookback: int = 5
    ):
        """
        Args:
            short_period: 단기 이동평균 기간
            long_period: 장기 이동평균 기간
            ma_type: 이동평균 유형 ('sma', 'ema')
            lookback: 크로스오버 확인 기간 (일)
        """
        super().__init__(
            name=f"데드크로스 ({short_period}/{long_period})",
            description=f"{short_period}일선이 {long_period}일선을 하향 돌파"
        )
        self.short_period = short_period
        self.long_period = long_period
        self.ma_type = ma_type
        self.lookback = lookback
        self.short_column = f'{ma_type}_{short_period}'
        self.long_column = f'{ma_type}_{long_period}'
        self._required_columns = [self.short_column, self.long_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)

        short_ma = data[self.short_column]
        long_ma = data[self.long_column]

        # 현재 단기 < 장기
        current_below = short_ma < long_ma

        # 데드크로스 컬럼이 있으면 사용
        if 'death_cross' in data.columns:
            return data['death_cross'].astype(bool)

        return current_below


class RSICondition(RangeCondition):
    """
    RSI 값 범위 조건

    Example:
        >>> cond = RSICondition(min_value=30, max_value=70)
        >>> # RSI가 30~70 범위인 종목
    """

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        period: int = 14,
        column: str = 'rsi'
    ):
        """
        Args:
            min_value: RSI 최소값 (0-100)
            max_value: RSI 최대값 (0-100)
            period: RSI 기간 (일반적으로 14)
            column: RSI 컬럼명
        """
        super().__init__(
            column=column,
            min_value=min_value,
            max_value=max_value,
            name=f"RSI 조건",
            description=f"RSI({period}) 범위 조건"
        )
        self.period = period


class RSIOverbought(ThresholdCondition):
    """
    RSI 과매수 조건

    Example:
        >>> cond = RSIOverbought(threshold=70)
        >>> # RSI가 70 이상인 과매수 종목
    """

    def __init__(self, threshold: float = 70, column: str = 'rsi'):
        """
        Args:
            threshold: 과매수 기준 (기본: 70)
            column: RSI 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='>=',
            name=f"RSI 과매수 (>= {threshold})",
            description=f"RSI가 {threshold} 이상 (과매수 상태)"
        )


class RSIOversold(ThresholdCondition):
    """
    RSI 과매도 조건

    Example:
        >>> cond = RSIOversold(threshold=30)
        >>> # RSI가 30 이하인 과매도 종목
    """

    def __init__(self, threshold: float = 30, column: str = 'rsi'):
        """
        Args:
            threshold: 과매도 기준 (기본: 30)
            column: RSI 컬럼명
        """
        super().__init__(
            column=column,
            threshold=threshold,
            operator='<=',
            name=f"RSI 과매도 (<= {threshold})",
            description=f"RSI가 {threshold} 이하 (과매도 상태)"
        )


class MACDCondition(BaseCondition):
    """
    MACD 조건

    Example:
        >>> cond = MACDCondition(signal='bullish')
        >>> # MACD가 시그널선 위에 있는 종목
    """

    def __init__(
        self,
        signal: Literal['bullish', 'bearish', 'positive', 'negative'] = 'bullish',
        macd_column: str = 'macd',
        signal_column: str = 'macd_signal'
    ):
        """
        Args:
            signal: 조건 유형
                - 'bullish': MACD > Signal (상승 신호)
                - 'bearish': MACD < Signal (하락 신호)
                - 'positive': MACD > 0 (양수)
                - 'negative': MACD < 0 (음수)
            macd_column: MACD 컬럼명
            signal_column: 시그널선 컬럼명
        """
        signal_names = {
            'bullish': 'MACD > Signal',
            'bearish': 'MACD < Signal',
            'positive': 'MACD > 0',
            'negative': 'MACD < 0'
        }

        super().__init__(
            name=f"MACD {signal_names.get(signal, signal)}",
            description=f"MACD 조건: {signal_names.get(signal, signal)}"
        )
        self.signal = signal
        self.macd_column = macd_column
        self.signal_column = signal_column

        if signal in ['bullish', 'bearish']:
            self._required_columns = [macd_column, signal_column]
        else:
            self._required_columns = [macd_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)

        macd = data[self.macd_column]

        if self.signal == 'bullish':
            return macd > data[self.signal_column]
        elif self.signal == 'bearish':
            return macd < data[self.signal_column]
        elif self.signal == 'positive':
            return macd > 0
        elif self.signal == 'negative':
            return macd < 0
        else:
            raise ValueError(f"알 수 없는 signal 유형: {self.signal}")


class MACDCrossover(BaseCondition):
    """
    MACD 크로스오버 조건

    Example:
        >>> cond = MACDCrossover(direction='bullish')
        >>> # MACD가 시그널선을 상향 돌파한 종목
    """

    def __init__(
        self,
        direction: Literal['bullish', 'bearish'] = 'bullish',
        macd_column: str = 'macd',
        signal_column: str = 'macd_signal'
    ):
        """
        Args:
            direction: 크로스오버 방향
                - 'bullish': MACD가 시그널선 상향 돌파
                - 'bearish': MACD가 시그널선 하향 돌파
            macd_column: MACD 컬럼명
            signal_column: 시그널선 컬럼명
        """
        super().__init__(
            name=f"MACD {'골든' if direction == 'bullish' else '데드'}크로스",
            description=f"MACD가 시그널선을 {'상향' if direction == 'bullish' else '하향'} 돌파"
        )
        self.direction = direction
        self.macd_column = macd_column
        self.signal_column = signal_column
        self._required_columns = [macd_column, signal_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)

        macd = data[self.macd_column]
        signal = data[self.signal_column]

        if self.direction == 'bullish':
            # MACD 골든크로스 컬럼이 있으면 사용
            if 'macd_golden_cross' in data.columns:
                return data['macd_golden_cross'].astype(bool)
            return macd > signal
        else:
            # MACD 데드크로스 컬럼이 있으면 사용
            if 'macd_death_cross' in data.columns:
                return data['macd_death_cross'].astype(bool)
            return macd < signal


class BollingerBandCondition(BaseCondition):
    """
    볼린저밴드 조건

    Example:
        >>> cond = BollingerBandCondition(position='below_lower')
        >>> # 볼린저밴드 하단 아래에 있는 종목
    """

    def __init__(
        self,
        position: Literal[
            'above_upper', 'below_upper',
            'above_middle', 'below_middle',
            'above_lower', 'below_lower'
        ] = 'below_lower',
        price_column: str = 'close',
        upper_column: str = 'bb_upper',
        middle_column: str = 'bb_middle',
        lower_column: str = 'bb_lower'
    ):
        """
        Args:
            position: 가격 위치 조건
                - 'above_upper': 상단밴드 위
                - 'below_upper': 상단밴드 아래
                - 'above_middle': 중간선 위
                - 'below_middle': 중간선 아래
                - 'above_lower': 하단밴드 위
                - 'below_lower': 하단밴드 아래
            price_column: 가격 컬럼명
            upper_column: 상단밴드 컬럼명
            middle_column: 중간선 컬럼명
            lower_column: 하단밴드 컬럼명
        """
        position_names = {
            'above_upper': '상단밴드 돌파',
            'below_upper': '상단밴드 아래',
            'above_middle': '중간선 위',
            'below_middle': '중간선 아래',
            'above_lower': '하단밴드 위',
            'below_lower': '하단밴드 이탈'
        }

        super().__init__(
            name=f"볼린저밴드 {position_names.get(position, position)}",
            description=f"볼린저밴드 조건: {position_names.get(position, position)}"
        )
        self.position = position
        self.price_column = price_column
        self.upper_column = upper_column
        self.middle_column = middle_column
        self.lower_column = lower_column

        # 필요한 컬럼 설정
        if 'upper' in position:
            self._required_columns = [price_column, upper_column]
        elif 'middle' in position:
            self._required_columns = [price_column, middle_column]
        else:
            self._required_columns = [price_column, lower_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        price = data[self.price_column]

        if self.position == 'above_upper':
            return price > data[self.upper_column]
        elif self.position == 'below_upper':
            return price < data[self.upper_column]
        elif self.position == 'above_middle':
            return price > data[self.middle_column]
        elif self.position == 'below_middle':
            return price < data[self.middle_column]
        elif self.position == 'above_lower':
            return price > data[self.lower_column]
        elif self.position == 'below_lower':
            return price < data[self.lower_column]
        else:
            raise ValueError(f"알 수 없는 position: {self.position}")


class ATRCondition(BaseCondition):
    """
    ATR (Average True Range) 조건

    Example:
        >>> cond = ATRCondition(min_value=100)
        >>> # ATR이 100 이상인 변동성 높은 종목
    """

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        column: str = 'atr'
    ):
        """
        Args:
            min_value: 최소 ATR 값
            max_value: 최대 ATR 값
            column: ATR 컬럼명
        """
        if min_value is not None and max_value is not None:
            name = f"ATR {min_value} ~ {max_value}"
        elif min_value is not None:
            name = f"ATR >= {min_value}"
        elif max_value is not None:
            name = f"ATR <= {max_value}"
        else:
            name = "ATR"

        super().__init__(name, "ATR (Average True Range) 조건")
        self.min_value = min_value
        self.max_value = max_value
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        atr = data[self.column]
        result = pd.Series([True] * len(data), index=data.index)

        if self.min_value is not None:
            result = result & (atr >= self.min_value)
        if self.max_value is not None:
            result = result & (atr <= self.max_value)

        return result


class StochasticCondition(BaseCondition):
    """
    스토캐스틱 조건

    Example:
        >>> cond = StochasticCondition(k_min=20, k_max=80)
        >>> # %K가 20~80 사이인 종목
    """

    def __init__(
        self,
        k_min: Optional[float] = None,
        k_max: Optional[float] = None,
        d_min: Optional[float] = None,
        d_max: Optional[float] = None,
        k_column: str = 'stoch_k',
        d_column: str = 'stoch_d'
    ):
        """
        Args:
            k_min: %K 최소값
            k_max: %K 최대값
            d_min: %D 최소값
            d_max: %D 최대값
            k_column: %K 컬럼명
            d_column: %D 컬럼명
        """
        super().__init__(
            name="스토캐스틱 조건",
            description="스토캐스틱 범위 조건"
        )
        self.k_min = k_min
        self.k_max = k_max
        self.d_min = d_min
        self.d_max = d_max
        self.k_column = k_column
        self.d_column = d_column

        self._required_columns = []
        if k_min is not None or k_max is not None:
            self._required_columns.append(k_column)
        if d_min is not None or d_max is not None:
            self._required_columns.append(d_column)

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        result = pd.Series([True] * len(data), index=data.index)

        if self.k_column in data.columns:
            k = data[self.k_column]
            if self.k_min is not None:
                result = result & (k >= self.k_min)
            if self.k_max is not None:
                result = result & (k <= self.k_max)

        if self.d_column in data.columns:
            d = data[self.d_column]
            if self.d_min is not None:
                result = result & (d >= self.d_min)
            if self.d_max is not None:
                result = result & (d <= self.d_max)

        return result


class StochasticOversold(BaseCondition):
    """
    스토캐스틱 과매도 조건

    Example:
        >>> cond = StochasticOversold(threshold=20)
        >>> # %K가 20 이하인 과매도 종목
    """

    def __init__(
        self,
        threshold: float = 20,
        k_column: str = 'stoch_k'
    ):
        super().__init__(
            name=f"스토캐스틱 과매도 (<= {threshold})",
            description=f"스토캐스틱 %K가 {threshold} 이하"
        )
        self.threshold = threshold
        self.k_column = k_column
        self._required_columns = [k_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.k_column] <= self.threshold


class StochasticOverbought(BaseCondition):
    """
    스토캐스틱 과매수 조건

    Example:
        >>> cond = StochasticOverbought(threshold=80)
        >>> # %K가 80 이상인 과매수 종목
    """

    def __init__(
        self,
        threshold: float = 80,
        k_column: str = 'stoch_k'
    ):
        super().__init__(
            name=f"스토캐스틱 과매수 (>= {threshold})",
            description=f"스토캐스틱 %K가 {threshold} 이상"
        )
        self.threshold = threshold
        self.k_column = k_column
        self._required_columns = [k_column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data[self.k_column] >= self.threshold


class ADXCondition(BaseCondition):
    """
    ADX (Average Directional Index) 조건

    Example:
        >>> cond = ADXCondition(min_value=25)
        >>> # ADX가 25 이상인 강한 추세 종목
    """

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        column: str = 'adx'
    ):
        """
        Args:
            min_value: 최소 ADX 값
            max_value: 최대 ADX 값
            column: ADX 컬럼명
        """
        if min_value is not None and max_value is not None:
            name = f"ADX {min_value} ~ {max_value}"
            desc = f"ADX가 {min_value} ~ {max_value} 범위"
        elif min_value is not None:
            name = f"ADX >= {min_value}"
            desc = f"ADX가 {min_value} 이상 (강한 추세)"
        elif max_value is not None:
            name = f"ADX <= {max_value}"
            desc = f"ADX가 {max_value} 이하 (약한 추세)"
        else:
            name = "ADX"
            desc = "ADX 조건"

        super().__init__(name, desc)
        self.min_value = min_value
        self.max_value = max_value
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        adx = data[self.column]
        result = pd.Series([True] * len(data), index=data.index)

        if self.min_value is not None:
            result = result & (adx >= self.min_value)
        if self.max_value is not None:
            result = result & (adx <= self.max_value)

        return result


class WilliamsRCondition(BaseCondition):
    """
    Williams %R 조건

    Example:
        >>> cond = WilliamsRCondition(min_value=-80, max_value=-20)
        >>> # Williams %R이 -80 ~ -20 범위인 종목
    """

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        column: str = 'williams_r'
    ):
        """
        Args:
            min_value: 최소값 (-100 ~ 0)
            max_value: 최대값 (-100 ~ 0)
            column: Williams %R 컬럼명
        """
        if min_value is not None and max_value is not None:
            name = f"Williams %R {min_value} ~ {max_value}"
        elif min_value is not None:
            name = f"Williams %R >= {min_value}"
        elif max_value is not None:
            name = f"Williams %R <= {max_value}"
        else:
            name = "Williams %R"

        super().__init__(name, "Williams %R 조건")
        self.min_value = min_value
        self.max_value = max_value
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        wr = data[self.column]
        result = pd.Series([True] * len(data), index=data.index)

        if self.min_value is not None:
            result = result & (wr >= self.min_value)
        if self.max_value is not None:
            result = result & (wr <= self.max_value)

        return result


class CCICondition(BaseCondition):
    """
    CCI (Commodity Channel Index) 조건

    Example:
        >>> cond = CCICondition(min_value=100)
        >>> # CCI가 100 이상인 강한 상승 추세 종목
    """

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        column: str = 'cci'
    ):
        """
        Args:
            min_value: 최소 CCI 값
            max_value: 최대 CCI 값
            column: CCI 컬럼명
        """
        if min_value is not None and max_value is not None:
            name = f"CCI {min_value} ~ {max_value}"
        elif min_value is not None:
            name = f"CCI >= {min_value}"
        elif max_value is not None:
            name = f"CCI <= {max_value}"
        else:
            name = "CCI"

        super().__init__(name, "CCI (Commodity Channel Index) 조건")
        self.min_value = min_value
        self.max_value = max_value
        self.column = column
        self._required_columns = [column]

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        cci = data[self.column]
        result = pd.Series([True] * len(data), index=data.index)

        if self.min_value is not None:
            result = result & (cci >= self.min_value)
        if self.max_value is not None:
            result = result & (cci <= self.max_value)

        return result
