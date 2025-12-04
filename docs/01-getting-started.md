# 01. 시작하기 (Getting Started)

퀀트 투자 시스템의 설치 및 환경 설정 가이드입니다.

## 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [설치 방법](#설치-방법)
3. [초기 설정](#초기-설정)
4. [빠른 시작 예제](#빠른-시작-예제)
5. [프로젝트 구조](#프로젝트-구조)

---

## 시스템 요구사항

### Python 버전
- Python 3.8 이상 필수
- Python 3.10 또는 3.11 권장

### 운영체제
- Linux (Ubuntu 20.04+)
- macOS (10.15+)
- Windows 10/11

### 하드웨어 권장사양
- RAM: 8GB 이상 (대용량 데이터 처리 시 16GB 권장)
- 저장공간: 10GB 이상 (주식 데이터 저장용)

---

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/yourusername/Quantitative_Investing.git
cd Quantitative_Investing
```

### 2. 가상환경 생성 (권장)

```bash
# venv 사용
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 또는
.\venv\Scripts\activate  # Windows

# 또는 conda 사용
conda create -n quant python=3.10
conda activate quant
```

### 3. 의존성 설치

```bash
# 기본 설치
pip install -r requirements.txt

# 개발용 도구 포함 설치
pip install -e ".[dev]"
```

### 4. TA-Lib 설치 (선택사항)

TA-Lib은 일부 시스템에서 별도 설치가 필요합니다:

```bash
# Ubuntu/Debian
sudo apt-get install ta-lib

# macOS
brew install ta-lib

# Windows
# https://github.com/mrjbq7/ta-lib#windows에서 바이너리 다운로드
```

---

## 초기 설정

### 1. 설정 파일 확인

`config/config.yaml` 파일을 열어 설정을 확인합니다:

```yaml
# 데이터 수집 설정
data_collection:
  kr_stock:
    market: ["KOSPI", "KOSDAQ"]
    min_market_cap: 50000000000  # 500억 원

  us_stock:
    market: ["NYSE", "NASDAQ"]
    min_market_cap: 1000000000   # 10억 달러

# 데이터 시작일
  start_date: "2018-01-01"
```

### 2. 데이터베이스 초기화

시스템 첫 실행 시 데이터베이스가 자동으로 생성됩니다:

```python
from src.utils.database import get_db

# 데이터베이스 초기화 (테이블 자동 생성)
db = get_db()
```

기본 경로: `data/database/quant_investing.db` (SQLite)

### 3. 로그 디렉토리 확인

로그는 `logs/` 디렉토리에 저장됩니다. 자동 생성되지만 수동으로도 생성 가능:

```bash
mkdir -p logs
```

---

## 빠른 시작 예제

### 예제 1: 한국 주식 데이터 수집

```python
from datetime import datetime, timedelta
from src.data_collection.kr_stock_collector import KoreanStockCollector

# 컬렉터 초기화
collector = KoreanStockCollector(use_pykrx=True)

# 주요 종목 리스트
major_stocks = [
    '005930',  # 삼성전자
    '000660',  # SK하이닉스
    '035420',  # NAVER
    '051910',  # LG화학
]

# 최근 1년 데이터 수집
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

# 데이터 수집 및 DB 저장
df = collector.collect_multiple_stocks(
    symbols=major_stocks,
    start_date=start_date,
    end_date=end_date,
    save_to_db=True  # 데이터베이스에 자동 저장
)

print(f"수집된 레코드 수: {len(df)}")
print(df.head())
```

### 예제 2: 미국 주식 데이터 수집

```python
from src.data_collection.us_stock_collector import USStockCollector

# 컬렉터 초기화
collector = USStockCollector()

# 기술주 리스트
tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']

# 벌크 다운로드 (빠른 방식)
df = collector.download_bulk_data(
    symbols=tech_stocks,
    start_date='2020-01-01',
    end_date='2024-01-01'
)

print(f"수집된 레코드 수: {len(df)}")
```

### 예제 3: 모멘텀 전략 백테스팅

```python
from src.strategies.quant_strategies import create_strategy
from src.backtesting.backtester import run_backtest
from src.utils.database import get_db

# DB에서 데이터 로드
db = get_db()
data = db.get_stock_prices(start_date='2020-01-01')

# 모멘텀 전략 생성
strategy = create_strategy('momentum')

# 백테스팅 실행
results, summary = run_backtest(
    strategy=strategy,
    data=data,
    initial_capital=100000000,  # 1억 원
    commission=0.0015,          # 0.15% 수수료
    slippage=0.001,             # 0.1% 슬리피지
    rebalance_frequency='monthly'
)

# 결과 출력
print("\n=== 백테스팅 결과 ===")
for key, value in summary.items():
    if isinstance(value, float):
        print(f"{key}: {value:.4f}")
    else:
        print(f"{key}: {value}")
```

### 예제 4: 기술적 지표 추가

```python
from src.data_processing.indicators import add_all_indicators

# 기존 데이터에 지표 추가
df_with_indicators = add_all_indicators(df)

# 추가된 지표 확인
print("추가된 컬럼들:")
print([col for col in df_with_indicators.columns if col not in df.columns])
```

---

## 프로젝트 구조

```
Quantitative_Investing/
│
├── config/
│   └── config.yaml              # 전체 설정 파일
│
├── data/
│   └── database/
│       └── quant_investing.db   # SQLite 데이터베이스
│
├── docs/                        # 문서
│   ├── README.md
│   └── *.md
│
├── logs/                        # 로그 파일
│   └── quant_investing.log
│
├── notebooks/                   # Jupyter 노트북
│
├── src/
│   ├── __init__.py
│   │
│   ├── data_collection/         # 데이터 수집 모듈
│   │   ├── __init__.py
│   │   ├── kr_stock_collector.py
│   │   └── us_stock_collector.py
│   │
│   ├── data_processing/         # 데이터 처리 모듈
│   │   ├── __init__.py
│   │   ├── indicators.py
│   │   └── feature_engineering.py
│   │
│   ├── strategies/              # 투자 전략 모듈
│   │   ├── __init__.py
│   │   ├── base_strategy.py
│   │   └── quant_strategies.py
│   │
│   ├── portfolio/               # 포트폴리오 모듈
│   │   ├── __init__.py
│   │   └── portfolio_optimizer.py
│   │
│   ├── backtesting/             # 백테스팅 모듈
│   │   ├── __init__.py
│   │   ├── backtester.py
│   │   ├── performance_metrics.py
│   │   └── visualizer.py
│   │
│   └── utils/                   # 유틸리티 모듈
│       ├── __init__.py
│       ├── config_loader.py
│       ├── database.py
│       ├── helpers.py
│       └── logger.py
│
├── tests/                       # 테스트 코드
│   ├── __init__.py
│   ├── test_indicators.py
│   ├── test_strategies.py
│   └── test_portfolio.py
│
├── requirements.txt             # Python 의존성
├── setup.py                     # 패키지 설치 스크립트
└── README.md                    # 프로젝트 설명
```

---

## 다음 단계

- [02. 데이터 수집](./02-data-collection.md) - 상세한 데이터 수집 방법
- [05. 투자 전략](./05-strategies.md) - 다양한 투자 전략 사용법
- [07. 백테스팅](./07-backtesting.md) - 백테스팅 실행 및 결과 분석

---

## 문제 해결

### 자주 발생하는 문제

1. **ImportError: No module named 'src'**
   ```bash
   # 프로젝트 루트에서 설치
   pip install -e .
   ```

2. **pykrx 연결 오류**
   - 한국 증권거래소 서버의 일시적 문제일 수 있음
   - 잠시 후 재시도

3. **yfinance Rate Limit**
   ```python
   # delay 파라미터 사용
   collector.collect_multiple_stocks(symbols, delay=0.5)
   ```

4. **TA-Lib 설치 오류**
   ```bash
   # ta-lib-prebuilt 사용 (사전 빌드 버전)
   pip install ta-lib-prebuilt
   ```
