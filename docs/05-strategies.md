# 05. 투자 전략 (Investment Strategies)

내장된 퀀트 투자 전략과 커스텀 전략 작성 방법에 대한 매뉴얼입니다.

## 목차

1. [전략 개요](#전략-개요)
2. [BaseStrategy 클래스](#basestrategy-클래스)
3. [내장 전략](#내장-전략)
4. [전략 팩토리 함수](#전략-팩토리-함수)
5. [커스텀 전략 작성](#커스텀-전략-작성)
6. [설정 항목](#설정-항목)
7. [예제 코드](#예제-코드)

---

## 전략 개요

**파일 위치**:
- `src/strategies/base_strategy.py` - 기본 전략 클래스
- `src/strategies/quant_strategies.py` - 퀀트 전략 구현

### 지원하는 전략

| 전략 | 클래스명 | 설명 |
|------|----------|------|
| 모멘텀 | `MomentumStrategy` | 과거 수익률 높은 종목 매수 |
| 가치 | `ValueStrategy` | 저평가 종목 매수 (낮은 PER, PBR) |
| 퀄리티 | `QualityStrategy` | 재무 건전성 좋은 종목 매수 |
| 멀티팩터 | `MultiFactorStrategy` | 여러 팩터 조합 |
| 사이즈 | `SizeStrategy` | 소형주 매수 |

---

## BaseStrategy 클래스

모든 전략의 기본이 되는 추상 클래스입니다.

### 클래스 구조

```python
from abc import ABC, abstractmethod

class BaseStrategy(ABC):

    def __init__(self, name: str, config: Dict = None):
        """전략 초기화"""

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """매매 신호 생성 (필수 구현)"""

    @abstractmethod
    def select_stocks(self, data: pd.DataFrame, top_n: int) -> List[str]:
        """종목 선정 (필수 구현)"""

    def calculate_weights(self, selected_stocks, data, method) -> Dict[str, float]:
        """포트폴리오 가중치 계산"""

    def rebalance_portfolio(self, data, current_date, current_positions) -> Dict[str, float]:
        """포트폴리오 리밸런싱"""

    def get_rebalancing_dates(self, start_date, end_date, frequency) -> List[datetime]:
        """리밸런싱 날짜 계산"""

    def filter_universe(self, data, min_market_cap, min_price, min_volume) -> pd.DataFrame:
        """투자 유니버스 필터링"""
```

### 주요 메서드

#### `generate_signals()` - 매매 신호 생성 (추상 메서드)

모든 전략에서 반드시 구현해야 합니다.

```python
# 반환 형식: 스코어 컬럼이 추가된 DataFrame
signals = strategy.generate_signals(data)
```

#### `select_stocks()` - 종목 선정 (추상 메서드)

신호를 기반으로 투자할 종목을 선정합니다.

```python
selected = strategy.select_stocks(data, top_n=20)
# 반환: ['005930', '000660', '035420', ...]
```

#### `calculate_weights()` - 가중치 계산

```python
weights = strategy.calculate_weights(
    selected_stocks=['005930', '000660'],
    data=df,
    method='equal'  # 'equal', 'market_cap', 'inverse_volatility'
)
# 반환: {'005930': 0.5, '000660': 0.5}
```

| 가중치 방식 | 설명 |
|------------|------|
| `equal` | 동일 가중 |
| `market_cap` | 시가총액 가중 |
| `inverse_volatility` | 역변동성 가중 |

#### `get_rebalancing_dates()` - 리밸런싱 날짜 계산

```python
rebal_dates = strategy.get_rebalancing_dates(
    start_date='2023-01-01',
    end_date='2024-01-01',
    frequency='monthly'  # 'daily', 'weekly', 'monthly', 'quarterly'
)
```

| 주기 | 설명 |
|------|------|
| `daily` | 매일 |
| `weekly` | 매주 금요일 |
| `monthly` | 매월 첫 영업일 |
| `quarterly` | 매분기 첫 영업일 |

#### `filter_universe()` - 유니버스 필터링

```python
filtered = strategy.filter_universe(
    data=df,
    min_market_cap=50000000000,  # 500억 원
    min_price=5000,              # 5,000원
    min_volume=100000            # 10만 주
)
```

---

## 내장 전략

### 1. MomentumStrategy (모멘텀 전략)

과거 수익률이 높은 종목을 매수하는 전략입니다.

```python
from src.strategies.quant_strategies import MomentumStrategy

strategy = MomentumStrategy(
    lookback_period=252,  # 12개월 (252 거래일)
    skip_recent=20,       # 최근 1개월 제외
    config=None           # 기본 설정 사용
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `lookback_period` | int | 252 | 모멘텀 계산 기간 |
| `skip_recent` | int | 20 | 최근 제외 기간 (단기 반전 방지) |
| `config` | Dict | None | 전략 설정 |

**신호 생성 로직**:
```python
# 12개월 수익률 (최근 1개월 제외) 기준 순위
momentum_score = (price[t-20] / price[t-272]) - 1
```

**종목 선정**:
- `momentum_rank` 기준 상위 N개 종목 선정

---

### 2. ValueStrategy (가치 전략)

저평가된 종목을 매수하는 전략입니다.

```python
from src.strategies.quant_strategies import ValueStrategy

strategy = ValueStrategy(
    use_pbr=True,   # PBR 사용 여부
    use_per=True,   # PER 사용 여부
    config=None
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `use_pbr` | bool | True | PBR 기반 가치 팩터 사용 |
| `use_per` | bool | True | PER 기반 가치 팩터 사용 |
| `config` | Dict | None | 전략 설정 |

**신호 생성 로직**:
```python
# PBR 기반: 낮을수록 높은 점수
value_pbr_score = 1 / PBR

# PER 기반: 낮을수록 높은 점수 (양수 PER만)
value_per_score = 1 / PER  (PER > 0)

# 복합 가치 스코어
value_score = mean(value_pbr_rank, value_per_rank)
```

---

### 3. QualityStrategy (퀄리티 전략)

재무 건전성이 좋은 종목을 매수하는 전략입니다.

```python
from src.strategies.quant_strategies import QualityStrategy

strategy = QualityStrategy(
    use_roe=True,        # ROE 사용 여부
    use_debt_ratio=True, # 부채비율 사용 여부
    config=None
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `use_roe` | bool | True | ROE 기반 퀄리티 팩터 사용 |
| `use_debt_ratio` | bool | True | 부채비율 기반 퀄리티 팩터 사용 |
| `config` | Dict | None | 전략 설정 |

**신호 생성 로직**:
```python
# ROE: 높을수록 높은 점수
quality_roe_rank = rank(ROE)

# 부채비율: 낮을수록 높은 점수
quality_debt_score = 1 / (1 + debt_ratio)

# 복합 퀄리티 스코어
quality_score = mean(quality_roe_rank, quality_debt_rank)
```

---

### 4. MultiFactorStrategy (멀티팩터 전략)

여러 팩터를 조합하는 전략입니다.

```python
from src.strategies.quant_strategies import MultiFactorStrategy

strategy = MultiFactorStrategy(
    momentum_weight=0.4,  # 모멘텀 가중치
    value_weight=0.3,     # 가치 가중치
    quality_weight=0.2,   # 퀄리티 가중치
    size_weight=0.1,      # 사이즈 가중치
    config=None
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `momentum_weight` | float | 0.4 | 모멘텀 팩터 가중치 |
| `value_weight` | float | 0.3 | 가치 팩터 가중치 |
| `quality_weight` | float | 0.2 | 퀄리티 팩터 가중치 |
| `size_weight` | float | 0.1 | 사이즈 팩터 가중치 |
| `config` | Dict | None | 전략 설정 |

**참고**: 가중치는 자동으로 정규화되어 합이 1.0이 됩니다.

**신호 생성 로직**:
```python
composite_score = (momentum_rank × 0.4) +
                  (value_rank × 0.3) +
                  (quality_rank × 0.2) +
                  (size_rank × 0.1)
```

**사용되는 팩터**:
- **모멘텀**: 12개월 수익률 (최근 1개월 제외)
- **가치**: PBR, PER 역수의 평균
- **퀄리티**: ROE, 부채비율 역수의 평균
- **사이즈**: 시가총액 로그값의 역수 (소형주 선호)

---

### 5. SizeStrategy (사이즈 전략)

소형주를 매수하는 전략입니다.

```python
from src.strategies.quant_strategies import SizeStrategy

strategy = SizeStrategy(config=None)
```

**신호 생성 로직**:
```python
# 시가총액이 작을수록 높은 점수
size_score = -log(market_cap)
```

---

## 전략 팩토리 함수

### `create_strategy()` - 전략 생성 함수

문자열로 전략을 생성할 수 있습니다.

```python
from src.strategies.quant_strategies import create_strategy

# 모멘텀 전략
strategy = create_strategy('momentum')

# 가치 전략
strategy = create_strategy('value')

# 퀄리티 전략
strategy = create_strategy('quality')

# 멀티팩터 전략
strategy = create_strategy('multifactor')
# 또는
strategy = create_strategy('multi_factor')

# 사이즈 전략
strategy = create_strategy('size')
```

| 전략 이름 | 클래스 |
|----------|--------|
| `'momentum'` | MomentumStrategy |
| `'value'` | ValueStrategy |
| `'quality'` | QualityStrategy |
| `'multifactor'` 또는 `'multi_factor'` | MultiFactorStrategy |
| `'size'` | SizeStrategy |

### 설정과 함께 생성

```python
config = {
    'max_positions': 30,
    'equal_weight': True,
    'max_position_size': 0.1
}

strategy = create_strategy('momentum', config=config)
```

---

## 커스텀 전략 작성

### 기본 구조

```python
from src.strategies.base_strategy import BaseStrategy
from typing import Dict, List
import pandas as pd

class MyCustomStrategy(BaseStrategy):
    """나만의 커스텀 전략"""

    def __init__(self, my_param: float = 1.0, config: Dict = None):
        super().__init__(name="MyCustom", config=config)
        self.my_param = my_param

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """매매 신호 생성"""
        signals = data.copy()

        # 나만의 스코어 계산 로직
        signals['my_score'] = ...

        # 순위 정규화
        signals['my_rank'] = signals.groupby('date')['my_score'].transform(
            lambda x: x.rank(pct=True)
        )

        return signals

    def select_stocks(self, data: pd.DataFrame, top_n: int = None) -> List[str]:
        """종목 선정"""
        if top_n is None:
            top_n = self.config.get('max_positions', 20)

        # 신호 생성
        if 'my_rank' not in data.columns:
            data = self.generate_signals(data)

        # 상위 N개 선정
        top_stocks = data.nlargest(top_n, 'my_rank')
        return top_stocks['symbol'].tolist()
```

### 예제: RSI 기반 전략

```python
from src.strategies.base_strategy import BaseStrategy
from src.data_processing.indicators import TechnicalIndicators

class RSIStrategy(BaseStrategy):
    """RSI 기반 역발상 전략"""

    def __init__(self, rsi_period: int = 14, oversold: float = 30, config: Dict = None):
        super().__init__(name="RSI", config=config)
        self.rsi_period = rsi_period
        self.oversold = oversold

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        signals = data.copy()

        # 종목별 RSI 계산
        signals['rsi'] = signals.groupby('symbol')['close'].transform(
            lambda x: TechnicalIndicators.rsi(x, self.rsi_period)
        )

        # 과매도 종목에 높은 점수
        signals['rsi_score'] = (self.oversold - signals['rsi']).clip(lower=0)

        # 날짜별 순위
        signals['rsi_rank'] = signals.groupby('date')['rsi_score'].transform(
            lambda x: x.rank(pct=True)
        )

        return signals

    def select_stocks(self, data: pd.DataFrame, top_n: int = None) -> List[str]:
        if top_n is None:
            top_n = self.config.get('max_positions', 20)

        if 'rsi_rank' not in data.columns:
            data = self.generate_signals(data)

        # RSI가 과매도 구간인 종목 중 상위 선정
        valid = data[data['rsi'] < self.oversold]
        if len(valid) < top_n:
            valid = data  # 과매도 종목이 부족하면 전체에서 선정

        top_stocks = valid.nlargest(top_n, 'rsi_rank')
        return top_stocks['symbol'].tolist()
```

### 예제: 듀얼 모멘텀 전략

```python
class DualMomentumStrategy(BaseStrategy):
    """듀얼 모멘텀 전략: 절대 모멘텀 + 상대 모멘텀"""

    def __init__(self, abs_lookback: int = 252, rel_lookback: int = 126, config: Dict = None):
        super().__init__(name="DualMomentum", config=config)
        self.abs_lookback = abs_lookback  # 절대 모멘텀 기간
        self.rel_lookback = rel_lookback  # 상대 모멘텀 기간

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        signals = data.copy()

        # 절대 모멘텀: N일 전 대비 수익률
        signals['abs_momentum'] = signals.groupby('symbol')['close'].transform(
            lambda x: x / x.shift(self.abs_lookback) - 1
        )

        # 상대 모멘텀: 다른 종목 대비 순위
        signals['rel_momentum'] = signals.groupby('symbol')['close'].transform(
            lambda x: x / x.shift(self.rel_lookback) - 1
        )
        signals['rel_rank'] = signals.groupby('date')['rel_momentum'].transform(
            lambda x: x.rank(pct=True)
        )

        # 듀얼 모멘텀 스코어: 절대 모멘텀 양수 + 상대 모멘텀 상위
        signals['dual_score'] = signals['rel_rank'] * (signals['abs_momentum'] > 0).astype(int)

        return signals

    def select_stocks(self, data: pd.DataFrame, top_n: int = None) -> List[str]:
        if top_n is None:
            top_n = self.config.get('max_positions', 20)

        if 'dual_score' not in data.columns:
            data = self.generate_signals(data)

        # 절대 모멘텀 양수인 종목 중에서 상대 모멘텀 상위 선정
        valid = data[data['abs_momentum'] > 0]

        if len(valid) == 0:
            return []  # 모든 종목이 하락 중이면 현금 보유

        top_stocks = valid.nlargest(top_n, 'dual_score')
        return top_stocks['symbol'].tolist()
```

---

## 설정 항목

`config/config.yaml` 파일의 `strategy` 섹션:

```yaml
strategy:
  # 리밸런싱
  rebalancing_frequency: "monthly"  # daily, weekly, monthly, quarterly
  rebalancing_day: 1                # 월간 리밸런싱 날짜

  # 포트폴리오 설정
  max_positions: 20                 # 최대 보유 종목 수
  min_positions: 10                 # 최소 보유 종목 수
  equal_weight: true                # 동일 가중 여부

  # 리스크 관리
  stop_loss: 0.15                   # 손절 비율 (15%)
  take_profit: null                 # 익절 비율 (null = 사용 안함)
  max_position_size: 0.1            # 최대 개별 종목 비중 (10%)

  # 팩터 가중치
  factor_weights:
    momentum: 0.4
    value: 0.3
    quality: 0.2
    size: 0.1
```

### 설정값 접근

```python
from src.utils.config_loader import get_config

config = get_config()

# 개별 설정 조회
max_positions = config.get('strategy.max_positions', 20)
rebal_freq = config.get('strategy.rebalancing_frequency', 'monthly')

# 전략 설정 전체 조회
strategy_config = config.get_strategy_config()
```

---

## 예제 코드

### 예제 1: 모멘텀 전략 사용

```python
from src.strategies.quant_strategies import create_strategy
from src.utils.database import get_db

# 데이터 로드
db = get_db()
data = db.get_stock_prices(start_date='2023-01-01')

# 전략 생성
strategy = create_strategy('momentum')

# 신호 생성
signals = strategy.generate_signals(data)

# 특정 날짜 종목 선정
latest_date = signals['date'].max()
latest_data = signals[signals['date'] == latest_date]
selected = strategy.select_stocks(latest_data, top_n=20)

print(f"선정된 종목: {selected}")
```

### 예제 2: 멀티팩터 전략 커스터마이징

```python
from src.strategies.quant_strategies import MultiFactorStrategy

# 커스텀 가중치로 전략 생성
strategy = MultiFactorStrategy(
    momentum_weight=0.5,   # 모멘텀 비중 높임
    value_weight=0.2,
    quality_weight=0.2,
    size_weight=0.1
)

# 신호 생성 및 종목 선정
signals = strategy.generate_signals(data)
selected = strategy.select_stocks(signals[signals['date'] == latest_date])

# 포트폴리오 가중치 계산
weights = strategy.calculate_weights(selected, signals, method='equal')
print(f"포트폴리오: {weights}")
```

### 예제 3: 전략 정보 확인

```python
strategy = create_strategy('multifactor')

# 전략 정보
info = strategy.get_strategy_info()
print(f"전략 이름: {info['name']}")
print(f"설정: {info['config']}")

# 리밸런싱 날짜 확인
rebal_dates = strategy.get_rebalancing_dates(
    start_date='2023-01-01',
    end_date='2024-01-01',
    frequency='monthly'
)
print(f"리밸런싱 날짜 수: {len(rebal_dates)}")
print(f"첫 리밸런싱: {rebal_dates[0]}")
```

---

## 다음 단계

- [06. 포트폴리오 최적화](./06-portfolio-optimizer.md) - 포트폴리오 가중치 최적화
- [07. 백테스팅](./07-backtesting.md) - 전략 성과 시뮬레이션
