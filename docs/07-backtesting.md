# 07. 백테스팅 (Backtesting)

투자 전략의 과거 성과를 시뮬레이션하는 방법에 대한 매뉴얼입니다.

## 목차

1. [개요](#개요)
2. [Backtester 클래스](#backtester-클래스)
3. [성과 지표](#성과-지표)
4. [시각화](#시각화)
5. [설정 항목](#설정-항목)
6. [예제 코드](#예제-코드)

---

## 개요

**파일 위치**:
- `src/backtesting/backtester.py` - 백테스팅 엔진
- `src/backtesting/performance_metrics.py` - 성과 지표 계산
- `src/backtesting/visualizer.py` - 결과 시각화

백테스팅은 과거 데이터를 사용하여 투자 전략의 성과를 시뮬레이션하는 과정입니다.

### 백테스팅 프로세스

```
1. 전략 생성
      ↓
2. 데이터 준비
      ↓
3. 리밸런싱 날짜 계산
      ↓
4. 각 날짜별 반복:
   - 리밸런싱 날짜인 경우:
     a. 신호 생성
     b. 종목 선정
     c. 거래 실행 (매수/매도)
   - 포트폴리오 가치 계산
      ↓
5. 성과 지표 계산
      ↓
6. 결과 시각화
```

---

## Backtester 클래스

### 초기화

```python
from src.backtesting.backtester import Backtester
from src.strategies.quant_strategies import create_strategy

# 전략 생성
strategy = create_strategy('momentum')

# 백테스터 초기화
backtester = Backtester(
    strategy=strategy,
    initial_capital=100000000,  # 1억 원
    commission=0.0015,          # 0.15% 수수료
    slippage=0.001              # 0.1% 슬리피지
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `strategy` | BaseStrategy | 필수 | 투자 전략 객체 |
| `initial_capital` | float | 100,000,000 | 초기 자본금 |
| `commission` | float | 0.0015 | 거래 수수료 (0.15%) |
| `slippage` | float | 0.001 | 슬리피지 (0.1%) |

### 비용 계산

```
매수 비용 = 주식수 × 매수가 × (1 + slippage) × (1 + commission)
매도 수익 = 주식수 × 매도가 × (1 - slippage) × (1 - commission)
```

---

### `run()` - 백테스트 실행

```python
results = backtester.run(
    data=df,
    start_date='2020-01-01',
    end_date='2023-12-31',
    rebalance_frequency='monthly'
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `data` | DataFrame | 필수 | 주식 데이터 |
| `start_date` | datetime/str | None | 백테스트 시작일 |
| `end_date` | datetime/str | None | 백테스트 종료일 |
| `rebalance_frequency` | str | 'monthly' | 리밸런싱 주기 |

**리밸런싱 주기 옵션**:
| 주기 | 설명 |
|------|------|
| `'daily'` | 매일 |
| `'weekly'` | 매주 |
| `'monthly'` | 매월 |
| `'quarterly'` | 매분기 |

**반환값**: DataFrame

```python
# 결과 컬럼
results.columns
# ['portfolio_value', 'cash', 'n_positions', 'returns', 'cumulative_returns']
```

| 컬럼 | 설명 |
|------|------|
| `portfolio_value` | 총 포트폴리오 가치 |
| `cash` | 현금 보유량 |
| `n_positions` | 보유 종목 수 |
| `returns` | 일간 수익률 |
| `cumulative_returns` | 누적 수익률 |

---

### `get_trades_df()` - 거래 내역 조회

```python
trades = backtester.get_trades_df()
print(trades)
```

**반환값**: DataFrame

| 컬럼 | 설명 |
|------|------|
| `date` | 거래 날짜 |
| `symbol` | 종목 코드 |
| `action` | 거래 유형 ('BUY' 또는 'SELL') |
| `shares` | 거래 주수 |
| `price` | 거래 가격 |
| `value` | 거래 금액 |

---

### `get_summary()` - 성과 요약

```python
summary = backtester.get_summary()

for key, value in summary.items():
    print(f"{key}: {value}")
```

**반환값**: Dictionary

| 키 | 설명 |
|------|------|
| `initial_capital` | 초기 자본금 |
| `final_value` | 최종 포트폴리오 가치 |
| `total_return` | 총 수익률 |
| `annual_return` | 연환산 수익률 (CAGR) |
| `volatility` | 연환산 변동성 |
| `sharpe_ratio` | 샤프 비율 |
| `max_drawdown` | 최대 낙폭 |
| `calmar_ratio` | 칼마 비율 |
| `win_rate` | 승률 |
| `n_trades` | 총 거래 횟수 |

---

## 편의 함수: `run_backtest()`

백테스팅을 한 번에 실행하는 편의 함수입니다.

```python
from src.backtesting.backtester import run_backtest

results, summary = run_backtest(
    strategy=strategy,
    data=data,
    start_date='2020-01-01',
    end_date='2023-12-31',
    initial_capital=100000000,
    commission=0.0015,
    slippage=0.001,
    rebalance_frequency='monthly'
)
```

**반환값**: Tuple (결과 DataFrame, 요약 Dictionary)

---

## 성과 지표

### PerformanceMetrics 클래스

**파일 위치**: `src/backtesting/performance_metrics.py`

```python
from src.backtesting.performance_metrics import PerformanceMetrics

# 성과 지표 계산기 초기화
metrics = PerformanceMetrics(
    portfolio_df=results,
    risk_free_rate=0.03  # 연 3%
)
```

### 개별 지표

#### 수익률 지표

```python
# 총 수익률
total_return = metrics.total_return()
# 0.45 (45%)

# 연환산 수익률 (CAGR)
annual_return = metrics.annual_return()
# 0.12 (연 12%)

# 월간 수익률
monthly_returns = metrics.monthly_returns()
```

#### 위험 지표

```python
# 연환산 변동성
volatility = metrics.volatility(annualized=True)
# 0.18 (18%)

# 최대 낙폭 (MDD)
max_drawdown = metrics.max_drawdown()
# 0.25 (25%)

# VaR (Value at Risk) - 95% 신뢰수준
var_95 = metrics.value_at_risk(confidence_level=0.95)
# 0.02 (일일 2%)

# CVaR (Expected Shortfall)
cvar_95 = metrics.conditional_value_at_risk(confidence_level=0.95)
# 0.03 (일일 3%)
```

#### 위험조정 수익률

```python
# 샤프 비율
sharpe_ratio = metrics.sharpe_ratio()
# 0.75

# 소르티노 비율 (하방 위험만 고려)
sortino_ratio = metrics.sortino_ratio()
# 1.10

# 칼마 비율 (연수익률 / MDD)
calmar_ratio = metrics.calmar_ratio()
# 0.48

# 정보 비율 (벤치마크 대비)
info_ratio = metrics.information_ratio(benchmark_returns)
# 0.35
```

#### 기타 지표

```python
# 승률
win_rate = metrics.win_rate()
# 0.52 (52%)

# 손익비
profit_factor = metrics.profit_factor()
# 1.35
```

### 모든 지표 한번에 조회

```python
all_metrics = metrics.get_all_metrics()
print(all_metrics)
# {
#     'Total Return': 0.45,
#     'Annual Return': 0.12,
#     'Volatility': 0.18,
#     'Sharpe Ratio': 0.75,
#     ...
# }
```

### 성과 요약 출력

```python
metrics.print_summary()

# 출력:
# ==================================================
# PERFORMANCE SUMMARY
# ==================================================
# Total Return.....................     45.00%
# Annual Return....................     12.00%
# Volatility.......................     18.00%
# Sharpe Ratio.....................       0.75
# ...
# ==================================================
```

### 전략 비교

```python
from src.backtesting.performance_metrics import compare_strategies

# 여러 전략 결과 비교
comparison = compare_strategies(
    results_dict={
        'Momentum': momentum_results,
        'Value': value_results,
        'MultiF': multi_results
    },
    risk_free_rate=0.03
)

print(comparison)
```

---

## 시각화

### BacktestVisualizer 클래스

**파일 위치**: `src/backtesting/visualizer.py`

```python
from src.backtesting.visualizer import BacktestVisualizer

# 시각화기 초기화
viz = BacktestVisualizer(results)
```

### 개별 차트

#### 포트폴리오 가치 차트

```python
viz.plot_portfolio_value(
    benchmark=benchmark_series,  # 선택사항
    save_path='portfolio_value.png'  # 선택사항
)
```

#### 누적 수익률 차트

```python
viz.plot_cumulative_returns(
    benchmark_returns=benchmark_returns,  # 선택사항
    save_path='cumulative_returns.png'
)
```

#### 낙폭 차트

```python
viz.plot_drawdown(save_path='drawdown.png')
```

#### 월간 수익률 히트맵

```python
viz.plot_monthly_returns_heatmap(save_path='monthly_heatmap.png')
```

#### 수익률 분포 차트

```python
viz.plot_return_distribution(save_path='return_distribution.png')
```

#### 롤링 샤프 비율

```python
viz.plot_rolling_sharpe(
    window=252,  # 1년
    save_path='rolling_sharpe.png'
)
```

### 전체 리포트 생성

```python
# 모든 차트를 한번에 생성
viz.create_full_report(save_dir='backtest_results/')
```

### 전략 비교 차트

```python
from src.backtesting.visualizer import compare_strategies_plot

compare_strategies_plot(
    results_dict={
        'Momentum': momentum_results,
        'Value': value_results,
        'MultiF': multi_results
    },
    save_path='strategy_comparison.png'
)
```

---

## 설정 항목

`config/config.yaml` 파일의 `backtesting` 섹션:

```yaml
backtesting:
  initial_capital: 100000000   # 초기 자본금 (1억 원)
  commission: 0.0015           # 거래 수수료 (0.15%)
  slippage: 0.001              # 슬리피지 (0.1%)

  # 성과 평가
  benchmark: "SPY"             # 벤치마크 (SPY, KOSPI 등)
  risk_free_rate: 0.03         # 무위험 수익률 (연 3%)
```

### 설정값 사용

```python
from src.utils.config_loader import get_config

config = get_config()
backtest_config = config.get_backtesting_config()

initial_capital = backtest_config.get('initial_capital', 100000000)
commission = backtest_config.get('commission', 0.0015)
risk_free_rate = backtest_config.get('risk_free_rate', 0.03)
```

---

## 예제 코드

### 예제 1: 기본 백테스팅

```python
from src.strategies.quant_strategies import create_strategy
from src.backtesting.backtester import run_backtest
from src.utils.database import get_db

# 데이터 로드
db = get_db()
data = db.get_stock_prices(start_date='2019-01-01')

# 펀더멘털 데이터 병합
fundamentals = db.get_fundamentals(start_date='2019-01-01')
data = data.merge(fundamentals, on=['symbol', 'date'], how='left')

# 전략 생성
strategy = create_strategy('multifactor')

# 백테스팅 실행
results, summary = run_backtest(
    strategy=strategy,
    data=data,
    start_date='2020-01-01',
    end_date='2023-12-31',
    initial_capital=100000000,
    commission=0.0015,
    slippage=0.001,
    rebalance_frequency='monthly'
)

# 결과 출력
print("\n=== 백테스팅 결과 ===")
print(f"초기 자본금: {summary['initial_capital']:,.0f} 원")
print(f"최종 가치: {summary['final_value']:,.0f} 원")
print(f"총 수익률: {summary['total_return']:.2%}")
print(f"연 수익률: {summary['annual_return']:.2%}")
print(f"변동성: {summary['volatility']:.2%}")
print(f"샤프 비율: {summary['sharpe_ratio']:.2f}")
print(f"최대 낙폭: {summary['max_drawdown']:.2%}")
print(f"총 거래 횟수: {summary['n_trades']}")
```

### 예제 2: 여러 전략 비교

```python
from src.strategies.quant_strategies import create_strategy
from src.backtesting.backtester import run_backtest
from src.backtesting.performance_metrics import compare_strategies
from src.backtesting.visualizer import compare_strategies_plot

# 테스트할 전략들
strategy_names = ['momentum', 'value', 'quality', 'multifactor']

results_dict = {}
summary_dict = {}

for name in strategy_names:
    print(f"\n{name} 전략 백테스팅 중...")

    strategy = create_strategy(name)
    results, summary = run_backtest(
        strategy=strategy,
        data=data,
        initial_capital=100000000,
        rebalance_frequency='monthly'
    )

    results_dict[name] = results
    summary_dict[name] = summary

# 성과 비교 테이블
comparison = compare_strategies(results_dict, risk_free_rate=0.03)
print("\n=== 전략 비교 ===")
print(comparison.to_string())

# 비교 차트
compare_strategies_plot(results_dict, save_path='strategy_comparison.png')
```

### 예제 3: 상세 분석 및 리포트

```python
from src.backtesting.backtester import Backtester
from src.backtesting.performance_metrics import PerformanceMetrics
from src.backtesting.visualizer import BacktestVisualizer

# 백테스팅 실행
strategy = create_strategy('momentum')
backtester = Backtester(strategy, initial_capital=100000000)
results = backtester.run(data, rebalance_frequency='monthly')

# 거래 내역 확인
trades = backtester.get_trades_df()
print(f"총 거래 횟수: {len(trades)}")
print("\n최근 10개 거래:")
print(trades.tail(10))

# 상세 성과 분석
metrics = PerformanceMetrics(results, risk_free_rate=0.03)
metrics.print_summary()

# 월간 수익률 확인
monthly = metrics.monthly_returns()
print("\n월간 수익률:")
print(monthly.tail(12))

# 시각화 리포트 생성
viz = BacktestVisualizer(results)
viz.create_full_report(save_dir='backtest_report/')

print("\n리포트가 'backtest_report/' 폴더에 저장되었습니다.")
```

### 예제 4: 다양한 리밸런싱 주기 비교

```python
frequencies = ['weekly', 'monthly', 'quarterly']
freq_results = {}

for freq in frequencies:
    results, summary = run_backtest(
        strategy=create_strategy('momentum'),
        data=data,
        rebalance_frequency=freq
    )
    freq_results[freq] = {
        'return': summary['annual_return'],
        'sharpe': summary['sharpe_ratio'],
        'trades': summary['n_trades']
    }

print("\n=== 리밸런싱 주기별 성과 ===")
for freq, result in freq_results.items():
    print(f"\n{freq}:")
    print(f"  연 수익률: {result['return']:.2%}")
    print(f"  샤프 비율: {result['sharpe']:.2f}")
    print(f"  거래 횟수: {result['trades']}")
```

### 예제 5: 다양한 비용 시나리오

```python
cost_scenarios = [
    {'commission': 0.001, 'slippage': 0.0005, 'name': '낮은 비용'},
    {'commission': 0.0015, 'slippage': 0.001, 'name': '보통 비용'},
    {'commission': 0.003, 'slippage': 0.002, 'name': '높은 비용'},
]

print("\n=== 비용 시나리오별 성과 ===")
for scenario in cost_scenarios:
    results, summary = run_backtest(
        strategy=create_strategy('multifactor'),
        data=data,
        commission=scenario['commission'],
        slippage=scenario['slippage']
    )

    print(f"\n{scenario['name']} (수수료: {scenario['commission']:.2%}, 슬리피지: {scenario['slippage']:.2%}):")
    print(f"  연 수익률: {summary['annual_return']:.2%}")
    print(f"  총 거래비용 추정: {summary['n_trades'] * (scenario['commission'] + scenario['slippage']):.2%}")
```

---

## 주의사항

### 1. 생존자 편향 (Survivorship Bias)

상장폐지된 종목을 포함해야 정확한 백테스트가 가능합니다.

### 2. 미래 참조 편향 (Look-Ahead Bias)

분석 시점에 알 수 없었던 정보를 사용하면 안 됩니다.
- 펀더멘털 데이터는 발표일 기준으로 사용
- 당일 종가로 당일 거래 불가능

### 3. 과적합 (Overfitting)

과거 데이터에만 최적화된 전략은 미래에 성과가 나쁠 수 있습니다.
- Out-of-sample 테스트 필수
- 간단한 전략 선호

### 4. 거래비용

백테스트 시 거래비용을 반드시 포함해야 합니다.
- 수수료: 증권사마다 다름 (보통 0.015% ~ 0.3%)
- 슬리피지: 대형주 0.05%, 소형주 0.2%+
- 세금: 매도 시 0.23% (국내)

### 5. 유동성

거래량이 적은 종목은 백테스트보다 실제 성과가 나쁠 수 있습니다.
- 최소 거래량 필터 적용 권장

---

## 다음 단계

- [08. 설정 파일](./08-configuration.md) - 상세 설정 방법
- [09. 데이터베이스](./09-database.md) - 데이터 저장 및 관리
