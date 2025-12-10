# 백테스팅 가이드

이 문서는 Quantitative Investing 시스템의 백테스팅 기능에 대한 상세한 설명을 제공합니다.

## 목차

1. [개요](#개요)
2. [백테스팅 구조](#백테스팅-구조)
3. [백테스팅 데이터 항목](#백테스팅-데이터-항목)
4. [성과 지표](#성과-지표)
5. [전략 구현](#전략-구현)
6. [백테스트 실행](#백테스트-실행)
7. [거래 비용 모델링](#거래-비용-모델링)
8. [결과 분석](#결과-분석)
9. [주의사항 및 한계](#주의사항-및-한계)
10. [고급 활용법](#고급-활용법)

---

## 개요

백테스팅은 과거 데이터를 사용하여 투자 전략의 성과를 검증하는 과정입니다. Quantitative Investing 시스템은 다양한 팩터 기반 전략과 종합적인 성과 분석 기능을 제공합니다.

### 백테스팅 프로세스

```
1. 데이터 로드
   ├── 가격 데이터 (OHLCV)
   ├── 펀더멘털 데이터 (PER, PBR, ROE 등)
   └── 시가총액 데이터

2. 팩터 계산
   ├── 모멘텀 팩터
   ├── 밸류 팩터
   ├── 퀄리티 팩터
   └── 사이즈 팩터

3. 시그널 생성
   └── 각 리밸런싱 시점마다 종목 선정

4. 포트폴리오 구성
   └── 상위 N개 종목 동일 비중

5. 거래 실행
   ├── 수수료 적용
   └── 슬리피지 적용

6. 성과 계산
   ├── 수익률 지표
   ├── 리스크 지표
   └── 위험조정 수익률
```

---

## 백테스팅 구조

### 모듈 구조

```
src/
├── backtesting/
│   ├── __init__.py
│   ├── backtester.py         # 메인 백테스터 클래스
│   └── performance_metrics.py # 성과 지표 계산
│
├── strategies/
│   ├── __init__.py
│   ├── base_strategy.py      # 전략 기본 클래스
│   └── quant_strategies.py   # 퀀트 전략 구현
│
└── data_processing/
    ├── indicators.py         # 기술적 지표
    └── feature_engineering.py # 팩터 계산
```

### 핵심 클래스

```python
# 백테스터
from src.backtesting import Backtester

# 전략
from src.strategies import (
    MomentumStrategy,
    ValueStrategy,
    QualityStrategy,
    MultiFactorStrategy,
    SizeStrategy,
    create_strategy
)

# 성과 분석
from src.backtesting import PerformanceMetrics
```

---

## 백테스팅 데이터 항목

### 1. 필수 가격 데이터

| 항목 | 필드명 | 용도 | 비고 |
|------|--------|------|------|
| 날짜 | `date` | 시간 축 | YYYY-MM-DD |
| 종목코드 | `symbol` | 종목 식별 | 문자열 |
| 시가 | `open` | 실행가 참조 | - |
| 고가 | `high` | 변동성 계산 | - |
| 저가 | `low` | 변동성 계산 | - |
| 종가 | `close` | 수익률 계산 | 필수 |
| 거래량 | `volume` | 유동성 필터 | - |
| 수정종가 | `adj_close` | 배당 조정 수익률 | 권장 |

### 2. 팩터 계산용 데이터

#### 2.1 밸류 팩터 데이터

| 항목 | 필드명 | 계산 | 해석 |
|------|--------|------|------|
| PER | `per` | 주가/EPS | 낮을수록 저평가 |
| PBR | `pbr` | 주가/BPS | 낮을수록 저평가 |
| PSR | `psr` | 주가/SPS | 낮을수록 저평가 |
| PEG | `peg_ratio` | PER/성장률 | 1 미만 저평가 |
| EV/EBITDA | `ev_to_ebitda` | EV/EBITDA | 낮을수록 저평가 |

**밸류 스코어 계산:**
```python
value_score = rank_normalize(1/PER) * 0.5 + rank_normalize(1/PBR) * 0.5
```

#### 2.2 모멘텀 팩터 데이터

| 항목 | 필드명 | 계산 | 기간 |
|------|--------|------|------|
| 12개월 모멘텀 | `momentum_12m` | (P_t-20 / P_t-272) - 1 | 252일 |
| 6개월 모멘텀 | `momentum_6m` | (P_t-20 / P_t-146) - 1 | 126일 |
| 3개월 모멘텀 | `momentum_3m` | (P_t-20 / P_t-83) - 1 | 63일 |

**모멘텀 스코어 계산:**
```python
# 최근 1개월은 제외 (단기 반전 효과)
momentum_score = (price[t-20] / price[t-272]) - 1
momentum_rank = rank_normalize(momentum_score)
```

#### 2.3 퀄리티 팩터 데이터

| 항목 | 필드명 | 해석 | 기준 |
|------|--------|------|------|
| ROE | `roe` | 자기자본이익률 | 높을수록 좋음 |
| ROA | `roa` | 총자산이익률 | 높을수록 좋음 |
| 영업이익률 | `operating_margin` | 영업효율성 | 높을수록 좋음 |
| 부채비율 | `debt_ratio` | 재무 레버리지 | 낮을수록 좋음 |

**퀄리티 스코어 계산:**
```python
quality_roe = rank_normalize(roe)
quality_debt = rank_normalize(1 / (1 + debt_ratio))
quality_score = quality_roe * 0.6 + quality_debt * 0.4
```

#### 2.4 사이즈 팩터 데이터

| 항목 | 필드명 | 해석 |
|------|--------|------|
| 시가총액 | `market_cap` | 기업 규모 |

**사이즈 스코어 계산:**
```python
# 소형주 프리미엄: 작을수록 높은 점수
size_score = -np.log(market_cap)
size_rank = rank_normalize(size_score)
```

### 3. 선택적 데이터 (향상된 백테스팅)

| 항목 | 필드명 | 용도 |
|------|--------|------|
| F-Score | `f_score` | 재무 건전성 필터 |
| Z-Score | `z_score` | 파산 위험 필터 |
| 베타 | `beta` | 리스크 조절 |
| 섹터 | `sector` | 섹터 중립화 |
| 배당수익률 | `dividend_yield` | 배당 전략 |

---

## 성과 지표

### 1. 수익률 지표 (Return Metrics)

| 지표 | 계산 방법 | 해석 |
|------|----------|------|
| **총 수익률** | (최종가치/초기가치) - 1 | 전체 기간 수익 |
| **연환산 수익률 (CAGR)** | (1+총수익률)^(1/연수) - 1 | 연평균 복리 수익 |
| **월간 수익률** | 월별 수익률 시계열 | 수익 분포 분석 |

```python
from src.backtesting import PerformanceMetrics

metrics = PerformanceMetrics(portfolio_values)

total_return = metrics.total_return()      # 예: 0.45 (45%)
annual_return = metrics.annual_return()    # 예: 0.12 (12%)
```

### 2. 리스크 지표 (Risk Metrics)

| 지표 | 계산 방법 | 해석 |
|------|----------|------|
| **변동성** | 수익률 표준편차 × √252 | 연간 변동성 |
| **최대 낙폭 (MDD)** | max((peak - trough) / peak) | 최악의 손실 |
| **VaR (95%)** | 5% 분위수 일간 손실 | 95% 신뢰 손실 한계 |
| **CVaR (95%)** | VaR 초과 손실 평균 | 꼬리 리스크 |

```python
volatility = metrics.volatility(annualized=True)
max_drawdown = metrics.max_drawdown()      # 예: 0.25 (25% 낙폭)
var_95 = metrics.value_at_risk(0.95)
cvar_95 = metrics.conditional_value_at_risk(0.95)
```

### 3. 위험조정 수익률 (Risk-Adjusted Returns)

| 지표 | 계산 방법 | 해석 | 기준 |
|------|----------|------|------|
| **샤프 비율** | (수익률 - 무위험) / 변동성 | 리스크 단위당 초과수익 | 1 이상 양호 |
| **소르티노 비율** | (수익률 - 무위험) / 하방변동성 | 하방 리스크 고려 | 1.5 이상 양호 |
| **칼마 비율** | 연수익률 / 최대낙폭 | MDD 대비 수익 | 1 이상 양호 |
| **정보 비율** | 초과수익 / 추적오차 | 벤치마크 대비 | 0.5 이상 양호 |

```python
sharpe = metrics.sharpe_ratio(risk_free_rate=0.02)
sortino = metrics.sortino_ratio(risk_free_rate=0.02)
calmar = metrics.calmar_ratio()
```

### 4. 거래 지표 (Trading Metrics)

| 지표 | 계산 방법 | 해석 |
|------|----------|------|
| **승률** | 양수 수익 일수 / 전체 일수 | 수익 빈도 |
| **손익비** | 평균 수익 / 평균 손실 | 수익 크기 비율 |
| **프로핏 팩터** | 총 수익 / 총 손실 | 절대 손익 비율 |

```python
win_rate = metrics.win_rate()
profit_factor = metrics.profit_factor()
```

### 5. 성과 지표 요약 함수

```python
summary = metrics.get_summary()
# {
#     'total_return': 0.45,
#     'annual_return': 0.12,
#     'volatility': 0.18,
#     'sharpe_ratio': 0.67,
#     'sortino_ratio': 0.89,
#     'max_drawdown': 0.25,
#     'calmar_ratio': 0.48,
#     'win_rate': 0.54,
#     'profit_factor': 1.23
# }
```

---

## 전략 구현

### 1. 기본 전략 클래스

모든 전략은 `BaseStrategy` 클래스를 상속합니다.

```python
from src.strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self, config=None):
        super().__init__(name="MyStrategy", config=config)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """시그널 생성 로직"""
        signals = data.copy()
        # 시그널 계산 로직
        return signals

    def select_stocks(self, data: pd.DataFrame, top_n: int = None) -> List[str]:
        """종목 선정 로직"""
        if top_n is None:
            top_n = self.config.get('max_positions', 20)

        # 선정 로직
        return selected_symbols
```

### 2. 내장 전략

#### 모멘텀 전략 (MomentumStrategy)

```python
from src.strategies import MomentumStrategy

strategy = MomentumStrategy(
    lookback_period=252,  # 12개월 룩백
    skip_recent=20        # 최근 1개월 제외
)

# 사용
signals = strategy.generate_signals(data)
selected = strategy.select_stocks(signals, top_n=20)
```

**시그널 계산:**
```
모멘텀 = (P[t-20] / P[t-272]) - 1
순위 = rank_normalize(모멘텀)
선정 = 순위 상위 N개
```

#### 밸류 전략 (ValueStrategy)

```python
from src.strategies import ValueStrategy

strategy = ValueStrategy(
    use_pbr=True,
    use_per=True
)

signals = strategy.generate_signals(data)
selected = strategy.select_stocks(signals, top_n=20)
```

**시그널 계산:**
```
PBR 스코어 = 1 / PBR
PER 스코어 = 1 / PER (양수만)
밸류 스코어 = (PBR 스코어 순위 + PER 스코어 순위) / 2
선정 = 밸류 스코어 상위 N개
```

#### 퀄리티 전략 (QualityStrategy)

```python
from src.strategies import QualityStrategy

strategy = QualityStrategy(
    use_roe=True,
    use_debt_ratio=True
)

signals = strategy.generate_signals(data)
selected = strategy.select_stocks(signals, top_n=20)
```

**시그널 계산:**
```
ROE 스코어 = rank_normalize(ROE)
부채 스코어 = rank_normalize(1 / (1 + 부채비율))
퀄리티 스코어 = (ROE 스코어 + 부채 스코어) / 2
선정 = 퀄리티 스코어 상위 N개
```

#### 멀티팩터 전략 (MultiFactorStrategy)

```python
from src.strategies import MultiFactorStrategy

strategy = MultiFactorStrategy(
    momentum_weight=0.4,
    value_weight=0.3,
    quality_weight=0.2,
    size_weight=0.1
)

signals = strategy.generate_signals(data)
selected = strategy.select_stocks(signals, top_n=20)
```

**복합 스코어 계산:**
```
복합 스코어 = 0.4 × 모멘텀 순위
           + 0.3 × 밸류 순위
           + 0.2 × 퀄리티 순위
           + 0.1 × 사이즈 순위
선정 = 복합 스코어 상위 N개
```

#### 사이즈 전략 (SizeStrategy)

```python
from src.strategies import SizeStrategy

strategy = SizeStrategy()
signals = strategy.generate_signals(data)
selected = strategy.select_stocks(signals, top_n=20)
```

**시그널 계산:**
```
사이즈 스코어 = -log(시가총액)
선정 = 사이즈 스코어 상위 N개 (소형주)
```

### 3. 전략 팩토리

```python
from src.strategies import create_strategy

# 전략 이름으로 생성
strategy = create_strategy('momentum')
strategy = create_strategy('value')
strategy = create_strategy('quality')
strategy = create_strategy('multifactor')
strategy = create_strategy('size')
```

---

## 백테스트 실행

### 기본 백테스트

```python
from src.backtesting import Backtester
from src.strategies import create_strategy

# 1. 전략 생성
strategy = create_strategy('multifactor')

# 2. 백테스터 설정
backtester = Backtester(
    strategy=strategy,
    initial_capital=100_000_000,  # 1억원
    commission=0.0015,            # 0.15% 수수료
    slippage=0.001,               # 0.1% 슬리피지
    rebalance_frequency='monthly' # 월간 리밸런싱
)

# 3. 백테스트 실행
results = backtester.run(
    start_date='2018-01-01',
    end_date='2023-12-31'
)

# 4. 결과 확인
print(f"총 수익률: {results['total_return']:.2%}")
print(f"연환산 수익률: {results['annual_return']:.2%}")
print(f"샤프 비율: {results['sharpe_ratio']:.2f}")
print(f"최대 낙폭: {results['max_drawdown']:.2%}")
```

### 백테스트 파라미터

| 파라미터 | 설명 | 기본값 |
|----------|------|--------|
| `initial_capital` | 초기 투자금 | 100,000,000 |
| `commission` | 거래 수수료율 | 0.0015 (0.15%) |
| `slippage` | 슬리피지율 | 0.001 (0.1%) |
| `rebalance_frequency` | 리밸런싱 주기 | 'monthly' |
| `max_positions` | 최대 보유 종목 수 | 20 |
| `min_positions` | 최소 보유 종목 수 | 5 |

### 리밸런싱 주기 옵션

| 옵션 | 설명 | 연간 리밸런싱 횟수 |
|------|------|-------------------|
| `'daily'` | 매일 | ~252회 |
| `'weekly'` | 매주 | ~52회 |
| `'monthly'` | 매월 | 12회 |
| `'quarterly'` | 분기별 | 4회 |

---

## 거래 비용 모델링

### 1. 수수료 (Commission)

```python
# 매수 비용
buy_cost = shares × buy_price × (1 + commission)

# 매도 수익
sell_proceeds = shares × sell_price × (1 - commission)
```

**한국 주식 실제 비용:**
| 항목 | 비율 |
|------|------|
| 증권사 수수료 | 0.015% ~ 0.5% |
| 증권거래세 | 0.23% (매도 시) |
| 유관기관 수수료 | 0.00363% |
| **총 비용 (편도)** | 약 0.15% ~ 0.25% |

### 2. 슬리피지 (Slippage)

시장가 주문 시 예상 가격과 실제 체결 가격의 차이:

```python
# 매수 시 불리한 가격
actual_buy_price = expected_price × (1 + slippage)

# 매도 시 불리한 가격
actual_sell_price = expected_price × (1 - slippage)
```

**슬리피지 요인:**
- 호가 스프레드
- 시장 충격 (Market Impact)
- 주문 크기
- 시장 유동성

### 3. 비용 설정 예시

```python
# 보수적 설정 (실제 비용 반영)
backtester = Backtester(
    commission=0.0025,  # 0.25% (수수료 + 거래세)
    slippage=0.002      # 0.2%
)

# 공격적 설정 (비용 최소화 가정)
backtester = Backtester(
    commission=0.001,   # 0.1%
    slippage=0.0005     # 0.05%
)
```

---

## 결과 분석

### 1. 수익률 곡선 분석

```python
import matplotlib.pyplot as plt

# 포트폴리오 가치 시계열
portfolio_values = results['portfolio_values']

plt.figure(figsize=(12, 6))
plt.plot(portfolio_values.index, portfolio_values.values)
plt.title('Portfolio Value Over Time')
plt.xlabel('Date')
plt.ylabel('Portfolio Value')
plt.show()
```

### 2. 낙폭 분석

```python
# 낙폭 시계열
drawdowns = results['drawdowns']

plt.figure(figsize=(12, 4))
plt.fill_between(drawdowns.index, drawdowns.values, 0, alpha=0.5, color='red')
plt.title('Drawdown Over Time')
plt.ylabel('Drawdown')
plt.show()
```

### 3. 월간 수익률 히트맵

```python
import seaborn as sns

# 월간 수익률 테이블
monthly_returns = results['monthly_returns']
monthly_pivot = monthly_returns.pivot_table(
    index=monthly_returns.index.year,
    columns=monthly_returns.index.month,
    values='return'
)

plt.figure(figsize=(12, 8))
sns.heatmap(monthly_pivot, annot=True, fmt='.2%', cmap='RdYlGn', center=0)
plt.title('Monthly Returns Heatmap')
plt.show()
```

### 4. 거래 분석

```python
# 거래 로그
trades = results['trades']

print(f"총 거래 횟수: {len(trades)}")
print(f"매수 거래: {len(trades[trades['action'] == 'BUY'])}")
print(f"매도 거래: {len(trades[trades['action'] == 'SELL'])}")
print(f"평균 보유 기간: {trades['holding_period'].mean():.1f}일")
```

### 5. 벤치마크 비교

```python
# 벤치마크 대비 분석
benchmark_returns = get_benchmark_returns('KOSPI')

# 초과 수익률
excess_return = results['annual_return'] - benchmark_returns.mean()

# 정보 비율
tracking_error = (results['returns'] - benchmark_returns).std() * np.sqrt(252)
information_ratio = excess_return / tracking_error

print(f"벤치마크 대비 초과 수익: {excess_return:.2%}")
print(f"정보 비율: {information_ratio:.2f}")
```

---

## 주의사항 및 한계

### 1. 생존 편향 (Survivorship Bias)

**문제:** 상장폐지된 종목이 제외되어 수익률 과대평가

**해결책:**
- 상장폐지 종목 포함 데이터 사용
- 종목 필터에 유동성 조건 추가

```python
# 유동성 필터로 위험 종목 제외
strategy.add_filter('avg_volume', '>', 100000)
strategy.add_filter('market_cap', '>', 50e9)  # 500억 이상
```

### 2. 미래 정보 편향 (Look-Ahead Bias)

**문제:** 백테스트 시점에 알 수 없는 정보 사용

**대표적 사례:**
- 실적 발표 전 재무제표 사용
- Point-in-Time 데이터 미사용

**해결책:**
- 데이터 시점 엄격히 관리
- 재무 데이터는 발표일 기준 적용

### 3. 데이터 스누핑 (Data Snooping)

**문제:** 과도한 파라미터 최적화로 과적합

**해결책:**
- In-sample / Out-of-sample 분리
- Walk-forward 분석
- 단순한 전략 선호

```python
# Walk-forward 백테스트
for train_end, test_start, test_end in walk_forward_periods:
    # 학습 기간으로 파라미터 최적화
    params = optimize(data[: train_end])

    # 테스트 기간으로 성과 검증
    test_results = backtest(data[test_start:test_end], params)
```

### 4. 거래 비용 과소평가

**문제:** 실제보다 낮은 거래 비용 가정

**해결책:**
- 보수적 비용 설정
- 시장 충격 고려

```python
# 보수적 비용 설정
backtester = Backtester(
    commission=0.003,   # 0.3%
    slippage=0.003      # 0.3%
)
```

### 5. 유동성 무시

**문제:** 대량 주문의 시장 충격 무시

**해결책:**
- 포지션 크기 제한
- 유동성 필터 적용

```python
# 일일 거래량의 10% 이하로 제한
max_position = daily_volume * close_price * 0.10
```

---

## 고급 활용법

### 1. 커스텀 팩터 추가

```python
from src.data_processing.feature_engineering import FactorCalculator

class EnhancedMultiFactorStrategy(MultiFactorStrategy):
    def generate_signals(self, data):
        signals = super().generate_signals(data)

        # 커스텀 팩터 추가
        if 'f_score' in data.columns:
            signals['f_score_rank'] = data.groupby('date')['f_score'].transform(
                lambda x: x.rank(pct=True)
            )

        # 복합 스코어 재계산
        signals['enhanced_score'] = (
            signals['composite_score'] * 0.8 +
            signals['f_score_rank'] * 0.2
        )

        return signals
```

### 2. 동적 가중치 조절

```python
def get_dynamic_weights(market_regime):
    """시장 국면에 따른 팩터 가중치 조절"""
    if market_regime == 'bull':
        return {
            'momentum': 0.5,
            'value': 0.2,
            'quality': 0.2,
            'size': 0.1
        }
    elif market_regime == 'bear':
        return {
            'momentum': 0.1,
            'value': 0.4,
            'quality': 0.4,
            'size': 0.1
        }
    else:
        return {
            'momentum': 0.3,
            'value': 0.3,
            'quality': 0.3,
            'size': 0.1
        }
```

### 3. 섹터 중립 전략

```python
def sector_neutral_selection(data, top_n_per_sector=3):
    """각 섹터에서 동일 수의 종목 선택"""
    selected = []

    for sector in data['sector'].unique():
        sector_data = data[data['sector'] == sector]
        top_in_sector = sector_data.nlargest(top_n_per_sector, 'composite_score')
        selected.extend(top_in_sector['symbol'].tolist())

    return selected
```

### 4. 리스크 패리티 가중치

```python
def risk_parity_weights(returns_df):
    """리스크 패리티 방식 가중치 계산"""
    volatilities = returns_df.std()
    inverse_vol = 1 / volatilities
    weights = inverse_vol / inverse_vol.sum()
    return weights
```

### 5. 최적화 백테스트

```python
from itertools import product

# 파라미터 그리드
momentum_weights = [0.2, 0.3, 0.4, 0.5]
value_weights = [0.2, 0.3, 0.4]
rebalance_freqs = ['monthly', 'quarterly']

results_grid = []

for mw, vw, rf in product(momentum_weights, value_weights, rebalance_freqs):
    qw = 1 - mw - vw - 0.1  # size weight = 0.1

    strategy = MultiFactorStrategy(
        momentum_weight=mw,
        value_weight=vw,
        quality_weight=qw,
        size_weight=0.1
    )

    backtester = Backtester(strategy=strategy, rebalance_frequency=rf)
    result = backtester.run()

    results_grid.append({
        'momentum_weight': mw,
        'value_weight': vw,
        'quality_weight': qw,
        'rebalance_freq': rf,
        'sharpe': result['sharpe_ratio'],
        'return': result['annual_return']
    })

# 최적 파라미터 찾기
best_result = max(results_grid, key=lambda x: x['sharpe'])
```

---

## 참고

- [데이터 수집 가이드](./13-data-collection.md)
- [스크리닝 가이드](./14-screening.md)
- [전략 개발 API](./api-reference.md#strategies)
