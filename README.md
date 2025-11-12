# Quantitative Investing System

한국/미국 주식 시장을 대상으로 하는 퀀트 투자 시스템입니다. 데이터 수집, 팩터 분석, 전략 백테스팅을 지원합니다.

## 📋 프로젝트 개요

이 프로젝트는 퀀트 투자 전략을 개발하고 백테스팅할 수 있는 통합 시스템을 제공합니다. Python 기반으로 구축되었으며, 다음과 같은 기능을 포함합니다:

- 한국 주식 (KOSPI/KOSDAQ) 및 미국 주식 (NYSE/NASDAQ) 데이터 수집
- 기술적 지표 계산 (SMA, RSI, MACD, Bollinger Bands 등)
- 퀀트 팩터 계산 (모멘텀, 밸류, 퀄리티, 사이즈)
- 다양한 투자 전략 구현 (모멘텀, 밸류, 퀄리티, 멀티팩터)
- 백테스팅 엔진 및 성과 분석
- 시각화 및 리포트 생성

## 🚀 시작하기

### 필수 요구사항

- Python 3.8 이상
- pip 또는 conda

### 설치

1. 레포지토리 클론
```bash
git clone https://github.com/yourusername/Quantitative_Investing.git
cd Quantitative_Investing
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 패키지 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
```bash
cp config/.env.example config/.env
# .env 파일을 열어 API 키 등을 설정
```

## 📂 프로젝트 구조

```
Quantitative_Investing/
├── config/                    # 설정 파일
│   ├── config.yaml           # 전역 설정
│   └── .env.example          # 환경 변수 예제
├── data/                      # 데이터 저장소
│   ├── raw/                  # 원본 데이터
│   ├── processed/            # 전처리된 데이터
│   └── database/             # SQLite DB
├── src/                       # 소스 코드
│   ├── data_collection/      # 데이터 수집
│   │   ├── kr_stock_collector.py
│   │   └── us_stock_collector.py
│   ├── data_processing/      # 데이터 전처리
│   │   ├── indicators.py
│   │   └── feature_engineering.py
│   ├── strategies/           # 투자 전략
│   │   ├── base_strategy.py
│   │   └── quant_strategies.py
│   ├── backtesting/          # 백테스팅
│   │   ├── backtester.py
│   │   ├── performance_metrics.py
│   │   └── visualizer.py
│   └── utils/                # 유틸리티
│       ├── config_loader.py
│       ├── database.py
│       ├── logger.py
│       └── helpers.py
├── notebooks/                 # Jupyter 노트북
├── tests/                     # 테스트 코드
└── README.md                  # 이 파일
```

## 💡 사용 예제

### 1. 데이터 수집

#### 한국 주식 데이터 수집
```python
from src.data_collection.kr_stock_collector import KoreanStockCollector
from datetime import datetime, timedelta

# 수집기 초기화
collector = KoreanStockCollector(use_pykrx=True)

# 주요 종목 리스트
stocks = ['005930', '000660', '035420']  # 삼성전자, SK하이닉스, NAVER

# 최근 1년 데이터 수집
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

df = collector.collect_multiple_stocks(
    symbols=stocks,
    start_date=start_date,
    end_date=end_date,
    save_to_db=True
)
```

#### 미국 주식 데이터 수집
```python
from src.data_collection.us_stock_collector import USStockCollector

collector = USStockCollector()

# 주요 기술주
tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']

df = collector.download_bulk_data(
    symbols=tech_stocks,
    start_date=start_date,
    end_date=end_date
)
```

### 2. 백테스팅

```python
from src.strategies.quant_strategies import create_strategy
from src.backtesting.backtester import run_backtest
from src.backtesting.visualizer import BacktestVisualizer

# 전략 생성
strategy = create_strategy('multifactor')

# 백테스트 실행
results, summary = run_backtest(
    strategy=strategy,
    data=df,
    start_date='2020-01-01',
    end_date='2023-12-31',
    initial_capital=100000000,  # 1억원
    rebalance_frequency='monthly'
)

# 결과 출력
print("Backtest Summary:")
for key, value in summary.items():
    print(f"{key}: {value}")

# 시각화
viz = BacktestVisualizer(results)
viz.plot_portfolio_value()
viz.plot_cumulative_returns()
viz.plot_drawdown()
```

### 3. 전략 비교

```python
from src.backtesting.performance_metrics import compare_strategies
from src.backtesting.visualizer import compare_strategies_plot

# 여러 전략 백테스트
strategies = {
    'Momentum': create_strategy('momentum'),
    'Value': create_strategy('value'),
    'Quality': create_strategy('quality'),
    'MultiF actor': create_strategy('multifactor')
}

