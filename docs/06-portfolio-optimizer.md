# 06. 포트폴리오 최적화 (Portfolio Optimization)

포트폴리오 가중치를 최적화하는 방법에 대한 매뉴얼입니다.

## 목차

1. [개요](#개요)
2. [PortfolioOptimizer 클래스](#portfoliooptimizer-클래스)
3. [최적화 방법](#최적화-방법)
4. [포트폴리오 메트릭](#포트폴리오-메트릭)
5. [설정 항목](#설정-항목)
6. [예제 코드](#예제-코드)

---

## 개요

**파일 위치**: `src/portfolio/portfolio_optimizer.py`

포트폴리오 최적화는 주어진 종목들의 비중을 결정하여 위험 대비 수익을 최대화하는 과정입니다.

### 지원하는 최적화 방법

| 방법 | 목표 | 특징 |
|------|------|------|
| 동일 가중 | 단순 분산 | 구현 간단, 재조정 빈번 |
| 최대 샤프 비율 | 위험조정수익 최대화 | 가장 일반적 |
| 최소 변동성 | 위험 최소화 | 보수적 투자 |
| 최대 수익률 | 수익 최대화 | 공격적 투자 |

---

## PortfolioOptimizer 클래스

### 초기화

```python
from src.portfolio.portfolio_optimizer import PortfolioOptimizer
import pandas as pd

# 가격 데이터 준비 (종목별 종가)
prices = pd.DataFrame({
    '005930': [...],  # 삼성전자
    '000660': [...],  # SK하이닉스
    '035420': [...],  # NAVER
}, index=dates)

# 최적화기 초기화
optimizer = PortfolioOptimizer(
    prices=prices,
    risk_free_rate=0.03  # 연 3% 무위험 수익률
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `prices` | DataFrame | 필수 | 종목별 가격 데이터 (columns: 종목, index: 날짜) |
| `risk_free_rate` | float | 0.02 | 연간 무위험 수익률 |

### 내부 속성

```python
# 초기화 시 자동 계산
optimizer.prices      # 원본 가격 데이터
optimizer.returns     # 일간 수익률 (pct_change)
optimizer.assets      # 종목 리스트
optimizer.n_assets    # 종목 수
```

---

## 최적화 방법

### 1. 동일 가중 (Equal Weight)

가장 단순한 방법으로, 모든 종목에 동일한 비중을 부여합니다.

```python
weights = optimizer.optimize_equal_weights()
print(weights)
# {'005930': 0.333, '000660': 0.333, '035420': 0.333}
```

**장점**:
- 구현이 간단
- 모델 리스크 없음
- 재조정이 용이

**단점**:
- 위험/수익 최적화 없음
- 대형주와 소형주 동일 취급

---

### 2. 평균-분산 최적화 (Mean-Variance Optimization)

Markowitz의 현대 포트폴리오 이론에 기반한 최적화입니다.

```python
weights = optimizer.optimize_mean_variance(objective='sharpe')
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `objective` | str | 'sharpe' | 최적화 목표 |

#### 최적화 목표 옵션

##### `objective='sharpe'` - 최대 샤프 비율

위험 대비 수익을 최대화합니다.

```python
weights = optimizer.optimize_mean_variance(objective='sharpe')
```

**수학적 정의**:
```
최대화: (포트폴리오 수익률 - 무위험수익률) / 포트폴리오 변동성
```

##### `objective='min_volatility'` - 최소 변동성

포트폴리오 전체 변동성을 최소화합니다.

```python
weights = optimizer.optimize_mean_variance(objective='min_volatility')
```

**수학적 정의**:
```
최소화: √(w'Σw)
where w = 가중치 벡터, Σ = 공분산 행렬
```

**특징**:
- 보수적 투자자에게 적합
- 낮은 상관관계 종목 선호
- 수익률보다 안정성 중시

##### `objective='max_return'` - 최대 수익률

기대 수익률을 최대화합니다.

```python
weights = optimizer.optimize_mean_variance(objective='max_return')
```

**수학적 정의**:
```
최대화: w'μ
where w = 가중치 벡터, μ = 기대수익률 벡터
```

**주의**: 과거 수익률 기반이므로 과적합 위험이 있습니다.

---

### 3. 최적화 제약 조건

모든 최적화에는 다음 제약이 적용됩니다:

```python
# 제약 조건
constraints = {
    'type': 'eq',
    'fun': lambda x: np.sum(x) - 1  # 가중치 합 = 1
}

# 범위 (공매도 금지)
bounds = tuple((0, 1) for _ in range(n_assets))  # 0 ≤ w_i ≤ 1
```

---

## 포트폴리오 메트릭

### `get_portfolio_metrics()` - 성과 지표 계산

주어진 가중치로 포트폴리오의 예상 성과를 계산합니다.

```python
weights = {'005930': 0.5, '000660': 0.3, '035420': 0.2}
metrics = optimizer.get_portfolio_metrics(weights)

print(metrics)
# {
#     'expected_return': 0.15,   # 예상 연간 수익률 (15%)
#     'volatility': 0.20,        # 예상 연간 변동성 (20%)
#     'sharpe_ratio': 0.60       # 샤프 비율
# }
```

| 메트릭 | 설명 |
|--------|------|
| `expected_return` | 연간 기대 수익률 (과거 데이터 기반) |
| `volatility` | 연간 변동성 (표준편차) |
| `sharpe_ratio` | (기대수익률 - 무위험수익률) / 변동성 |

---

## 효율적 프론티어

효율적 프론티어는 주어진 위험 수준에서 최대 수익률을 달성하는 포트폴리오의 집합입니다.

```python
import numpy as np
import matplotlib.pyplot as plt

# 효율적 프론티어 계산
def get_efficient_frontier(optimizer, n_points=100):
    results = []

    for target_return in np.linspace(0.05, 0.30, n_points):
        try:
            # 목표 수익률 제약 추가하여 최적화
            # (커스텀 구현 필요)
            pass
        except:
            continue

    return results

# 시각화
returns = [r['return'] for r in results]
volatilities = [r['volatility'] for r in results]

plt.figure(figsize=(10, 6))
plt.scatter(volatilities, returns, c='blue', marker='o')
plt.xlabel('Volatility')
plt.ylabel('Expected Return')
plt.title('Efficient Frontier')
plt.show()
```

---

## 설정 항목

`config/config.yaml` 파일의 관련 설정:

```yaml
strategy:
  # 포트폴리오 설정
  max_positions: 20              # 최대 보유 종목 수
  min_positions: 10              # 최소 보유 종목 수
  equal_weight: true             # 동일 가중 여부
  max_position_size: 0.1         # 최대 개별 종목 비중 (10%)

backtesting:
  risk_free_rate: 0.03           # 무위험 수익률 (연 3%)
```

### 설정값 사용

```python
from src.utils.config_loader import get_config

config = get_config()

# 포트폴리오 설정
max_positions = config.get('strategy.max_positions', 20)
max_position_size = config.get('strategy.max_position_size', 0.1)

# 무위험 수익률
risk_free_rate = config.get('backtesting.risk_free_rate', 0.03)
```

---

## 예제 코드

### 예제 1: 기본 최적화

```python
from src.portfolio.portfolio_optimizer import PortfolioOptimizer
from src.utils.database import get_db
import pandas as pd

# 데이터 로드
db = get_db()
symbols = ['005930', '000660', '035420', '051910', '006400']
price_data = db.get_stock_prices(symbol=symbols, start_date='2022-01-01')

# 피벗 테이블로 변환 (종목별 종가)
prices = price_data.pivot(index='date', columns='symbol', values='close')

# 결측치 처리
prices = prices.dropna()

# 최적화기 초기화
optimizer = PortfolioOptimizer(prices, risk_free_rate=0.03)

# 동일 가중
eq_weights = optimizer.optimize_equal_weights()
eq_metrics = optimizer.get_portfolio_metrics(eq_weights)

# 최대 샤프 비율
sharpe_weights = optimizer.optimize_mean_variance(objective='sharpe')
sharpe_metrics = optimizer.get_portfolio_metrics(sharpe_weights)

# 최소 변동성
minvol_weights = optimizer.optimize_mean_variance(objective='min_volatility')
minvol_metrics = optimizer.get_portfolio_metrics(minvol_weights)

# 결과 비교
print("=" * 60)
print("포트폴리오 최적화 결과 비교")
print("=" * 60)

for name, (weights, metrics) in [
    ("동일 가중", (eq_weights, eq_metrics)),
    ("최대 샤프", (sharpe_weights, sharpe_metrics)),
    ("최소 변동성", (minvol_weights, minvol_metrics))
]:
    print(f"\n{name}:")
    print(f"  기대 수익률: {metrics['expected_return']:.2%}")
    print(f"  변동성: {metrics['volatility']:.2%}")
    print(f"  샤프 비율: {metrics['sharpe_ratio']:.2f}")
    print(f"  비중: {weights}")
```

### 예제 2: 전략과 최적화 결합

```python
from src.strategies.quant_strategies import create_strategy
from src.portfolio.portfolio_optimizer import PortfolioOptimizer

# 모멘텀 전략으로 종목 선정
strategy = create_strategy('momentum')
signals = strategy.generate_signals(data)

# 최신 날짜의 상위 10개 종목 선정
latest_data = signals[signals['date'] == signals['date'].max()]
selected_stocks = strategy.select_stocks(latest_data, top_n=10)

# 선정된 종목의 가격 데이터 추출
selected_prices = prices[selected_stocks]

# 포트폴리오 최적화
optimizer = PortfolioOptimizer(selected_prices)
optimal_weights = optimizer.optimize_mean_variance(objective='sharpe')

print("최적 포트폴리오 가중치:")
for symbol, weight in sorted(optimal_weights.items(), key=lambda x: -x[1]):
    if weight > 0.001:  # 0.1% 이상만 표시
        print(f"  {symbol}: {weight:.2%}")
```

### 예제 3: 위치 제한 적용

```python
from src.strategies.base_strategy import BaseStrategy

# 전략의 apply_position_limits 메서드 사용
class ConstrainedOptimization:

    @staticmethod
    def apply_constraints(weights, max_weight=0.1):
        """개별 종목 비중 제한"""
        constrained = {}
        excess = 0

        # 1단계: 최대 비중 적용
        for symbol, weight in weights.items():
            if weight > max_weight:
                constrained[symbol] = max_weight
                excess += weight - max_weight
            else:
                constrained[symbol] = weight

        # 2단계: 초과분 재분배
        eligible = {k: v for k, v in constrained.items() if v < max_weight}
        if eligible and excess > 0:
            redistribution = excess / len(eligible)
            for symbol in eligible:
                constrained[symbol] = min(constrained[symbol] + redistribution, max_weight)

        # 3단계: 정규화
        total = sum(constrained.values())
        return {k: v / total for k, v in constrained.items()}

# 사용
optimal_weights = optimizer.optimize_mean_variance(objective='sharpe')
constrained_weights = ConstrainedOptimization.apply_constraints(
    optimal_weights,
    max_weight=0.15  # 최대 15%
)

print("제약 적용 후 가중치:")
print(constrained_weights)
```

### 예제 4: 여러 최적화 결과 비교 시각화

```python
import matplotlib.pyplot as plt
import numpy as np

# 최적화 결과
methods = {
    'Equal Weight': optimizer.optimize_equal_weights(),
    'Max Sharpe': optimizer.optimize_mean_variance('sharpe'),
    'Min Volatility': optimizer.optimize_mean_variance('min_volatility'),
}

# 메트릭 계산
results = {}
for name, weights in methods.items():
    metrics = optimizer.get_portfolio_metrics(weights)
    results[name] = {
        'return': metrics['expected_return'],
        'volatility': metrics['volatility'],
        'sharpe': metrics['sharpe_ratio']
    }

# 시각화
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# 수익률 vs 변동성
ax1 = axes[0]
for name, r in results.items():
    ax1.scatter(r['volatility'], r['return'], s=100, label=name)
ax1.set_xlabel('Volatility')
ax1.set_ylabel('Expected Return')
ax1.set_title('Risk-Return Profile')
ax1.legend()

# 샤프 비율 비교
ax2 = axes[1]
names = list(results.keys())
sharpes = [results[n]['sharpe'] for n in names]
ax2.bar(names, sharpes, color=['blue', 'green', 'orange'])
ax2.set_ylabel('Sharpe Ratio')
ax2.set_title('Sharpe Ratio Comparison')
ax2.tick_params(axis='x', rotation=45)

# 가중치 분포
ax3 = axes[2]
x = np.arange(len(optimizer.assets))
width = 0.25

for i, (name, weights) in enumerate(methods.items()):
    weights_list = [weights.get(a, 0) for a in optimizer.assets]
    ax3.bar(x + i*width, weights_list, width, label=name)

ax3.set_ylabel('Weight')
ax3.set_title('Weight Distribution')
ax3.set_xticks(x + width)
ax3.set_xticklabels(optimizer.assets, rotation=45)
ax3.legend()

plt.tight_layout()
plt.savefig('portfolio_optimization_comparison.png', dpi=300)
plt.show()
```

---

## 주의사항

1. **과거 데이터의 한계**: 최적화는 과거 데이터에 기반하므로 미래 성과를 보장하지 않습니다.

2. **추정 오차**: 기대 수익률과 공분산 추정에 오차가 있을 수 있습니다.

3. **집중 리스크**: 최적화 결과가 특정 종목에 집중될 수 있으므로 비중 제한이 필요합니다.

4. **재조정 비용**: 빈번한 재조정은 거래 비용을 증가시킵니다.

5. **소수점 주의**: 가중치 합이 정확히 1.0이 되도록 반올림에 주의합니다.

---

## 다음 단계

- [07. 백테스팅](./07-backtesting.md) - 포트폴리오 전략 시뮬레이션
- [08. 설정 파일](./08-configuration.md) - 상세 설정 방법
