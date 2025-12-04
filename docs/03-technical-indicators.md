# 03. 기술적 지표 (Technical Indicators)

주식 데이터에 기술적 분석 지표를 추가하는 방법에 대한 매뉴얼입니다.

## 목차

1. [개요](#개요)
2. [TechnicalIndicators 클래스](#technicalindicators-클래스)
3. [지표 상세 설명](#지표-상세-설명)
4. [일괄 지표 추가](#일괄-지표-추가)
5. [설정 항목](#설정-항목)
6. [예제 코드](#예제-코드)

---

## 개요

**파일 위치**: `src/data_processing/indicators.py`

기술적 지표는 가격과 거래량 데이터를 기반으로 주가의 추세, 모멘텀, 변동성 등을 분석하는 데 사용됩니다.

### 지원하는 지표 종류

| 카테고리 | 지표 |
|---------|------|
| 이동평균 | SMA, EMA |
| 모멘텀 | RSI, MACD, Momentum, ROC, Stochastic |
| 변동성 | Bollinger Bands, ATR |
| 추세 | ADX, Williams %R, CCI |
| 거래량 | OBV, VWAP |

---

## TechnicalIndicators 클래스

### 기본 사용법

```python
from src.data_processing.indicators import TechnicalIndicators

ti = TechnicalIndicators()
```

모든 메서드는 `@staticmethod`로 정의되어 있어 인스턴스 생성 없이도 사용 가능합니다:

```python
# 인스턴스 없이 직접 호출
sma = TechnicalIndicators.sma(df['close'], period=20)
```

---

## 지표 상세 설명

### 1. 이동평균 (Moving Averages)

#### SMA (Simple Moving Average) - 단순이동평균

```python
# 20일 단순이동평균
sma_20 = TechnicalIndicators.sma(df['close'], period=20)

# 50일, 200일 이동평균
sma_50 = TechnicalIndicators.sma(df['close'], period=50)
sma_200 = TechnicalIndicators.sma(df['close'], period=200)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `prices` | pd.Series | 필수 | 가격 시리즈 |
| `period` | int | 20 | 기간 |

**해석**:
- 가격 > SMA: 상승 추세
- 가격 < SMA: 하락 추세
- SMA 20 > SMA 50: 골든 크로스 (매수 신호)
- SMA 20 < SMA 50: 데드 크로스 (매도 신호)

#### EMA (Exponential Moving Average) - 지수이동평균

```python
# 12일 지수이동평균
ema_12 = TechnicalIndicators.ema(df['close'], period=12)

# 26일 지수이동평균
ema_26 = TechnicalIndicators.ema(df['close'], period=26)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `prices` | pd.Series | 필수 | 가격 시리즈 |
| `period` | int | 20 | 기간 |

**특징**: 최근 가격에 더 많은 가중치를 부여하여 SMA보다 가격 변화에 민감하게 반응

---

### 2. 모멘텀 지표 (Momentum Indicators)

#### RSI (Relative Strength Index) - 상대강도지수

```python
# 14일 RSI
rsi = TechnicalIndicators.rsi(df['close'], period=14)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `prices` | pd.Series | 필수 | 가격 시리즈 |
| `period` | int | 14 | 기간 |

**반환값**: 0-100 범위의 시리즈

**해석**:
- RSI > 70: 과매수 구간 (매도 고려)
- RSI < 30: 과매도 구간 (매수 고려)
- RSI = 50: 중립

```python
# RSI 기반 신호 생성
df['rsi_signal'] = 'neutral'
df.loc[rsi > 70, 'rsi_signal'] = 'overbought'
df.loc[rsi < 30, 'rsi_signal'] = 'oversold'
```

#### MACD (Moving Average Convergence Divergence)

```python
# MACD 계산
macd_line, signal_line, histogram = TechnicalIndicators.macd(
    df['close'],
    fast_period=12,
    slow_period=26,
    signal_period=9
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `prices` | pd.Series | 필수 | 가격 시리즈 |
| `fast_period` | int | 12 | 빠른 EMA 기간 |
| `slow_period` | int | 26 | 느린 EMA 기간 |
| `signal_period` | int | 9 | 시그널 라인 기간 |

**반환값**: Tuple (MACD Line, Signal Line, Histogram)

**해석**:
- MACD > Signal: 매수 신호
- MACD < Signal: 매도 신호
- Histogram > 0: 상승 모멘텀
- Histogram < 0: 하락 모멘텀

```python
# MACD DataFrame에 추가
df['macd'] = macd_line
df['macd_signal'] = signal_line
df['macd_hist'] = histogram
```

#### Momentum - 모멘텀

```python
# 12일 모멘텀
momentum = TechnicalIndicators.momentum(df['close'], period=12)
```

**반환값**: 현재 가격 - N일 전 가격

#### ROC (Rate of Change) - 변화율

```python
# 12일 변화율
roc = TechnicalIndicators.roc(df['close'], period=12)
```

**반환값**: 백분율 변화율 (%)

```
ROC = ((현재가격 - N일전가격) / N일전가격) × 100
```

#### Stochastic Oscillator - 스토캐스틱

```python
# 스토캐스틱 계산
stoch_k, stoch_d = TechnicalIndicators.stochastic(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    k_period=14,
    d_period=3
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `high` | pd.Series | 필수 | 고가 시리즈 |
| `low` | pd.Series | 필수 | 저가 시리즈 |
| `close` | pd.Series | 필수 | 종가 시리즈 |
| `k_period` | int | 14 | %K 기간 |
| `d_period` | int | 3 | %D 기간 |

**반환값**: Tuple (%K, %D)

**해석**:
- %K > 80: 과매수
- %K < 20: 과매도
- %K가 %D를 상향 돌파: 매수 신호
- %K가 %D를 하향 돌파: 매도 신호

---

### 3. 변동성 지표 (Volatility Indicators)

#### Bollinger Bands - 볼린저 밴드

```python
upper, middle, lower = TechnicalIndicators.bollinger_bands(
    df['close'],
    period=20,
    std_dev=2.0
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `prices` | pd.Series | 필수 | 가격 시리즈 |
| `period` | int | 20 | 이동평균 기간 |
| `std_dev` | float | 2.0 | 표준편차 배수 |

**반환값**: Tuple (상단밴드, 중간밴드, 하단밴드)

**해석**:
- 가격 > 상단밴드: 과매수 (평균 회귀 예상)
- 가격 < 하단밴드: 과매도 (평균 회귀 예상)
- 밴드폭 확대: 변동성 증가
- 밴드폭 축소: 변동성 감소

```python
# 볼린저 밴드 폭 계산
df['bb_width'] = (upper - lower) / middle * 100
```

#### ATR (Average True Range) - 평균진폭

```python
atr = TechnicalIndicators.atr(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    period=14
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `high` | pd.Series | 필수 | 고가 시리즈 |
| `low` | pd.Series | 필수 | 저가 시리즈 |
| `close` | pd.Series | 필수 | 종가 시리즈 |
| `period` | int | 14 | 기간 |

**용도**: 변동성 측정, 손절가 설정, 포지션 크기 결정

```python
# ATR 기반 손절가 설정
stop_loss_price = df['close'] - (2 * atr)  # 2 ATR 손절
```

---

### 4. 추세 지표 (Trend Indicators)

#### ADX (Average Directional Index) - 평균방향지수

```python
adx = TechnicalIndicators.adx(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    period=14
)
```

**해석**:
- ADX > 25: 강한 추세
- ADX < 20: 약한 추세 또는 횡보
- ADX 상승: 추세 강화 중
- ADX 하락: 추세 약화 중

#### Williams %R

```python
williams_r = TechnicalIndicators.williams_r(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    period=14
)
```

**반환값**: -100 ~ 0 범위

**해석**:
- %R > -20: 과매수
- %R < -80: 과매도

#### CCI (Commodity Channel Index) - 상품채널지수

```python
cci = TechnicalIndicators.cci(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    period=20,
    constant=0.015
)
```

**해석**:
- CCI > +100: 과매수 (상승 추세)
- CCI < -100: 과매도 (하락 추세)

---

### 5. 거래량 지표 (Volume Indicators)

#### OBV (On-Balance Volume) - 거래량 균형

```python
obv = TechnicalIndicators.obv(df['close'], df['volume'])
```

**용도**:
- 가격과 거래량의 관계 분석
- OBV 상승 + 가격 횡보 = 매집 신호
- OBV 하락 + 가격 횡보 = 분산 신호

#### VWAP (Volume Weighted Average Price) - 거래량가중평균가격

```python
vwap = TechnicalIndicators.vwap(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    volume=df['volume']
)
```

**용도**:
- 기관 투자자의 평균 매수가 추정
- 가격 > VWAP: 강세
- 가격 < VWAP: 약세

---

## 일괄 지표 추가

### `add_all_indicators()` 함수

모든 기술적 지표를 한번에 추가합니다.

```python
from src.data_processing.indicators import add_all_indicators

# 모든 지표 추가
df_with_indicators = add_all_indicators(
    df,
    close_col='close',
    high_col='high',
    low_col='low',
    volume_col='volume'
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `df` | DataFrame | 필수 | OHLCV 데이터 |
| `close_col` | str | 'close' | 종가 컬럼명 |
| `high_col` | str | 'high' | 고가 컬럼명 |
| `low_col` | str | 'low' | 저가 컬럼명 |
| `volume_col` | str | 'volume' | 거래량 컬럼명 |

### 추가되는 컬럼

```python
# 이동평균
'sma_20', 'sma_50', 'sma_200'
'ema_12', 'ema_26'

# RSI
'rsi'

# MACD
'macd', 'macd_signal', 'macd_hist'

# 볼린저 밴드
'bb_upper', 'bb_middle', 'bb_lower'

# ATR
'atr'

# 스토캐스틱
'stoch_k', 'stoch_d'

# 모멘텀
'momentum', 'roc'

# 거래량 지표
'obv', 'vwap'
```

---

## 설정 항목

`config/config.yaml` 파일의 `indicators` 섹션에서 지표 파라미터를 설정할 수 있습니다:

```yaml
indicators:
  # 이동평균
  sma_periods: [20, 50, 200]    # SMA 기간
  ema_periods: [12, 26]          # EMA 기간

  # RSI
  rsi_period: 14                 # RSI 기간

  # MACD
  macd_fast: 12                  # MACD 빠른 기간
  macd_slow: 26                  # MACD 느린 기간
  macd_signal: 9                 # MACD 시그널 기간

  # 볼린저 밴드
  bollinger_period: 20           # 볼린저 밴드 기간
  bollinger_std: 2               # 표준편차 배수

  # ATR
  atr_period: 14                 # ATR 기간
```

### 설정값 사용

```python
from src.utils.config_loader import get_config

config = get_config()

# 설정값 조회
rsi_period = config.get('indicators.rsi_period', 14)
macd_fast = config.get('indicators.macd_fast', 12)
```

---

## 예제 코드

### 예제 1: 기본 지표 계산

```python
import pandas as pd
from src.data_processing.indicators import TechnicalIndicators, add_all_indicators
from src.data_collection.kr_stock_collector import KoreanStockCollector

# 데이터 수집
collector = KoreanStockCollector()
df = collector.get_price_data('005930', '2023-01-01', '2024-01-01')

# 개별 지표 계산
ti = TechnicalIndicators()

df['sma_20'] = ti.sma(df['close'], 20)
df['rsi'] = ti.rsi(df['close'], 14)

macd, signal, hist = ti.macd(df['close'])
df['macd'] = macd
df['macd_signal'] = signal

print(df[['date', 'close', 'sma_20', 'rsi', 'macd']].tail())
```

### 예제 2: 모든 지표 한번에 추가

```python
from src.data_processing.indicators import add_all_indicators

# 모든 지표 추가
df_full = add_all_indicators(df)

# 추가된 컬럼 확인
new_columns = [col for col in df_full.columns if col not in df.columns]
print(f"추가된 지표: {new_columns}")

# 결과 확인
print(df_full[['date', 'close', 'sma_20', 'rsi', 'macd', 'bb_upper']].tail())
```

### 예제 3: 매매 신호 생성

```python
from src.data_processing.indicators import TechnicalIndicators

ti = TechnicalIndicators()

# 지표 계산
df['sma_20'] = ti.sma(df['close'], 20)
df['sma_50'] = ti.sma(df['close'], 50)
df['rsi'] = ti.rsi(df['close'], 14)
df['macd'], df['macd_signal'], _ = ti.macd(df['close'])

# 신호 생성
df['signal'] = 0  # 0: 보유, 1: 매수, -1: 매도

# 골든 크로스 + RSI 과매도 = 강한 매수
df.loc[
    (df['sma_20'] > df['sma_50']) &
    (df['sma_20'].shift(1) <= df['sma_50'].shift(1)) &  # 크로스
    (df['rsi'] < 40),  # RSI 낮음
    'signal'
] = 1

# 데드 크로스 + RSI 과매수 = 강한 매도
df.loc[
    (df['sma_20'] < df['sma_50']) &
    (df['sma_20'].shift(1) >= df['sma_50'].shift(1)) &  # 크로스
    (df['rsi'] > 60),  # RSI 높음
    'signal'
] = -1

# 신호 발생 날짜 확인
buy_signals = df[df['signal'] == 1]
sell_signals = df[df['signal'] == -1]

print(f"매수 신호: {len(buy_signals)}건")
print(f"매도 신호: {len(sell_signals)}건")
```

### 예제 4: 볼린저 밴드 전략

```python
upper, middle, lower = TechnicalIndicators.bollinger_bands(df['close'], 20, 2)

df['bb_upper'] = upper
df['bb_lower'] = lower

# 볼린저 밴드 하단 돌파 시 매수
df['bb_signal'] = 0
df.loc[df['close'] < df['bb_lower'], 'bb_signal'] = 1  # 매수
df.loc[df['close'] > df['bb_upper'], 'bb_signal'] = -1  # 매도

# %B 계산 (볼린저 밴드 내 위치)
df['percent_b'] = (df['close'] - lower) / (upper - lower)
```

---

## 주의사항

1. **NaN 값 처리**: 이동평균 등의 지표는 초기 기간 동안 NaN 값이 발생합니다.
   ```python
   df = df.dropna()  # NaN 제거
   # 또는
   df = df.fillna(method='ffill')  # 앞 값으로 채우기
   ```

2. **데이터 충분성**: 200일 이동평균을 계산하려면 최소 200일 이상의 데이터가 필요합니다.

3. **실시간 데이터**: 당일 지표는 장 마감 전까지 변동될 수 있습니다.

---

## 다음 단계

- [04. 팩터 분석](./04-factor-analysis.md) - 퀀트 팩터 계산
- [05. 투자 전략](./05-strategies.md) - 기술적 지표 기반 전략