results_dict = {}
for name, strategy in strategies.items():
    results, _ = run_backtest(strategy, df, start_date='2020-01-01')
    results_dict[name] = results

# 전략 비교 테이블
comparison = compare_strategies(results_dict)
print(comparison)

# 시각화
compare_strategies_plot(results_dict)
```

## 📊 지원하는 전략

### 1. 모멘텀 전략 (Momentum Strategy)
- 과거 수익률이 높은 종목에 투자
- 12개월 모멘텀 (최근 1개월 제외)
- 승자 지속 효과 활용

### 2. 밸류 전략 (Value Strategy)
- 저평가된 종목에 투자
- PBR (Price-to-Book Ratio)
- PER (Price-to-Earnings Ratio)

### 3. 퀄리티 전략 (Quality Strategy)
- 우량 기업에 투자
- ROE (Return on Equity)
- 부채비율 (Debt Ratio)

### 4. 멀티팩터 전략 (Multi-Factor Strategy)
- 여러 팩터를 결합
- 기본 가중치: 모멘텀 40%, 밸류 30%, 퀄리티 20%, 사이즈 10%
- 팩터 가중치 커스터마이징 가능

### 5. 사이즈 전략 (Size Strategy)
- 소형주 프리미엄 활용
- 시가총액 기준 선택

## 📈 성과 지표

시스템은 다음과 같은 성과 지표를 제공합니다:

- **Total Return**: 총 수익률
- **Annual Return (CAGR)**: 연환산 수익률
- **Volatility**: 변동성 (연환산)
- **Sharpe Ratio**: 샤프 비율
- **Sortino Ratio**: 소르티노 비율
- **Max Drawdown**: 최대 낙폭
- **Calmar Ratio**: 칼마 비율
- **Win Rate**: 승률
- **Profit Factor**: 손익 비율
- **Value at Risk (VaR)**: 위험가치
- **Conditional VaR (CVaR)**: 조건부 위험가치

## 🛠️ 설정

`config/config.yaml` 파일에서 다음을 설정할 수 있습니다:

- 데이터 수집 설정 (시장, 시가총액 필터 등)
- 전략 파라미터 (리밸런싱 주기, 포지션 수, 팩터 가중치)
- 백테스팅 설정 (초기 자본, 수수료, 슬리피지)
- 데이터베이스 설정
- 로깅 설정

## 📝 예제 노트북

`notebooks/` 디렉토리에서 다음 예제를 확인할 수 있습니다:

1. **데이터 수집 및 탐색** (exploratory/)
2. **전략 개발 및 최적화** (strategy_development/)
3. **백테스팅 결과 분석** (backtesting_results/)

## 🔧 개발 가이드

### 새로운 전략 추가하기

1. `src/strategies/base_strategy.py`의 `BaseStrategy` 클래스를 상속
2. `generate_signals()` 메서드 구현
3. `select_stocks()` 메서드 구현

예제:
```python
from src.strategies.base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, config=None):
        super().__init__(name="MyCustom", config=config)

    def generate_signals(self, data):
        # 시그널 생성 로직
        signals = data.copy()
        # ... 팩터 계산
        return signals

    def select_stocks(self, data, top_n=None):
        # 종목 선택 로직
        # ... 상위 N개 종목 선택
        return selected_symbols
```

### 테스트 실행

```bash
pytest tests/
```

## 📚 참고 자료

- [FinanceDataReader Documentation](https://github.com/FinanceData/FinanceDataReader)
- [pykrx Documentation](https://github.com/sharebook-kr/pykrx)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [Quantitative Investment Analysis](https://www.cfainstitute.org/)

## ⚠️ 주의사항

1. **투자 위험**: 이 시스템은 교육 및 연구 목적으로 제공됩니다. 실제 투자 시 발생하는 손실에 대해 책임지지 않습니다.
2. **과거 성과**: 백테스팅 결과가 미래 수익을 보장하지 않습니다.
3. **데이터 정확성**: 데이터 소스의 정확성을 항상 검증하세요.
4. **거래 비용**: 실제 거래 시 수수료와 세금을 고려하세요.
5. **API 제한**: 무료 데이터 API는 요청 제한이 있을 수 있습니다.

## 🤝 기여하기

기여를 환영합니다! 다음 방법으로 기여할 수 있습니다:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이센스

This project is licensed under the MIT License.

## 📧 연락처

프로젝트 관련 문의: [your.email@example.com](mailto:your.email@example.com)

## 🙏 감사의 말

- FinanceDataReader, pykrx, yfinance 개발자분들께 감사드립니다.
- 퀀트 투자 커뮤니티의 모든 기여자분들께 감사드립니다.

---

**Happy Quant Investing! 📊💰**
