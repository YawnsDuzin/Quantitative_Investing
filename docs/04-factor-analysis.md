# 04. 팩터 분석 (Factor Analysis)

퀀트 투자에서 사용되는 팩터(모멘텀, 가치, 퀄리티 등)를 계산하는 방법에 대한 매뉴얼입니다.

## 목차

1. [팩터 투자 개요](#팩터-투자-개요)
2. [FactorCalculator 클래스](#factorcalculator-클래스)
3. [개별 팩터 상세](#개별-팩터-상세)
4. [복합 팩터 계산](#복합-팩터-계산)
5. [교차 섹션 분석](#교차-섹션-분석)
6. [설정 항목](#설정-항목)
7. [예제 코드](#예제-코드)

---

## 팩터 투자 개요

**파일 위치**: `src/data_processing/feature_engineering.py`

팩터 투자는 특정 특성(팩터)을 가진 주식들이 시장을 초과하는 수익을 낸다는 학술적 연구에 기반한 투자 방법입니다.

### 주요 팩터

| 팩터 | 설명 | 기대 효과 |
|------|------|----------|
| **모멘텀 (Momentum)** | 과거 수익률이 높은 주식 | 상승세 지속 |
| **가치 (Value)** | 저평가된 주식 (낮은 PER, PBR) | 평균 회귀 |
| **퀄리티 (Quality)** | 높은 수익성, 낮은 부채 | 안정적 성장 |
| **사이즈 (Size)** | 소형주 | 크기 프리미엄 |
| **저변동성 (Low Volatility)** | 변동성이 낮은 주식 | 리스크 조정 수익 |

### 팩터 스코어링 프로세스

```
1. 원시 팩터 값 계산 (예: PER)
      ↓
2. 이상치 처리 (Winsorize)
      ↓
3. 순위 정규화 (Rank Normalize) - 0~1 범위
      ↓
4. 복합 팩터 계산 (가중 합계)
      ↓
5. 종목 선정 (상위 N%)
```

---

## FactorCalculator 클래스

### 기본 사용법

```python
from src.data_processing.feature_engineering import FactorCalculator

fc = FactorCalculator()
```

모든 메서드는 `@staticmethod`로 정의되어 있어 인스턴스 없이도 사용 가능:

```python
# 직접 호출
momentum = FactorCalculator.momentum_factor(df['close'], period=252)
```

---

## 개별 팩터 상세

### 1. 모멘텀 팩터 (Momentum Factor)

과거 수익률을 기반으로 주가 상승 추세를 측정합니다.

```python
momentum = FactorCalculator.momentum_factor(
    prices=df['close'],
    period=252,        # 12개월 (252 거래일)
    skip_recent=20     # 최근 1개월 제외
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `prices` | pd.Series | 필수 | 가격 시리즈 |
| `period` | int | 252 | 수익률 계산 기간 (거래일) |
| `skip_recent` | int | 20 | 최근 제외 기간 (단기 반전 효과 방지) |

**계산 방식**:
```
모멘텀 = (t-skip_recent 가격) / (t-period-skip_recent 가격) - 1
```

**해석**:
- 양수: 상승 추세
- 음수: 하락 추세
- 높을수록 강한 모멘텀

**추천 기간**:
| 기간 | 거래일 | 용도 |
|------|--------|------|
| 3개월 | 63 | 단기 모멘텀 |
| 6개월 | 126 | 중기 모멘텀 |
| 12개월 | 252 | 장기 모멘텀 (가장 일반적) |

```python
# 다양한 기간의 모멘텀
df['momentum_12m'] = fc.momentum_factor(df['close'], 252, 20)
df['momentum_6m'] = fc.momentum_factor(df['close'], 126, 20)
df['momentum_3m'] = fc.momentum_factor(df['close'], 63, 20)
```

---

### 2. 가치 팩터 (Value Factor)

저평가된 주식을 찾기 위한 팩터입니다.

#### PBR 기반 가치 팩터

```python
value_pbr = FactorCalculator.value_pbr_factor(df['pbr'])
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `pbr` | pd.Series | 주가순자산비율 시리즈 |

**계산 방식**: `1 / PBR` (낮은 PBR = 높은 가치 스코어)

#### PER 기반 가치 팩터

```python
value_per = FactorCalculator.value_per_factor(df['per'])
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `per` | pd.Series | 주가수익비율 시리즈 |

**계산 방식**: `1 / PER` (음수 PER은 제외)

**참고**:
- PER < 0: 적자 기업 (제외)
- PER > 100: 고평가 또는 특수 상황

---

### 3. 퀄리티 팩터 (Quality Factor)

재무 건전성과 수익성을 측정합니다.

#### ROE 기반 퀄리티 팩터

```python
quality_roe = FactorCalculator.quality_roe_factor(df['roe'])
```

**계산 방식**: ROE 그대로 사용 (높을수록 좋음)

| ROE 범위 | 평가 |
|----------|------|
| > 20% | 우수 |
| 10-20% | 양호 |
| 5-10% | 보통 |
| < 5% | 저조 |

#### 부채비율 기반 퀄리티 팩터

```python
quality_debt = FactorCalculator.quality_debt_factor(df['debt_ratio'])
```

**계산 방식**: `1 / (1 + 부채비율)` (낮은 부채 = 높은 스코어)

---

### 4. 사이즈 팩터 (Size Factor)

시가총액을 기반으로 소형주를 선호합니다.

```python
size = FactorCalculator.size_factor(df['market_cap'])
```

**계산 방식**: `-log(시가총액)` (작은 시가총액 = 높은 스코어)

**참고**: 소형주 프리미엄은 학술적으로 검증되었으나, 유동성 리스크가 있습니다.

---

### 5. 변동성 팩터 (Volatility Factor)

저변동성 주식을 선호합니다.

```python
volatility = FactorCalculator.volatility_factor(
    returns=df['returns'],
    period=252
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `returns` | pd.Series | 필수 | 수익률 시리즈 |
| `period` | int | 252 | 변동성 계산 기간 |

**계산 방식**: `-rolling_std` (낮은 변동성 = 높은 스코어)

---

### 6. 유동성 팩터 (Liquidity Factor)

거래 유동성을 측정합니다.

```python
liquidity = FactorCalculator.liquidity_factor(
    volume=df['volume'],
    price=df['close'],
    period=20
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `volume` | pd.Series | 필수 | 거래량 시리즈 |
| `price` | pd.Series | 필수 | 가격 시리즈 |
| `period` | int | 20 | 평균 계산 기간 |

**계산 방식**: `log(평균 거래대금)`

---

### 7. 추세 강도 팩터 (Trend Strength Factor)

이동평균 대비 가격 위치를 측정합니다.

```python
trend = FactorCalculator.trend_strength_factor(
    prices=df['close'],
    period=200
)
```

**계산 방식**: `(가격 / 200일 이동평균) - 1`

---

## 복합 팩터 계산

### 복합 가치 팩터

```python
combined_value = FactorCalculator.combined_value_factor(
    pbr=df['pbr'],
    per=df['per'],
    weights=[0.5, 0.5]  # PBR 50%, PER 50%
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `pbr` | pd.Series | None | PBR 시리즈 |
| `per` | pd.Series | None | PER 시리즈 |
| `weights` | List[float] | None | 각 팩터 가중치 (기본: 동일 가중) |

### 복합 퀄리티 팩터

```python
combined_quality = FactorCalculator.combined_quality_factor(
    roe=df['roe'],
    debt_ratio=df['debt_ratio'],
    weights=[0.6, 0.4]  # ROE 60%, 부채비율 40%
)
```

---

## 교차 섹션 분석

### CrossSectionalFactors 클래스

여러 종목을 동시에 분석하여 상대적 팩터 순위를 계산합니다.

```python
from src.data_processing.feature_engineering import CrossSectionalFactors

csf = CrossSectionalFactors()
```

### `calculate_cross_sectional_factors()` - 교차 섹션 팩터 계산

```python
df_with_factors = CrossSectionalFactors.calculate_cross_sectional_factors(
    df,
    date_col='date',
    symbol_col='symbol',
    price_col='close'
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `df` | DataFrame | 필수 | 멀티 종목 데이터 |
| `date_col` | str | 'date' | 날짜 컬럼명 |
| `symbol_col` | str | 'symbol' | 종목 코드 컬럼명 |
| `price_col` | str | 'close' | 가격 컬럼명 |

**추가되는 컬럼**:
- `momentum_12m`: 12개월 모멘텀
- `momentum_6m`: 6개월 모멘텀
- `momentum_12m_rank`: 모멘텀 순위 (0-1)
- `value_pbr`: PBR 기반 가치 스코어
- `value_per`: PER 기반 가치 스코어
- `quality_roe`: ROE 기반 퀄리티 스코어
- `size_factor`: 사이즈 팩터

### `create_composite_score()` - 복합 스코어 생성

```python
composite_score = CrossSectionalFactors.create_composite_score(
    df=df_with_factors,
    factor_columns=['momentum_12m_rank', 'value_pbr', 'quality_roe', 'size_factor'],
    weights=[0.4, 0.3, 0.2, 0.1]  # 모멘텀 40%, 가치 30%, 퀄리티 20%, 사이즈 10%
)

df_with_factors['composite_score'] = composite_score
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `df` | DataFrame | 필수 | 팩터가 포함된 데이터프레임 |
| `factor_columns` | List[str] | 필수 | 사용할 팩터 컬럼 리스트 |
| `weights` | List[float] | None | 각 팩터 가중치 (기본: 동일 가중) |

---

## 설정 항목

`config/config.yaml` 파일의 `strategy.factor_weights` 섹션에서 팩터 가중치를 설정합니다:

```yaml
strategy:
  # 팩터 가중치 (총합 1.0)
  factor_weights:
    momentum: 0.4    # 모멘텀 40%
    value: 0.3       # 가치 30%
    quality: 0.2     # 퀄리티 20%
    size: 0.1        # 사이즈 10%
```

### 설정값 사용

```python
from src.utils.config_loader import get_config

config = get_config()
factor_weights = config.get('strategy.factor_weights')

print(factor_weights)
# {'momentum': 0.4, 'value': 0.3, 'quality': 0.2, 'size': 0.1}
```

---

## 예제 코드

### 예제 1: 개별 종목 팩터 계산

```python
from src.data_processing.feature_engineering import FactorCalculator, add_all_factors
from src.data_collection.kr_stock_collector import KoreanStockCollector

# 데이터 수집
collector = KoreanStockCollector()
price_df = collector.get_price_data('005930', '2020-01-01', '2024-01-01')
fundamental_df = collector.get_fundamental_data('005930', '2020-01-01', '2024-01-01')

# 데이터 병합
df = price_df.merge(fundamental_df, on=['date', 'symbol'], how='left')

# 개별 팩터 계산
fc = FactorCalculator()

df['momentum_12m'] = fc.momentum_factor(df['close'], 252, 20)
df['momentum_6m'] = fc.momentum_factor(df['close'], 126, 20)
df['value_pbr'] = fc.value_pbr_factor(df['pbr'])
df['value_per'] = fc.value_per_factor(df['per'])

print(df[['date', 'close', 'momentum_12m', 'value_pbr']].tail())
```

### 예제 2: 모든 팩터 일괄 추가

```python
from src.data_processing.feature_engineering import add_all_factors

# 모든 팩터 추가
df_with_factors = add_all_factors(df)

# 추가된 팩터 확인
factor_cols = [col for col in df_with_factors.columns
               if any(f in col for f in ['momentum', 'value', 'quality', 'size', 'liquidity'])]
print(f"추가된 팩터: {factor_cols}")
```

### 예제 3: 멀티 종목 교차 섹션 분석

```python
from src.data_processing.feature_engineering import CrossSectionalFactors
from src.utils.database import get_db
import pandas as pd

# DB에서 다중 종목 데이터 로드
db = get_db()
df = db.get_stock_prices(start_date='2023-01-01')

# 펀더멘털 데이터 병합
fundamentals = db.get_fundamentals(start_date='2023-01-01')
df = df.merge(fundamentals, on=['symbol', 'date'], how='left')

# 교차 섹션 팩터 계산
df_factors = CrossSectionalFactors.calculate_cross_sectional_factors(
    df,
    date_col='date',
    symbol_col='symbol',
    price_col='close'
)

# 특정 날짜의 팩터 순위 확인
latest_date = df_factors['date'].max()
latest_data = df_factors[df_factors['date'] == latest_date]

# 모멘텀 상위 10개 종목
top_momentum = latest_data.nlargest(10, 'momentum_12m_rank')[['symbol', 'momentum_12m_rank']]
print("모멘텀 상위 10개 종목:")
print(top_momentum)
```

### 예제 4: 복합 스코어 기반 종목 선정

```python
from src.data_processing.feature_engineering import CrossSectionalFactors

# 복합 스코어 생성
composite = CrossSectionalFactors.create_composite_score(
    df_factors,
    factor_columns=['momentum_12m_rank', 'value_pbr', 'quality_roe'],
    weights=[0.5, 0.3, 0.2]  # 모멘텀 50%, 가치 30%, 퀄리티 20%
)

df_factors['composite_score'] = composite

# 최신 날짜의 상위 20개 종목 선정
latest_data = df_factors[df_factors['date'] == df_factors['date'].max()]
top_20 = latest_data.nlargest(20, 'composite_score')

print("복합 스코어 상위 20개 종목:")
print(top_20[['symbol', 'composite_score', 'momentum_12m_rank', 'value_pbr']].to_string())
```

### 예제 5: 팩터 상관관계 분석

```python
import seaborn as sns
import matplotlib.pyplot as plt

# 팩터 컬럼만 선택
factor_cols = ['momentum_12m_rank', 'value_pbr', 'quality_roe', 'size_factor']
factor_data = df_factors[factor_cols].dropna()

# 상관관계 계산
correlation = factor_data.corr()

# 히트맵 시각화
plt.figure(figsize=(10, 8))
sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0,
            xticklabels=['Momentum', 'Value', 'Quality', 'Size'],
            yticklabels=['Momentum', 'Value', 'Quality', 'Size'])
plt.title('Factor Correlation Matrix')
plt.tight_layout()
plt.savefig('factor_correlation.png')
plt.show()
```

---

## 유틸리티 함수

### `rank_normalize()` - 순위 정규화

```python
from src.utils.helpers import rank_normalize

# 0-1 범위로 정규화
normalized = rank_normalize(df['momentum'])
```

### `winsorize()` - 이상치 처리

```python
from src.utils.helpers import winsorize

# 상하위 1% 값을 제한
cleaned = winsorize(df['per'], lower_percentile=0.01, upper_percentile=0.99)
```

---

## 주의사항

1. **데이터 품질**: 팩터 계산 전 결측치와 이상치를 처리해야 합니다.

2. **생존자 편향**: 과거 상장폐지된 종목도 포함해야 정확한 백테스트가 가능합니다.

3. **팩터 시차**: 펀더멘털 데이터는 발표 시점이 다르므로 look-ahead bias에 주의합니다.

4. **팩터 혼잡**: 너무 많은 투자자가 같은 팩터를 사용하면 효과가 감소할 수 있습니다.

---

## 다음 단계

- [05. 투자 전략](./05-strategies.md) - 팩터 기반 투자 전략
- [06. 포트폴리오 최적화](./06-portfolio-optimizer.md) - 포트폴리오 구성
