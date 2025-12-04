# 09. 데이터베이스 (Database)

데이터베이스 스키마와 사용법에 대한 상세 매뉴얼입니다.

## 목차

1. [개요](#개요)
2. [데이터베이스 스키마](#데이터베이스-스키마)
3. [DatabaseManager 클래스](#databasemanager-클래스)
4. [데이터 저장](#데이터-저장)
5. [데이터 조회](#데이터-조회)
6. [고급 쿼리](#고급-쿼리)
7. [예제 코드](#예제-코드)

---

## 개요

**파일 위치**: `src/utils/database.py`

시스템은 SQLite, PostgreSQL, MySQL을 지원합니다. 기본적으로 SQLite가 사용됩니다.

### 데이터베이스 파일 위치

```
data/database/quant_investing.db  (SQLite)
```

### 지원 데이터베이스

| 데이터베이스 | 장점 | 단점 |
|-------------|------|------|
| SQLite | 설치 불필요, 파일 기반 | 동시 접속 제한 |
| PostgreSQL | 고성능, 확장성 | 별도 설치 필요 |
| MySQL | 널리 사용됨 | 별도 설치 필요 |

---

## 데이터베이스 스키마

### 테이블 구조

```
┌─────────────────────┐      ┌─────────────────────┐
│    stock_prices     │      │  stock_fundamentals │
├─────────────────────┤      ├─────────────────────┤
│ id (PK)             │      │ id (PK)             │
│ symbol              │      │ symbol              │
│ date                │      │ date                │
│ open                │      │ market_cap          │
│ high                │      │ per                 │
│ low                 │      │ pbr                 │
│ close               │      │ eps                 │
│ volume              │      │ bps                 │
│ adj_close           │      │ roe                 │
│ market              │      │ debt_ratio          │
└─────────────────────┘      │ ...                 │
                             └─────────────────────┘

┌─────────────────────┐      ┌─────────────────────┐
│     stock_info      │      │  strategy_results   │
├─────────────────────┤      ├─────────────────────┤
│ symbol (PK)         │      │ id (PK)             │
│ name                │      │ strategy_name       │
│ market              │      │ run_date            │
│ sector              │      │ start_date          │
│ industry            │      │ end_date            │
│ listing_date        │      │ total_return        │
│ last_updated        │      │ annual_return       │
└─────────────────────┘      │ sharpe_ratio        │
                             │ max_drawdown        │
                             │ ...                 │
                             └─────────────────────┘

┌─────────────────────┐
│ portfolio_holdings  │
├─────────────────────┤
│ id (PK)             │
│ portfolio_name      │
│ date                │
│ symbol              │
│ weight              │
│ quantity            │
│ price               │
│ value               │
└─────────────────────┘
```

### 테이블별 상세 스키마

#### stock_prices - 주가 데이터

```sql
CREATE TABLE stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,           -- 종목 코드
    date DATE NOT NULL,             -- 날짜
    open REAL,                      -- 시가
    high REAL,                      -- 고가
    low REAL,                       -- 저가
    close REAL,                     -- 종가
    volume INTEGER,                 -- 거래량
    adj_close REAL,                 -- 수정 종가 (미국 주식)
    market TEXT,                    -- 시장 (KOSPI, NASDAQ 등)
    UNIQUE(symbol, date)            -- 복합 유니크 제약
);

-- 인덱스
CREATE INDEX idx_prices_symbol_date ON stock_prices(symbol, date);
CREATE INDEX idx_prices_date ON stock_prices(date);
```

#### stock_fundamentals - 펀더멘털 데이터

```sql
CREATE TABLE stock_fundamentals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,           -- 종목 코드
    date DATE NOT NULL,             -- 날짜
    market_cap REAL,                -- 시가총액
    per REAL,                       -- 주가수익비율
    pbr REAL,                       -- 주가순자산비율
    eps REAL,                       -- 주당순이익
    bps REAL,                       -- 주당순자산
    roe REAL,                       -- 자기자본이익률
    debt_ratio REAL,                -- 부채비율
    current_ratio REAL,             -- 유동비율
    revenue REAL,                   -- 매출액
    operating_income REAL,          -- 영업이익
    net_income REAL,                -- 순이익
    UNIQUE(symbol, date)
);

CREATE INDEX idx_fundamentals_symbol_date ON stock_fundamentals(symbol, date);
```

#### stock_info - 종목 정보

```sql
CREATE TABLE stock_info (
    symbol TEXT PRIMARY KEY,        -- 종목 코드
    name TEXT,                      -- 종목명
    market TEXT,                    -- 시장
    sector TEXT,                    -- 섹터
    industry TEXT,                  -- 산업
    listing_date DATE,              -- 상장일
    last_updated TIMESTAMP          -- 최종 업데이트
);
```

#### strategy_results - 전략 결과

```sql
CREATE TABLE strategy_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,    -- 전략 이름
    run_date TIMESTAMP NOT NULL,    -- 실행 날짜
    start_date DATE,                -- 백테스트 시작일
    end_date DATE,                  -- 백테스트 종료일
    total_return REAL,              -- 총 수익률
    annual_return REAL,             -- 연환산 수익률
    sharpe_ratio REAL,              -- 샤프 비율
    max_drawdown REAL,              -- 최대 낙폭
    win_rate REAL,                  -- 승률
    parameters TEXT,                -- 전략 파라미터 (JSON)
    UNIQUE(strategy_name, run_date)
);
```

#### portfolio_holdings - 포트폴리오 보유

```sql
CREATE TABLE portfolio_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_name TEXT NOT NULL,   -- 포트폴리오 이름
    date DATE NOT NULL,             -- 날짜
    symbol TEXT NOT NULL,           -- 종목 코드
    weight REAL,                    -- 비중
    quantity INTEGER,               -- 수량
    price REAL,                     -- 가격
    value REAL,                     -- 평가 금액
    UNIQUE(portfolio_name, date, symbol)
);

CREATE INDEX idx_holdings_portfolio_date ON portfolio_holdings(portfolio_name, date);
```

---

## DatabaseManager 클래스

### 초기화

```python
from src.utils.database import DatabaseManager, get_db

# 싱글톤 패턴으로 인스턴스 얻기 (권장)
db = get_db()

# 또는 직접 초기화
db = DatabaseManager(db_config={
    'type': 'sqlite',
    'path': 'data/database/quant_investing.db'
})
```

### 연결 문자열

```python
# SQLite
"sqlite:///data/database/quant_investing.db"

# PostgreSQL
"postgresql://user:password@localhost:5432/quant_investing"

# MySQL
"mysql+pymysql://user:password@localhost:3306/quant_investing"
```

---

## 데이터 저장

### `save_stock_prices()` - 주가 데이터 저장

```python
import pandas as pd
from src.utils.database import get_db

db = get_db()

# DataFrame 준비
df = pd.DataFrame({
    'symbol': ['005930', '005930'],
    'date': ['2024-01-02', '2024-01-03'],
    'open': [71000, 71500],
    'high': [72000, 72500],
    'low': [70000, 70500],
    'close': [71500, 72000],
    'volume': [1000000, 1200000],
    'market': ['KOSPI', 'KOSPI']
})

# 저장
db.save_stock_prices(df, if_exists='append')
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `df` | DataFrame | 저장할 데이터 |
| `if_exists` | str | 'append' (추가) 또는 'replace' (교체) |

### `save_fundamentals()` - 펀더멘털 데이터 저장

```python
fundamentals = pd.DataFrame({
    'symbol': ['005930'],
    'date': ['2024-01-02'],
    'market_cap': [400000000000000],
    'per': [15.5],
    'pbr': [1.2],
    'eps': [4500],
    'roe': [0.12]
})

db.save_fundamentals(fundamentals, if_exists='append')
```

### `save_stock_info()` - 종목 정보 저장

```python
stock_info = pd.DataFrame({
    'symbol': ['005930', '000660'],
    'name': ['삼성전자', 'SK하이닉스'],
    'market': ['KOSPI', 'KOSPI'],
    'sector': ['전자', '반도체'],
    'last_updated': [datetime.now(), datetime.now()]
})

db.save_stock_info(stock_info, if_exists='replace')
```

---

## 데이터 조회

### `get_stock_prices()` - 주가 데이터 조회

```python
from src.utils.database import get_db

db = get_db()

# 전체 데이터 조회
all_prices = db.get_stock_prices()

# 특정 종목 조회
samsung = db.get_stock_prices(symbol='005930')

# 여러 종목 조회
selected = db.get_stock_prices(symbol=['005930', '000660'])

# 기간 지정 조회
recent = db.get_stock_prices(
    symbol='005930',
    start_date='2023-01-01',
    end_date='2024-01-01'
)
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `symbol` | str/List[str] | 종목 코드 (선택) |
| `start_date` | str | 시작일 YYYY-MM-DD (선택) |
| `end_date` | str | 종료일 YYYY-MM-DD (선택) |

### `get_fundamentals()` - 펀더멘털 데이터 조회

```python
# 특정 종목 펀더멘털 조회
fundamentals = db.get_fundamentals(
    symbol='005930',
    start_date='2023-01-01',
    end_date='2024-01-01'
)
```

### `get_stock_info()` - 종목 정보 조회

```python
# 전체 종목 정보
all_info = db.get_stock_info()

# 특정 종목 정보
info = db.get_stock_info(symbol='005930')

# 여러 종목 정보
selected_info = db.get_stock_info(symbol=['005930', '000660'])
```

### `get_all_symbols()` - 전체 종목 코드 조회

```python
# 전체 종목
all_symbols = db.get_all_symbols()

# 특정 시장 종목
kospi_symbols = db.get_all_symbols(market='KOSPI')
nasdaq_symbols = db.get_all_symbols(market='NASDAQ')
```

---

## 고급 쿼리

### `execute_query()` - 커스텀 SQL 실행

```python
# SELECT 쿼리
query = """
SELECT symbol, date, close, volume
FROM stock_prices
WHERE date >= :start_date
AND volume > :min_volume
ORDER BY volume DESC
LIMIT 100
"""

results = db.execute_query(
    query,
    params={
        'start_date': '2024-01-01',
        'min_volume': 10000000
    }
)

print(results)
```

### 자주 사용하는 쿼리 예제

#### 거래량 상위 종목

```python
query = """
SELECT symbol, name, AVG(volume) as avg_volume
FROM stock_prices p
JOIN stock_info i ON p.symbol = i.symbol
WHERE p.date >= :start_date
GROUP BY p.symbol
ORDER BY avg_volume DESC
LIMIT 20
"""

top_volume = db.execute_query(query, {'start_date': '2024-01-01'})
```

#### 시가총액 상위 종목

```python
query = """
SELECT f.symbol, i.name, f.market_cap
FROM stock_fundamentals f
JOIN stock_info i ON f.symbol = i.symbol
WHERE f.date = (SELECT MAX(date) FROM stock_fundamentals)
ORDER BY f.market_cap DESC
LIMIT 20
"""

top_market_cap = db.execute_query(query)
```

#### 저PER 종목 찾기

```python
query = """
SELECT f.symbol, i.name, f.per, f.pbr
FROM stock_fundamentals f
JOIN stock_info i ON f.symbol = i.symbol
WHERE f.date = (SELECT MAX(date) FROM stock_fundamentals)
AND f.per > 0 AND f.per < 10
ORDER BY f.per
"""

low_per = db.execute_query(query)
```

#### 최근 수익률 계산

```python
query = """
WITH recent_prices AS (
    SELECT
        symbol,
        close,
        LAG(close, 20) OVER (PARTITION BY symbol ORDER BY date) as price_20d_ago
    FROM stock_prices
    WHERE date >= :start_date
)
SELECT
    symbol,
    (close / price_20d_ago - 1) * 100 as return_20d
FROM recent_prices
WHERE price_20d_ago IS NOT NULL
ORDER BY return_20d DESC
"""

returns = db.execute_query(query, {'start_date': '2024-01-01'})
```

---

## 예제 코드

### 예제 1: 데이터 수집 후 저장

```python
from src.data_collection.kr_stock_collector import KoreanStockCollector
from src.utils.database import get_db
from datetime import datetime, timedelta

# 컬렉터 및 DB 초기화
collector = KoreanStockCollector()
db = get_db()

# 데이터 수집
symbols = ['005930', '000660', '035420']
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

for symbol in symbols:
    # 가격 데이터
    prices = collector.get_price_data(symbol, start_date, end_date)
    if not prices.empty:
        db.save_stock_prices(prices, if_exists='append')

    # 펀더멘털 데이터
    fundamentals = collector.get_fundamental_data(symbol, start_date, end_date)
    if not fundamentals.empty:
        db.save_fundamentals(fundamentals, if_exists='append')

    print(f"{symbol} 저장 완료")

print("모든 데이터 저장 완료")
```

### 예제 2: 데이터 병합 및 분석

```python
from src.utils.database import get_db
import pandas as pd

db = get_db()

# 가격 및 펀더멘털 데이터 조회
prices = db.get_stock_prices(start_date='2023-01-01')
fundamentals = db.get_fundamentals(start_date='2023-01-01')

# 데이터 병합
merged = prices.merge(
    fundamentals[['symbol', 'date', 'per', 'pbr', 'roe', 'market_cap']],
    on=['symbol', 'date'],
    how='left'
)

# 최신 날짜 데이터 필터링
latest_date = merged['date'].max()
latest = merged[merged['date'] == latest_date]

# 저PER + 고ROE 종목 찾기
quality_value = latest[
    (latest['per'] > 0) &
    (latest['per'] < 15) &
    (latest['roe'] > 0.1)
].sort_values('roe', ascending=False)

print("저PER + 고ROE 종목:")
print(quality_value[['symbol', 'close', 'per', 'pbr', 'roe']].head(10))
```

### 예제 3: 백업 및 복원

```python
import shutil
from pathlib import Path

# SQLite 데이터베이스 백업
def backup_database(backup_dir='backups/'):
    db_path = Path('data/database/quant_investing.db')
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_path / f'quant_investing_{timestamp}.db'

    shutil.copy2(db_path, backup_file)
    print(f"백업 완료: {backup_file}")

# 복원
def restore_database(backup_file):
    db_path = Path('data/database/quant_investing.db')
    shutil.copy2(backup_file, db_path)
    print(f"복원 완료: {db_path}")

# 실행
backup_database()
```

### 예제 4: 데이터 무결성 확인

```python
from src.utils.database import get_db

db = get_db()

# 중복 데이터 확인
duplicates_query = """
SELECT symbol, date, COUNT(*) as cnt
FROM stock_prices
GROUP BY symbol, date
HAVING cnt > 1
"""

duplicates = db.execute_query(duplicates_query)
if not duplicates.empty:
    print(f"중복 레코드 발견: {len(duplicates)}건")
    print(duplicates)
else:
    print("중복 레코드 없음")

# 결측치 확인
null_check_query = """
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN close IS NULL THEN 1 ELSE 0 END) as null_close,
    SUM(CASE WHEN volume IS NULL THEN 1 ELSE 0 END) as null_volume
FROM stock_prices
"""

null_counts = db.execute_query(null_check_query)
print(null_counts)

# 날짜 연속성 확인
date_gaps_query = """
SELECT symbol, date,
       LAG(date) OVER (PARTITION BY symbol ORDER BY date) as prev_date,
       julianday(date) - julianday(LAG(date) OVER (PARTITION BY symbol ORDER BY date)) as gap
FROM stock_prices
HAVING gap > 5
"""

# 실행 (SQLite에서는 윈도우 함수 지원)
```

### 예제 5: 데이터베이스 통계

```python
from src.utils.database import get_db

db = get_db()

# 데이터 통계
stats_query = """
SELECT
    'stock_prices' as table_name,
    COUNT(*) as row_count,
    COUNT(DISTINCT symbol) as symbols,
    MIN(date) as min_date,
    MAX(date) as max_date
FROM stock_prices
UNION ALL
SELECT
    'stock_fundamentals',
    COUNT(*),
    COUNT(DISTINCT symbol),
    MIN(date),
    MAX(date)
FROM stock_fundamentals
UNION ALL
SELECT
    'stock_info',
    COUNT(*),
    COUNT(DISTINCT symbol),
    NULL,
    NULL
FROM stock_info
"""

stats = db.execute_query(stats_query)
print("데이터베이스 통계:")
print(stats.to_string(index=False))
```

---

## 연결 관리

### 연결 닫기

```python
from src.utils.database import get_db

db = get_db()

# 작업 수행...

# 명시적으로 연결 종료
db.close()
```

### Context Manager 사용 (권장)

```python
from src.utils.database import DatabaseManager

# with 문 사용 시 자동으로 연결 정리
with DatabaseManager() as db:
    data = db.get_stock_prices(symbol='005930')
    # 작업 수행
# with 블록 종료 시 자동 close
```

---

## 주의사항

1. **트랜잭션**: 대량 데이터 삽입 시 트랜잭션을 사용하여 성능 향상
2. **인덱스**: 자주 조회하는 컬럼에는 인덱스 추가
3. **백업**: 정기적으로 데이터베이스 백업
4. **연결 관리**: 작업 완료 후 연결 닫기
5. **데이터 타입**: 날짜는 문자열 'YYYY-MM-DD' 형식 사용

---

## 문서 끝

이 문서로 Quantitative Investing 시스템의 매뉴얼이 완료되었습니다.

### 전체 문서 목록

1. [시작하기](./01-getting-started.md)
2. [데이터 수집](./02-data-collection.md)
3. [기술적 지표](./03-technical-indicators.md)
4. [팩터 분석](./04-factor-analysis.md)
5. [투자 전략](./05-strategies.md)
6. [포트폴리오 최적화](./06-portfolio-optimizer.md)
7. [백테스팅](./07-backtesting.md)
8. [설정 파일](./08-configuration.md)
9. [데이터베이스](./09-database.md) (현재 문서)
