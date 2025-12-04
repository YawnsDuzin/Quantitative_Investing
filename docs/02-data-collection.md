# 02. 데이터 수집 (Data Collection)

한국 및 미국 주식 데이터 수집 방법에 대한 상세 매뉴얼입니다.

## 목차

1. [한국 주식 데이터 수집](#한국-주식-데이터-수집)
2. [미국 주식 데이터 수집](#미국-주식-데이터-수집)
3. [데이터 종류](#데이터-종류)
4. [데이터 저장](#데이터-저장)
5. [예제 코드](#예제-코드)

---

## 한국 주식 데이터 수집

### 클래스: `KoreanStockCollector`

**파일 위치**: `src/data_collection/kr_stock_collector.py`

한국 주식 데이터는 `pykrx` 또는 `FinanceDataReader` 라이브러리를 사용하여 수집합니다.

### 초기화

```python
from src.data_collection.kr_stock_collector import KoreanStockCollector

# pykrx 사용 (권장 - 더 안정적)
collector = KoreanStockCollector(use_pykrx=True)

# FinanceDataReader 사용
collector = KoreanStockCollector(use_pykrx=False)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `use_pykrx` | bool | True | pykrx 라이브러리 사용 여부 |

### 메서드 상세

#### 1. `get_stock_list(market)` - 종목 리스트 조회

```python
# 전체 종목 조회
all_stocks = collector.get_stock_list(market="ALL")

# KOSPI만 조회
kospi_stocks = collector.get_stock_list(market="KOSPI")

# KOSDAQ만 조회
kosdaq_stocks = collector.get_stock_list(market="KOSDAQ")
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `market` | str | "ALL" | 시장 종류: "KOSPI", "KOSDAQ", "ALL" |

**반환값**: DataFrame (columns: symbol, name, market)

```
    symbol       name  market
0   005930     삼성전자   KOSPI
1   000660  SK하이닉스   KOSPI
2   035420       NAVER   KOSPI
```

#### 2. `get_price_data(symbol, start_date, end_date)` - 가격 데이터 조회

```python
from datetime import datetime, timedelta

# 삼성전자 1년 가격 데이터
df = collector.get_price_data(
    symbol='005930',
    start_date='2023-01-01',
    end_date='2024-01-01'
)

# datetime 객체 사용 가능
end_date = datetime.now()
start_date = end_date - timedelta(days=365)
df = collector.get_price_data('005930', start_date, end_date)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `symbol` | str | 필수 | 종목 코드 (예: '005930') |
| `start_date` | str/datetime | None | 시작일 (기본: 5년 전) |
| `end_date` | str/datetime | None | 종료일 (기본: 오늘) |

**반환값**: DataFrame (OHLCV 데이터)

```
        date   open   high    low  close   volume symbol  market
0 2023-01-02  55500  56300  55100  55300  9823144 005930   KOSPI
1 2023-01-03  55200  55600  54800  55100  8234512 005930   KOSPI
```

#### 3. `get_fundamental_data(symbol, start_date, end_date)` - 펀더멘털 데이터

```python
# PER, PBR, EPS 등 조회
fundamentals = collector.get_fundamental_data(
    symbol='005930',
    start_date='2023-01-01',
    end_date='2024-01-01'
)
```

**반환값**: DataFrame

| 컬럼 | 설명 |
|------|------|
| `per` | 주가수익비율 (Price-Earnings Ratio) |
| `pbr` | 주가순자산비율 (Price-Book Ratio) |
| `eps` | 주당순이익 (Earnings Per Share) |
| `bps` | 주당순자산 (Book Value Per Share) |
| `dividend_yield` | 배당수익률 |
| `dps` | 주당배당금 |

#### 4. `get_market_cap(symbol, start_date, end_date)` - 시가총액 데이터

```python
# 시가총액 조회
market_cap = collector.get_market_cap(
    symbol='005930',
    start_date='2023-01-01',
    end_date='2024-01-01'
)
```

**반환값**: DataFrame

| 컬럼 | 설명 |
|------|------|
| `market_cap` | 시가총액 |
| `volume` | 거래량 |
| `trading_value` | 거래대금 |
| `listed_shares` | 상장주식수 |

#### 5. `collect_multiple_stocks(symbols, ...)` - 여러 종목 수집

```python
# 주요 종목 데이터 수집
symbols = ['005930', '000660', '035420', '051910']

df = collector.collect_multiple_stocks(
    symbols=symbols,
    start_date='2023-01-01',
    end_date='2024-01-01',
    save_to_db=True  # DB에 자동 저장
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `symbols` | List[str] | 필수 | 종목 코드 리스트 |
| `start_date` | str/datetime | None | 시작일 |
| `end_date` | str/datetime | None | 종료일 |
| `save_to_db` | bool | True | 데이터베이스 저장 여부 |

#### 6. `update_stock_list(market)` - 종목 리스트 업데이트

```python
# DB의 종목 리스트 업데이트
collector.update_stock_list(market="ALL")
```

---

## 미국 주식 데이터 수집

### 클래스: `USStockCollector`

**파일 위치**: `src/data_collection/us_stock_collector.py`

미국 주식 데이터는 `yfinance` 라이브러리를 사용하여 수집합니다.

### 초기화

```python
from src.data_collection.us_stock_collector import USStockCollector

collector = USStockCollector()
```

### 메서드 상세

#### 1. `get_stock_info(symbol)` - 종목 정보 조회

```python
# Apple 종목 정보
info = collector.get_stock_info('AAPL')
print(info)
```

**반환값**: Dictionary

```python
{
    'symbol': 'AAPL',
    'name': 'Apple Inc.',
    'market': 'NMS',
    'sector': 'Technology',
    'industry': 'Consumer Electronics',
    'market_cap': 2800000000000,
    'currency': 'USD'
}
```

#### 2. `get_price_data(symbol, start_date, end_date, interval)` - 가격 데이터

```python
# Apple 일봉 데이터
df = collector.get_price_data(
    symbol='AAPL',
    start_date='2023-01-01',
    end_date='2024-01-01',
    interval='1d'  # 일봉
)

# 주봉 데이터
df_weekly = collector.get_price_data('AAPL', interval='1wk')

# 월봉 데이터
df_monthly = collector.get_price_data('AAPL', interval='1mo')
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `symbol` | str | 필수 | 티커 심볼 (예: 'AAPL') |
| `start_date` | str/datetime | None | 시작일 |
| `end_date` | str/datetime | None | 종료일 |
| `interval` | str | '1d' | 데이터 간격: '1d', '1wk', '1mo' |

**반환값**: DataFrame

```
        date   open   high    low  close    volume  adj_close symbol market
0 2023-01-03 130.28 130.90 124.17 125.07  112117471     124.22   AAPL    NMS
1 2023-01-04 126.89 128.66 125.08 126.36   89113633     125.50   AAPL    NMS
```

#### 3. `get_fundamental_data(symbol)` - 펀더멘털 데이터

```python
# Apple 펀더멘털 데이터
fundamentals = collector.get_fundamental_data('AAPL')
```

**반환값**: Dictionary

| 키 | 설명 |
|------|------|
| `market_cap` | 시가총액 |
| `per` | PER (trailing P/E) |
| `pbr` | PBR (Price/Book) |
| `eps` | EPS |
| `roe` | 자기자본이익률 |
| `debt_ratio` | 부채비율 |
| `current_ratio` | 유동비율 |
| `revenue` | 매출액 |
| `operating_income` | 영업이익 |
| `net_income` | 순이익 |
| `dividend_yield` | 배당수익률 |
| `beta` | 베타 |

#### 4. `get_sp500_tickers()` - S&P 500 종목 리스트

```python
# S&P 500 전체 티커 조회
sp500 = collector.get_sp500_tickers()
print(f"S&P 500 종목 수: {len(sp500)}")
# 출력: S&P 500 종목 수: 503
```

#### 5. `get_nasdaq100_tickers()` - NASDAQ 100 종목 리스트

```python
# NASDAQ 100 전체 티커 조회
nasdaq100 = collector.get_nasdaq100_tickers()
```

#### 6. `collect_multiple_stocks(symbols, ...)` - 여러 종목 수집

```python
tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']

df = collector.collect_multiple_stocks(
    symbols=tech_stocks,
    start_date='2020-01-01',
    end_date='2024-01-01',
    save_to_db=True,
    delay=0.1  # API 제한 방지 딜레이
)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `symbols` | List[str] | 필수 | 티커 리스트 |
| `start_date` | str/datetime | None | 시작일 |
| `end_date` | str/datetime | None | 종료일 |
| `save_to_db` | bool | True | DB 저장 여부 |
| `delay` | float | 0.1 | 요청 간 딜레이(초) |

#### 7. `download_bulk_data(symbols, ...)` - 벌크 다운로드 (빠름)

```python
# 여러 종목 한번에 다운로드 (병렬 처리)
df = collector.download_bulk_data(
    symbols=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
    start_date='2020-01-01',
    end_date='2024-01-01'
)
```

> **참고**: `download_bulk_data`는 yfinance의 병렬 다운로드 기능을 사용하여 `collect_multiple_stocks`보다 훨씬 빠릅니다.

---

## 데이터 종류

### 1. 가격 데이터 (OHLCV)

| 컬럼 | 설명 |
|------|------|
| `date` | 날짜 |
| `open` | 시가 |
| `high` | 고가 |
| `low` | 저가 |
| `close` | 종가 |
| `volume` | 거래량 |
| `adj_close` | 수정 종가 (미국만) |
| `symbol` | 종목 코드 |
| `market` | 시장 |

### 2. 펀더멘털 데이터

| 컬럼 | 설명 | 비고 |
|------|------|------|
| `per` | 주가수익비율 | 낮을수록 저평가 |
| `pbr` | 주가순자산비율 | 낮을수록 저평가 |
| `eps` | 주당순이익 | 높을수록 좋음 |
| `roe` | 자기자본이익률 | 높을수록 좋음 |
| `debt_ratio` | 부채비율 | 낮을수록 좋음 |

### 3. 시가총액 데이터

| 컬럼 | 설명 |
|------|------|
| `market_cap` | 시가총액 |
| `listed_shares` | 상장주식수 |
| `trading_value` | 거래대금 |

---

## 데이터 저장

### 자동 저장 (save_to_db=True)

```python
# 수집 시 자동으로 DB에 저장
df = collector.collect_multiple_stocks(
    symbols=['005930'],
    save_to_db=True  # 이 옵션이 True면 자동 저장
)
```

### 수동 저장

```python
from src.utils.database import get_db

db = get_db()

# 가격 데이터 저장
db.save_stock_prices(df, if_exists='append')

# 펀더멘털 데이터 저장
db.save_fundamentals(fundamentals_df, if_exists='append')

# 종목 정보 저장
db.save_stock_info(info_df, if_exists='replace')
```

| if_exists 옵션 | 설명 |
|---------------|------|
| `'append'` | 기존 데이터에 추가 |
| `'replace'` | 기존 데이터 교체 |

---

## 예제 코드

### 예제 1: 한국 시장 전체 데이터 수집

```python
from datetime import datetime, timedelta
from src.data_collection.kr_stock_collector import KoreanStockCollector

def collect_korean_market():
    collector = KoreanStockCollector(use_pykrx=True)

    # 1. 종목 리스트 업데이트
    print("종목 리스트 업데이트 중...")
    collector.update_stock_list(market="ALL")

    # 2. 종목 리스트 조회
    stocks = collector.get_stock_list(market="KOSPI")
    symbols = stocks['symbol'].tolist()

    # 3. 상위 100개 종목만 수집 (예시)
    symbols = symbols[:100]

    # 4. 최근 5년 데이터 수집
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*5)

    print(f"{len(symbols)}개 종목 데이터 수집 중...")
    df = collector.collect_multiple_stocks(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        save_to_db=True
    )

    print(f"수집 완료: {len(df)} 레코드")
    return df

if __name__ == "__main__":
    collect_korean_market()
```

### 예제 2: S&P 500 전체 데이터 수집

```python
from src.data_collection.us_stock_collector import USStockCollector

def collect_sp500():
    collector = USStockCollector()

    # 1. S&P 500 티커 조회
    tickers = collector.get_sp500_tickers()
    print(f"S&P 500 종목 수: {len(tickers)}")

    # 2. 벌크 다운로드 (빠름)
    df = collector.download_bulk_data(
        symbols=tickers,
        start_date='2019-01-01',
        end_date='2024-01-01'
    )

    # 3. DB 저장
    from src.utils.database import get_db
    db = get_db()
    db.save_stock_prices(df, if_exists='append')

    print(f"수집 완료: {len(df)} 레코드")
    return df

if __name__ == "__main__":
    collect_sp500()
```

### 예제 3: 펀더멘털 데이터와 가격 데이터 병합

```python
from src.data_collection.kr_stock_collector import KoreanStockCollector
import pandas as pd

collector = KoreanStockCollector()

symbol = '005930'
start_date = '2023-01-01'
end_date = '2024-01-01'

# 가격 데이터
prices = collector.get_price_data(symbol, start_date, end_date)

# 펀더멘털 데이터
fundamentals = collector.get_fundamental_data(symbol, start_date, end_date)

# 시가총액 데이터
market_cap = collector.get_market_cap(symbol, start_date, end_date)

# 데이터 병합
merged = prices.merge(
    fundamentals[['date', 'per', 'pbr', 'eps']],
    on='date',
    how='left'
)

merged = merged.merge(
    market_cap[['date', 'market_cap']],
    on='date',
    how='left'
)

print(merged.head())
```

---

## 주의사항

### API 제한

1. **yfinance**: 과도한 요청 시 일시적으로 차단될 수 있음
   - `delay` 파라미터 사용 권장
   - 대량 다운로드 시 `download_bulk_data` 사용

2. **pykrx**: 한국거래소 서버 상태에 따라 응답 속도 달라짐
   - 장 마감 후 데이터 수집 권장
   - 주말/공휴일에는 최신 데이터 없음

### 데이터 품질

1. 누락 데이터 확인
   ```python
   print(df.isnull().sum())
   ```

2. 이상치 확인
   ```python
   print(df.describe())
   ```

3. 중복 데이터 확인
   ```python
   duplicates = df.duplicated(subset=['symbol', 'date'])
   print(f"중복 레코드: {duplicates.sum()}")
   ```

---

## 다음 단계

- [03. 기술적 지표](./03-technical-indicators.md) - 수집한 데이터에 기술적 지표 추가
- [04. 팩터 분석](./04-factor-analysis.md) - 퀀트 팩터 계산
