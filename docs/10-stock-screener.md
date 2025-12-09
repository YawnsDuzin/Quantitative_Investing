# 10. 종목 스크리닝 (Stock Screening)

다양한 조건을 조합하여 종목을 필터링하는 기능에 대한 매뉴얼입니다.

## 목차

1. [개요](#개요)
2. [빠른 시작](#빠른-시작)
3. [조건 클래스](#조건-클래스)
4. [조건 조합](#조건-조합)
5. [스크리너 빌더](#스크리너-빌더)
6. [프리셋 전략](#프리셋-전략)
7. [설정 항목](#설정-항목)
8. [예제 코드](#예제-코드)

---

## 개요

**파일 위치**: `src/screening/`

주식 스크리닝은 수많은 종목 중에서 특정 조건을 충족하는 종목만을 추출하는 과정입니다. 이 모듈은 가격, 기술적 지표, 펀더멘털, 시장 분류 등 다양한 조건을 조합하여 종목을 필터링할 수 있습니다.

### 주요 기능

| 기능 | 설명 |
|------|------|
| 조건 기반 필터링 | 다양한 조건 클래스를 사용한 필터링 |
| 조건 조합 | AND, OR, NOT 연산자로 조건 결합 |
| 빌더 패턴 | 체이닝 방식의 직관적인 API |
| 프리셋 전략 | 자주 사용되는 전략을 미리 정의 |
| 확장성 | 커스텀 조건 쉽게 추가 가능 |

### 모듈 구조

```
src/screening/
├── __init__.py              # 모듈 진입점
├── screener.py              # StockScreener, ScreenerBuilder
├── conditions/
│   ├── __init__.py
│   ├── base_condition.py    # 기본 조건 클래스
│   ├── price_conditions.py  # 가격 조건
│   ├── technical_conditions.py  # 기술적 지표 조건
│   ├── fundamental_conditions.py  # 펀더멘털 조건
│   └── market_conditions.py # 시장/분류 조건
└── presets/
    ├── __init__.py
    └── preset_strategies.py # 프리셋 전략
```

---

## 빠른 시작

### 기본 사용법

```python
from src.screening import StockScreener, PriceAbove, RSIOversold

# 스크리너 생성
screener = StockScreener("내 스크리너")

# 조건 추가
screener.add_condition(PriceAbove(10000))  # 주가 10,000원 이상
screener.add_condition(RSIOversold(30))    # RSI 30 이하 (과매도)

# 스크리닝 실행
results = screener.screen(data)
print(f"조건 충족 종목: {len(results)}개")
```

### 빌더 패턴 사용

```python
from src.screening import ScreenerBuilder

# 체이닝 방식으로 스크리너 구성
results = (ScreenerBuilder("가치주 스크리너")
    .price_above(5000)
    .per_below(10)
    .pbr_below(1.0)
    .roe_above(10)
    .exclude_administrative()
    .sort_by('per', ascending=True)
    .limit(20)
    .screen(data))
```

### 프리셋 전략 사용

```python
from src.screening import get_preset_strategy

# 가치 투자 프리셋
screener = get_preset_strategy('value', max_per=8, max_pbr=0.8)
results = screener.screen(data)
```

---

## 조건 클래스

### 가격 조건 (Price Conditions)

`src/screening/conditions/price_conditions.py`

| 클래스 | 설명 | 예제 |
|--------|------|------|
| `PriceAbove` | 주가 >= 값 | `PriceAbove(10000)` |
| `PriceBelow` | 주가 <= 값 | `PriceBelow(50000)` |
| `PriceBetween` | 주가 범위 | `PriceBetween(10000, 50000)` |
| `PriceChangePercent` | 변동률 조건 | `PriceChangePercent(min_change=3.0)` |
| `Above52WeekHigh` | 52주 신고가 돌파 | `Above52WeekHigh()` |
| `Below52WeekLow` | 52주 신저가 하회 | `Below52WeekLow()` |
| `NearHighPercent` | 52주 고가 N% 이내 | `NearHighPercent(percent=5)` |
| `NearLowPercent` | 52주 저가 N% 이내 | `NearLowPercent(percent=10)` |
| `GapUp` | 갭상승 | `GapUp(percent=2.0)` |
| `GapDown` | 갭하락 | `GapDown(percent=2.0)` |
| `VolumeAbove` | 거래량 >= 값 | `VolumeAbove(1000000)` |
| `VolumeBelow` | 거래량 <= 값 | `VolumeBelow(100000)` |
| `VolumeRatio` | 거래량 비율 | `VolumeRatio(min_ratio=2.0)` |
| `AverageVolumeAbove` | 평균 거래량 >= 값 | `AverageVolumeAbove(500000)` |

#### 예제: 가격 조건

```python
from src.screening.conditions.price_conditions import *

# 주가 범위 조건
price_cond = PriceBetween(10000, 100000)

# 52주 고가 근접
high_cond = NearHighPercent(percent=3)

# 거래량 급증
volume_cond = VolumeRatio(min_ratio=3.0)

# 조건 조합
combined = price_cond & high_cond & volume_cond
```

---

### 기술적 지표 조건 (Technical Conditions)

`src/screening/conditions/technical_conditions.py`

| 클래스 | 설명 | 예제 |
|--------|------|------|
| `PriceAboveSMA` | 주가 > SMA | `PriceAboveSMA(period=200)` |
| `PriceBelowSMA` | 주가 < SMA | `PriceBelowSMA(period=50)` |
| `GoldenCross` | 골든크로스 | `GoldenCross(50, 200)` |
| `DeathCross` | 데드크로스 | `DeathCross(50, 200)` |
| `RSICondition` | RSI 범위 | `RSICondition(30, 70)` |
| `RSIOverbought` | RSI 과매수 | `RSIOverbought(70)` |
| `RSIOversold` | RSI 과매도 | `RSIOversold(30)` |
| `MACDCondition` | MACD 조건 | `MACDCondition('bullish')` |
| `MACDCrossover` | MACD 크로스오버 | `MACDCrossover('bullish')` |
| `BollingerBandCondition` | 볼린저밴드 위치 | `BollingerBandCondition('below_lower')` |
| `ATRCondition` | ATR 범위 | `ATRCondition(min_value=100)` |
| `StochasticCondition` | 스토캐스틱 범위 | `StochasticCondition(k_min=20)` |
| `ADXCondition` | ADX 추세 강도 | `ADXCondition(min_value=25)` |

#### 예제: 기술적 지표 조건

```python
from src.screening.conditions.technical_conditions import *

# 골든크로스 + RSI 중립
golden = GoldenCross(50, 200)
rsi = RSICondition(min_value=40, max_value=60)

# MACD 상승 신호
macd = MACDCondition(signal='bullish')

# 볼린저밴드 하단 터치 (반등 기대)
bb_lower = BollingerBandCondition(position='below_lower')

# 강한 추세
adx = ADXCondition(min_value=30)
```

---

### 펀더멘털 조건 (Fundamental Conditions)

`src/screening/conditions/fundamental_conditions.py`

| 클래스 | 설명 | 예제 |
|--------|------|------|
| `MarketCapAbove` | 시가총액 >= 값 | `MarketCapAbove(1e12)` |
| `MarketCapBelow` | 시가총액 <= 값 | `MarketCapBelow(1e11)` |
| `MarketCapBetween` | 시가총액 범위 | `MarketCapBetween(1e11, 1e12)` |
| `PERAbove` | PER >= 값 | `PERAbove(10)` |
| `PERBelow` | PER <= 값 | `PERBelow(15)` |
| `PERBetween` | PER 범위 | `PERBetween(5, 15)` |
| `PBRAbove` | PBR >= 값 | `PBRAbove(0.5)` |
| `PBRBelow` | PBR <= 값 | `PBRBelow(1.0)` |
| `PBRBetween` | PBR 범위 | `PBRBetween(0.5, 1.5)` |
| `DividendYieldAbove` | 배당수익률 >= 값 | `DividendYieldAbove(3.0)` |
| `ROEAbove` | ROE >= 값 | `ROEAbove(15)` |
| `ROAAbove` | ROA >= 값 | `ROAAbove(8)` |
| `DebtRatioBelow` | 부채비율 <= 값 | `DebtRatioBelow(100)` |
| `EPSGrowthAbove` | EPS 성장률 >= 값 | `EPSGrowthAbove(20)` |
| `RevenueGrowthAbove` | 매출 성장률 >= 값 | `RevenueGrowthAbove(15)` |

#### 예제: 펀더멘털 조건

```python
from src.screening.conditions.fundamental_conditions import *

# 가치 투자 조건
value_cond = PERBelow(10) & PBRBelow(1.0) & ROEAbove(10)

# 대형 우량주
bluechip = MarketCapAbove(1e12) & DebtRatioBelow(50)

# 고배당주
dividend = DividendYieldAbove(3.0) & MarketCapAbove(5e11)

# 성장주
growth = EPSGrowthAbove(25) & RevenueGrowthAbove(20)
```

---

### 시장/분류 조건 (Market Conditions)

`src/screening/conditions/market_conditions.py`

| 클래스 | 설명 | 예제 |
|--------|------|------|
| `MarketIs` | 특정 시장 | `MarketIs('KOSPI')` |
| `SectorIs` | 특정 섹터 | `SectorIs('IT')` |
| `SectorExclude` | 섹터 제외 | `SectorExclude(['금융'])` |
| `IndustryIs` | 특정 업종 | `IndustryIs('반도체')` |
| `IndustryExclude` | 업종 제외 | `IndustryExclude(['은행'])` |
| `ExcludeAdministrative` | 관리종목 제외 | `ExcludeAdministrative()` |
| `ExcludeTradingHalt` | 거래정지 제외 | `ExcludeTradingHalt()` |
| `OnlyETF` | ETF만 | `OnlyETF()` |
| `ExcludeETF` | ETF 제외 | `ExcludeETF()` |
| `ExcludePreferred` | 우선주 제외 | `ExcludePreferred()` |
| `ExcludeSPAC` | SPAC 제외 | `ExcludeSPAC()` |
| `ListedDaysAbove` | 상장일수 >= 값 | `ListedDaysAbove(365)` |
| `IndexMember` | 지수 구성종목 | `IndexMember('KOSPI200')` |
| `ThemeIs` | 특정 테마 | `ThemeIs('2차전지')` |

#### 예제: 시장/분류 조건

```python
from src.screening.conditions.market_conditions import *

# KOSPI 대형주
kospi_large = MarketIs('KOSPI') & IndexMember('KOSPI200')

# 특정 섹터 제외
exclude_finance = SectorExclude(['금융', '보험'])

# 일반 주식만 (ETF, 우선주, SPAC 제외)
common_stock = ExcludeETF() & ExcludePreferred() & ExcludeSPAC()

# 테마 필터
ev_theme = ThemeIs(['2차전지', '전기차', '배터리'])
```

---

## 조건 조합

### 논리 연산자

Python의 비트 연산자를 사용하여 조건을 조합합니다.

| 연산자 | 의미 | 예제 |
|--------|------|------|
| `&` | AND (모두 충족) | `cond1 & cond2` |
| `|` | OR (하나 이상 충족) | `cond1 | cond2` |
| `~` | NOT (반전) | `~cond1` |

### AND 조건

```python
from src.screening import PriceAbove, RSIOversold, MarketCapAbove

# 세 조건을 모두 만족해야 함
condition = PriceAbove(10000) & RSIOversold(30) & MarketCapAbove(1e11)
```

### OR 조건

```python
from src.screening import RSIOversold, BollingerBandCondition

# 둘 중 하나만 만족하면 됨
oversold = RSIOversold(25) | BollingerBandCondition('below_lower')
```

### NOT 조건

```python
from src.screening import MarketIs

# KOSPI가 아닌 종목
not_kospi = ~MarketIs('KOSPI')
```

### 복합 조건

```python
from src.screening import *

# 가치주 OR 성장주
value = PERBelow(10) & PBRBelow(1.0) & ROEAbove(10)
growth = EPSGrowthAbove(30) & RevenueGrowthAbove(25)

# 가치주이거나 성장주이면서, 관리종목이 아닌 종목
complex_condition = (value | growth) & ~ExcludeAdministrative()
```

---

## 스크리너 빌더

`ScreenerBuilder`는 체이닝 방식으로 스크리너를 구성할 수 있는 편리한 API를 제공합니다.

### 기본 사용법

```python
from src.screening import ScreenerBuilder

screener = (ScreenerBuilder("스크리너 이름")
    .price_above(5000)
    .price_below(100000)
    .per_below(15)
    .roe_above(10)
    .exclude_administrative()
    .exclude_etf()
    .sort_by('per', ascending=True)
    .limit(30)
    .build())

results = screener.screen(data)
```

### 빌더 메서드

#### 가격 관련

```python
.price_above(threshold)        # 주가 >= threshold
.price_below(threshold)        # 주가 <= threshold
.price_between(min, max)       # 주가 범위
.price_change_above(percent)   # 변동률 >= percent%
.price_change_below(percent)   # 변동률 <= percent%
.above_52week_high()           # 52주 신고가 돌파
.below_52week_low()            # 52주 신저가 하회
.volume_above(threshold)       # 거래량 >= threshold
.volume_ratio_above(ratio)     # 거래량비율 >= ratio
```

#### 기술적 지표

```python
.price_above_sma(period)           # 주가 > SMA
.price_below_sma(period)           # 주가 < SMA
.golden_cross(short, long)         # 골든크로스
.death_cross(short, long)          # 데드크로스
.rsi_above(threshold)              # RSI >= threshold
.rsi_below(threshold)              # RSI <= threshold
.rsi_between(min, max)             # RSI 범위
.macd_bullish()                    # MACD > Signal
.macd_bearish()                    # MACD < Signal
.bollinger_below_lower()           # 볼린저밴드 하단 이탈
.bollinger_above_upper()           # 볼린저밴드 상단 돌파
.adx_above(threshold)              # ADX >= threshold
```

#### 펀더멘털

```python
.market_cap_above(threshold)       # 시가총액 >= threshold
.market_cap_below(threshold)       # 시가총액 <= threshold
.market_cap_between(min, max)      # 시가총액 범위
.per_above(threshold)              # PER >= threshold
.per_below(threshold)              # PER <= threshold
.per_between(min, max)             # PER 범위
.pbr_above(threshold)              # PBR >= threshold
.pbr_below(threshold)              # PBR <= threshold
.pbr_between(min, max)             # PBR 범위
.dividend_yield_above(threshold)   # 배당수익률 >= threshold
.roe_above(threshold)              # ROE >= threshold
.roa_above(threshold)              # ROA >= threshold
.debt_ratio_below(threshold)       # 부채비율 <= threshold
.eps_growth_above(threshold)       # EPS성장률 >= threshold
.revenue_growth_above(threshold)   # 매출성장률 >= threshold
```

#### 시장/분류

```python
.market_is(market)                 # 특정 시장
.sector_is(sector)                 # 특정 섹터
.industry_is(industry)             # 특정 업종
.exclude_administrative()          # 관리종목 제외
.exclude_trading_halt()            # 거래정지 제외
.exclude_etf()                     # ETF 제외
.only_etf()                        # ETF만
```

#### 정렬 및 제한

```python
.sort_by(column, ascending=True)   # 정렬
.limit(n)                          # 결과 개수 제한
```

#### 커스텀 조건

```python
.custom(condition)                 # BaseCondition 객체 추가
.custom_func(name, func, columns)  # 람다 함수로 조건 추가
```

### 커스텀 함수 조건

```python
from src.screening import ScreenerBuilder

# 종가가 시가보다 5% 이상 높은 종목 (양봉)
screener = (ScreenerBuilder("양봉 스크리너")
    .custom_func(
        name="강한 양봉",
        func=lambda df: (df['close'] - df['open']) / df['open'] > 0.05,
        required_columns=['open', 'close']
    )
    .volume_above(100000)
    .build())
```

---

## 프리셋 전략

### 사용 가능한 프리셋

| 프리셋 | 설명 |
|--------|------|
| `value` | 저평가된 우량 기업 (낮은 PER/PBR, 높은 ROE) |
| `growth` | 고성장 기업 (높은 EPS/매출 성장률) |
| `momentum` | 강한 상승 추세 (이동평균 돌파, RSI 상승) |
| `dividend` | 안정적인 고배당주 |
| `small_cap_value` | 저평가된 소형주 |
| `quality` | 재무 우량 기업 (높은 ROE/ROA) |
| `turnaround` | 실적 개선 기대 종목 (저점 근처) |
| `oversold_bounce` | 과매도 반등 기대 (RSI/볼린저) |
| `breakout` | 주요 저항 돌파 (신고가, 골든크로스) |
| `income` | 안정적 수입 추구 (고배당 대형주) |

### 프리셋 사용법

```python
from src.screening import get_preset_strategy, list_preset_strategies

# 사용 가능한 프리셋 목록
presets = list_preset_strategies()
for p in presets:
    print(f"{p['key']}: {p['description']}")

# 프리셋 전략 사용
screener = get_preset_strategy('value')
results = screener.screen(data)

# 파라미터 커스터마이징
screener = get_preset_strategy('value', max_per=8, max_pbr=0.8, limit=50)
results = screener.screen(data)
```

### 프리셋 상세

#### 가치 투자 (value)

```python
screener = get_preset_strategy('value',
    max_per=10.0,           # 최대 PER
    max_pbr=1.0,            # 최대 PBR
    min_roe=10.0,           # 최소 ROE
    max_debt_ratio=100.0,   # 최대 부채비율
    min_market_cap=1e11,    # 최소 시가총액
    limit=30                # 결과 개수
)
```

#### 성장 투자 (growth)

```python
screener = get_preset_strategy('growth',
    min_eps_growth=20.0,      # 최소 EPS 성장률
    min_revenue_growth=15.0,  # 최소 매출 성장률
    min_roe=15.0,             # 최소 ROE
    min_market_cap=5e10,      # 최소 시가총액
    limit=30
)
```

#### 모멘텀 (momentum)

```python
screener = get_preset_strategy('momentum',
    min_volume_ratio=1.5,   # 최소 거래량 비율
    min_rsi=50.0,           # 최소 RSI
    max_rsi=70.0,           # 최대 RSI (과매수 제외)
    min_market_cap=1e11,
    limit=30
)
```

#### 배당 투자 (dividend)

```python
screener = get_preset_strategy('dividend',
    min_dividend_yield=3.0,   # 최소 배당수익률
    max_debt_ratio=100.0,     # 최대 부채비율
    min_market_cap=5e11,
    limit=30
)
```

---

## 설정 항목

`config/config.yaml`

```yaml
screening:
  # 기본 조건
  defaults:
    exclude_administrative: true  # 관리종목 제외
    exclude_trading_halt: true    # 거래정지 제외
    exclude_etf: true             # ETF 제외
    min_market_cap: 50000000000   # 최소 시가총액 (500억)
    min_volume: 10000             # 최소 거래량

  # 가격 조건
  price:
    min_price: 1000       # 최소 주가
    max_price: null       # 최대 주가

  # 기술적 지표 조건
  technical:
    rsi_oversold: 30      # RSI 과매도 기준
    rsi_overbought: 70    # RSI 과매수 기준
    sma_periods: [20, 50, 200]

  # 펀더멘털 조건
  fundamental:
    max_per: 20           # 최대 PER
    max_pbr: 3.0          # 최대 PBR
    min_roe: 5            # 최소 ROE
    max_debt_ratio: 200   # 최대 부채비율

  # 프리셋
  presets:
    default: "value"      # 기본 프리셋

  # 결과
  results:
    max_stocks: 50        # 최대 결과 종목 수
    sort_by: "market_cap" # 정렬 기준
    sort_ascending: false
```

### 설정값 사용

```python
from src.utils.config_loader import get_config

config = get_config()

# 스크리닝 기본 설정
min_market_cap = config.get('screening.defaults.min_market_cap', 5e10)
rsi_oversold = config.get('screening.technical.rsi_oversold', 30)

# 프리셋 설정
default_preset = config.get('screening.presets.default', 'value')
```

---

## 예제 코드

### 예제 1: 기본 스크리닝

```python
from src.screening import StockScreener, PriceAbove, PERBelow, ROEAbove
from src.utils.database import get_db

# 데이터 로드
db = get_db()
data = db.get_latest_stock_data()

# 스크리너 생성 및 조건 추가
screener = StockScreener("기본 스크리너")
screener.add_conditions(
    PriceAbove(5000),
    PERBelow(15),
    ROEAbove(10)
)

# 스크리닝 실행
results = screener.screen(data)
print(f"필터링된 종목 수: {len(results)}")
print(results[['symbol', 'name', 'close', 'per', 'roe']].head(10))
```

### 예제 2: 빌더 패턴 활용

```python
from src.screening import ScreenerBuilder

# 성장 가치주 스크리너
results = (ScreenerBuilder("성장 가치주")
    .market_is(['KOSPI', 'KOSDAQ'])
    .market_cap_above(1e11)       # 1000억 이상
    .per_between(5, 15)           # PER 5~15
    .pbr_below(1.5)               # PBR 1.5 이하
    .roe_above(12)                # ROE 12% 이상
    .eps_growth_above(10)         # EPS 성장률 10% 이상
    .debt_ratio_below(100)        # 부채비율 100% 이하
    .exclude_administrative()
    .exclude_etf()
    .sort_by('roe', ascending=False)
    .limit(20)
    .screen(data))

print("성장 가치주 TOP 20:")
print(results[['symbol', 'name', 'per', 'pbr', 'roe', 'eps_growth']])
```

### 예제 3: 기술적 분석 스크리닝

```python
from src.screening import ScreenerBuilder

# 기술적 반등 기대 종목
results = (ScreenerBuilder("기술적 반등")
    .market_cap_above(5e10)       # 500억 이상
    .rsi_below(30)                # RSI 과매도
    .bollinger_below_lower()      # 볼린저밴드 하단 이탈
    .volume_ratio_above(1.5)      # 거래량 증가
    .exclude_administrative()
    .sort_by('rsi', ascending=True)
    .limit(10)
    .screen(data))

print("기술적 반등 기대 종목:")
print(results[['symbol', 'name', 'close', 'rsi', 'change_pct']])
```

### 예제 4: 조건 조합 고급 활용

```python
from src.screening import *

# 복합 조건: (가치주 OR 성장주) AND 대형주 AND NOT 금융
value_cond = PERBelow(10) & PBRBelow(1.0) & ROEAbove(15)
growth_cond = EPSGrowthAbove(30) & RevenueGrowthAbove(25)
large_cap = MarketCapAbove(1e12)  # 1조 이상
no_finance = SectorExclude(['금융', '보험', '은행'])
not_admin = ExcludeAdministrative()

final_condition = (value_cond | growth_cond) & large_cap & no_finance & not_admin

# 스크리너에 복합 조건 추가
screener = StockScreener("복합 조건")
screener.add_condition(final_condition)
screener.set_sort('market_cap', ascending=False)
screener.set_limit(30)

results = screener.screen(data)
```

### 예제 5: 프리셋 비교

```python
from src.screening import get_preset_strategy, list_preset_strategies

# 여러 프리셋 전략 비교
presets_to_test = ['value', 'growth', 'momentum', 'dividend']

print("프리셋별 스크리닝 결과:")
print("=" * 60)

for preset_name in presets_to_test:
    screener = get_preset_strategy(preset_name)
    results = screener.screen(data)

    print(f"\n{screener.name}: {len(results)}개 종목")
    if len(results) > 0:
        print(f"  대표 종목: {results['name'].head(3).tolist()}")
```

### 예제 6: 스크리닝 통계

```python
from src.screening import ScreenerBuilder

screener = (ScreenerBuilder("통계 테스트")
    .market_cap_above(1e11)
    .per_below(20)
    .roe_above(10)
    .exclude_administrative()
    .build())

# 스크리닝 통계 확인
stats = screener.get_statistics(data)

print("스크리닝 통계:")
print(f"  전체 종목: {stats['total_stocks']}")
print(f"  통과 종목: {stats['passed_stocks']}")
print(f"  필터링: {stats['filtered_out']}")
print(f"  통과율: {stats['pass_rate']:.1f}%")

print("\n조건별 통과율:")
for cond_stat in stats['condition_stats']:
    print(f"  {cond_stat['name']}: {cond_stat['pass_rate']:.1f}%")
```

### 예제 7: 커스텀 조건 생성

```python
from src.screening.conditions.base_condition import CustomCondition, BaseCondition
from src.screening import StockScreener
import pandas as pd

# 방법 1: CustomCondition 사용
strong_candle = CustomCondition(
    name="강한 양봉",
    func=lambda df: (df['close'] - df['open']) / df['open'] > 0.03,
    required_columns=['open', 'close'],
    description="종가가 시가보다 3% 이상 높은 강한 양봉"
)

# 방법 2: 클래스 상속
class VolumeSpike(BaseCondition):
    """거래량 급증 조건 (이전 N일 평균 대비)"""

    def __init__(self, days: int = 5, multiplier: float = 3.0):
        super().__init__(
            name=f"거래량 급증 ({multiplier}배)",
            description=f"최근 {days}일 평균 대비 {multiplier}배 이상"
        )
        self.days = days
        self.multiplier = multiplier
        self._required_columns = ['volume', f'volume_ma_{days}']

    def evaluate(self, data: pd.DataFrame) -> pd.Series:
        self.validate_columns(data)
        return data['volume'] > data[f'volume_ma_{self.days}'] * self.multiplier

# 사용
screener = StockScreener("커스텀 조건")
screener.add_condition(strong_candle)
screener.add_condition(VolumeSpike(5, 2.5))
results = screener.screen(data)
```

---

## 주의사항

1. **데이터 요구사항**: 각 조건은 특정 컬럼을 필요로 합니다. 데이터에 필요한 컬럼이 없으면 오류가 발생합니다.

2. **성능**: 많은 조건을 조합하면 처리 시간이 증가합니다. 효율적인 순서로 조건을 배치하세요 (많이 필터링되는 조건을 먼저).

3. **데이터 품질**: 스크리닝 결과는 데이터 품질에 크게 의존합니다. 결측치, 이상치 처리가 필요합니다.

4. **과최적화 주의**: 너무 많은 조건은 과최적화를 야기할 수 있습니다.

5. **시장 상황**: 동일한 조건도 시장 상황에 따라 다른 결과를 줄 수 있습니다.

---

## 다음 단계

- [01. 시작하기](./01-getting-started.md) - 설치 및 기본 설정
- [03. 기술적 지표](./03-technical-indicators.md) - 기술적 지표 계산
- [04. 팩터 분석](./04-factor-analysis.md) - 팩터 기반 분석
- [05. 투자 전략](./05-strategies.md) - 전략 구현
