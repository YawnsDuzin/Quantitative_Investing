# 데이터 수집 가이드

이 문서는 Quantitative Investing 시스템의 데이터 수집 기능에 대한 상세한 설명을 제공합니다.

## 목차

1. [개요](#개요)
2. [데이터 소스](#데이터-소스)
3. [수집 데이터 항목](#수집-데이터-항목)
4. [기본 데이터 수집](#기본-데이터-수집)
5. [확장 데이터 수집](#확장-데이터-수집)
6. [데이터베이스 스키마](#데이터베이스-스키마)
7. [데이터 수집 방법](#데이터-수집-방법)
8. [API 사용량 관리](#api-사용량-관리)
9. [데이터 업데이트 스케줄](#데이터-업데이트-스케줄)
10. [문제 해결](#문제-해결)

---

## 개요

Quantitative Investing 시스템은 한국(KOSPI, KOSDAQ)과 미국(NYSE, NASDAQ) 주식 시장의 데이터를 수집합니다. 수집된 데이터는 백테스팅, 스크리닝, 포트폴리오 최적화에 활용됩니다.

### 데이터 수집 구조

```
src/data_collection/
├── __init__.py
├── kr_stock_collector.py      # 한국 주식 데이터 수집
├── us_stock_collector.py      # 미국 주식 데이터 수집
└── extended_collector.py      # 확장 데이터 수집 (펀더멘털, 스코어 등)
```

---

## 데이터 소스

### 한국 주식 (KR)

| 소스 | 라이브러리 | 제공 데이터 | 특징 |
|------|-----------|------------|------|
| **한국거래소(KRX)** | `pykrx` | OHLCV, 펀더멘털, 시가총액 | 공식 데이터, 안정적 |
| **FinanceDataReader** | `FinanceDataReader` | OHLCV, 종목 목록 | 대안 소스 |

### 미국 주식 (US)

| 소스 | 라이브러리 | 제공 데이터 | 특징 |
|------|-----------|------------|------|
| **Yahoo Finance** | `yfinance` | OHLCV, 펀더멘털, 재무제표 | 무료, 포괄적 |
| **Wikipedia** | `pandas` | S&P 500, NASDAQ 100 목록 | 인덱스 구성종목 |

---

## 수집 데이터 항목

### 1. 가격 데이터 (Price Data)

| 항목 | 필드명 | 설명 | 단위 |
|------|--------|------|------|
| 시가 | `open` | 장 시작 가격 | 원/달러 |
| 고가 | `high` | 일중 최고가 | 원/달러 |
| 저가 | `low` | 일중 최저가 | 원/달러 |
| 종가 | `close` | 장 마감 가격 | 원/달러 |
| 거래량 | `volume` | 거래 주식 수 | 주 |
| 수정종가 | `adj_close` | 배당/분할 조정 종가 | 원/달러 |
| 날짜 | `date` | 거래일 | YYYY-MM-DD |
| 종목코드 | `symbol` | 종목 식별자 | 문자열 |
| 시장 | `market` | 거래소 | KOSPI/KOSDAQ/NYSE/NASDAQ |

### 2. 기본 펀더멘털 데이터 (Basic Fundamentals)

| 항목 | 필드명 | 설명 | 공식/비고 |
|------|--------|------|----------|
| 시가총액 | `market_cap` | 총 주식 가치 | 주가 × 발행주식수 |
| PER | `per` | 주가수익비율 | 주가 / EPS |
| PBR | `pbr` | 주가순자산비율 | 주가 / BPS |
| EPS | `eps` | 주당순이익 | 순이익 / 발행주식수 |
| BPS | `bps` | 주당순자산 | 자본총계 / 발행주식수 |
| ROE | `roe` | 자기자본이익률 | 순이익 / 자기자본 |
| 부채비율 | `debt_ratio` | 부채 대 자본 비율 | 부채 / 자본 × 100 |
| 유동비율 | `current_ratio` | 단기 지급능력 | 유동자산 / 유동부채 |
| 매출액 | `revenue` | 총 매출 | 원/달러 |
| 영업이익 | `operating_income` | 영업활동 이익 | 원/달러 |
| 순이익 | `net_income` | 당기순이익 | 원/달러 |

### 3. 확장 펀더멘털 데이터 (Extended Fundamentals)

#### 3.1 밸류에이션 지표

| 항목 | 필드명 | 설명 | 해석 |
|------|--------|------|------|
| 선행 PER | `forward_per` | 예상 실적 기준 PER | 낮을수록 저평가 |
| PSR | `psr` | 주가매출비율 | 낮을수록 저평가 |
| PEG | `peg_ratio` | PER/성장률 | 1 미만이면 저평가 |
| EV | `enterprise_value` | 기업가치 | 시총 + 부채 - 현금 |
| EV/EBITDA | `ev_to_ebitda` | 기업가치 대비 EBITDA | 낮을수록 저평가 |
| EV/Revenue | `ev_to_revenue` | 기업가치 대비 매출 | 낮을수록 저평가 |

#### 3.2 수익성 지표

| 항목 | 필드명 | 설명 | 기준 |
|------|--------|------|------|
| ROA | `roa` | 총자산이익률 | 5% 이상 양호 |
| 매출총이익률 | `gross_margin` | 매출총이익/매출 | 업종별 상이 |
| 영업이익률 | `operating_margin` | 영업이익/매출 | 10% 이상 양호 |
| 순이익률 | `profit_margin` | 순이익/매출 | 5% 이상 양호 |
| EBITDA 마진 | `ebitda_margin` | EBITDA/매출 | 높을수록 좋음 |

#### 3.3 성장 지표

| 항목 | 필드명 | 설명 | 비고 |
|------|--------|------|------|
| 매출 성장률 | `revenue_growth` | YoY 매출 증가율 | 양수면 성장 |
| 이익 성장률 | `earnings_growth` | YoY 이익 증가율 | 양수면 성장 |
| 분기 이익 성장률 | `earnings_quarterly_growth` | QoQ 이익 증가율 | 분기 기준 |

#### 3.4 재무 건전성 지표

| 항목 | 필드명 | 설명 | 기준 |
|------|--------|------|------|
| 당좌비율 | `quick_ratio` | (유동자산-재고)/유동부채 | 1 이상 양호 |
| 총부채 | `total_debt` | 총 부채 금액 | - |
| 총현금 | `total_cash` | 보유 현금 | - |
| 주당현금 | `total_cash_per_share` | 주당 현금 | - |
| 이자보상배율 | `interest_coverage` | 영업이익/이자비용 | 3 이상 양호 |

#### 3.5 현금흐름 지표

| 항목 | 필드명 | 설명 | 해석 |
|------|--------|------|------|
| 영업현금흐름 | `operating_cash_flow` | 영업활동 현금흐름 | 양수면 양호 |
| 잉여현금흐름 | `free_cash_flow` | FCF | 투자 후 남는 현금 |
| FCF 수익률 | `fcf_yield` | FCF/시가총액 | 높을수록 좋음 |
| 현금흐름/부채 | `cf_to_debt` | OCF/총부채 | 높을수록 좋음 |

#### 3.6 배당 지표

| 항목 | 필드명 | 설명 | 비고 |
|------|--------|------|------|
| 배당수익률 | `dividend_yield` | 연간배당/주가 | % |
| 배당금 | `dividend_rate` | 연간 배당금 | 원/달러 |
| 배당성향 | `payout_ratio` | 배당/순이익 | 70% 미만 지속가능 |
| 배당락일 | `ex_dividend_date` | 배당 기준일 | 날짜 |
| 5년 평균 배당률 | `five_year_avg_dividend_yield` | 5년 평균 | % |

#### 3.7 리스크 지표

| 항목 | 필드명 | 설명 | 해석 |
|------|--------|------|------|
| 베타 | `beta` | 시장 대비 변동성 | 1=시장과 동일 |
| 52주 최고가 | `fifty_two_week_high` | 52주 최고 | - |
| 52주 최저가 | `fifty_two_week_low` | 52주 최저 | - |
| 50일 이동평균 | `fifty_day_average` | 단기 추세 | - |
| 200일 이동평균 | `two_hundred_day_average` | 장기 추세 | - |
| 52주 고점 대비 | `price_to_52w_high` | 현재가/52주고점 | - |
| 52주 범위 위치 | `price_52w_range_pct` | 범위 내 위치 | 0~1 |

#### 3.8 거래량 & 유동성 지표

| 항목 | 필드명 | 설명 | 비고 |
|------|--------|------|------|
| 평균 거래량 | `avg_volume` | 평균 일 거래량 | 주 |
| 10일 평균 거래량 | `avg_volume_10d` | 최근 10일 평균 | 주 |
| 발행주식수 | `shares_outstanding` | 총 발행 주식 | 주 |
| 유동주식수 | `float_shares` | 유통 가능 주식 | 주 |
| 공매도 주식수 | `shares_short` | 공매도 수량 | 주 |
| 공매도 비율 | `short_ratio` | 커버까지 일수 | 일 |
| 유동주 대비 공매도 | `short_percent_of_float` | 공매도/유동주식 | % |

#### 3.9 소유 구조 지표

| 항목 | 필드명 | 설명 | 해석 |
|------|--------|------|------|
| 내부자 지분율 | `held_percent_insiders` | 경영진/임원 보유 | 높으면 경영진 신뢰 |
| 기관 지분율 | `held_percent_institutions` | 기관투자자 보유 | 높으면 안정적 |

#### 3.10 애널리스트 데이터

| 항목 | 필드명 | 설명 | 해석 |
|------|--------|------|------|
| 목표가 (상한) | `target_high_price` | 최고 목표가 | - |
| 목표가 (하한) | `target_low_price` | 최저 목표가 | - |
| 목표가 (평균) | `target_mean_price` | 평균 목표가 | - |
| 목표가 (중앙값) | `target_median_price` | 중앙값 목표가 | - |
| 추천 점수 | `recommendation_mean` | 평균 추천 (1~5) | 1=강력매수, 5=매도 |
| 추천 등급 | `recommendation_key` | 텍스트 등급 | buy/hold/sell |
| 애널리스트 수 | `number_of_analyst_opinions` | 커버 애널리스트 수 | - |
| 상승여력 | `upside_to_target` | (목표가-현재가)/현재가 | % |

### 4. 재무 건전성 스코어 (Financial Scores)

#### 4.1 피오트로스키 F-Score (0~9점)

| 구성요소 | 필드명 | 기준 | 점수 |
|----------|--------|------|------|
| 순이익 양수 | `positive_net_income` | 순이익 > 0 | 1 |
| 영업현금흐름 양수 | `positive_ocf` | OCF > 0 | 1 |
| ROA 개선 | `roa_improvement` | 당기 ROA > 전기 ROA | 1 |
| 이익 품질 | `earnings_quality` | OCF > 순이익 | 1 |
| 부채비율 감소 | `debt_decrease` | 당기 부채비율 < 전기 | 1 |
| 유동비율 증가 | `current_ratio_increase` | 당기 유동비율 > 전기 | 1 |
| 주식 희석 없음 | `no_dilution` | 주식수 증가 없음 | 1 |
| 매출총이익률 개선 | `gross_margin_increase` | 당기 > 전기 | 1 |
| 자산회전율 개선 | `asset_turnover_increase` | 당기 > 전기 | 1 |

**해석:**
- 8-9점: 우수한 재무 건전성
- 6-7점: 양호
- 4-5점: 보통
- 0-3점: 주의 필요

#### 4.2 알트만 Z-Score (파산 위험 지표)

| 구성요소 | 필드명 | 가중치 |
|----------|--------|--------|
| 운전자본/총자산 | `working_capital_to_assets` | 1.2 |
| 이익잉여금/총자산 | `retained_earnings_to_assets` | 1.4 |
| EBIT/총자산 | `ebit_to_assets` | 3.3 |
| 시가총액/총부채 | `market_cap_to_liabilities` | 0.6 |
| 매출/총자산 | `revenue_to_assets` | 1.0 |

**공식:** Z = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E

**해석:**
| Z-Score | 영역 | 해석 |
|---------|------|------|
| > 2.99 | Safe | 재무적으로 안전 |
| 1.81 ~ 2.99 | Grey | 불확실, 주의 필요 |
| < 1.81 | Distress | 파산 위험 높음 |

---

## 기본 데이터 수집

### 한국 주식 수집

```python
from src.data_collection import KoreanStockCollector

collector = KoreanStockCollector(use_pykrx=True)

# 종목 목록 가져오기
stock_list = collector.get_stock_list(market="ALL")  # KOSPI + KOSDAQ

# 가격 데이터 수집
price_data = collector.get_price_data(
    symbol="005930",  # 삼성전자
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# 펀더멘털 데이터 수집
fundamental_data = collector.get_fundamental_data(
    symbol="005930",
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# 시가총액 데이터 수집
market_cap_data = collector.get_market_cap(
    symbol="005930",
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# 여러 종목 동시 수집
symbols = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, 네이버
combined_data = collector.collect_multiple_stocks(
    symbols=symbols,
    start_date="2023-01-01",
    end_date="2024-01-01",
    save_to_db=True
)
```

### 미국 주식 수집

```python
from src.data_collection import USStockCollector

collector = USStockCollector()

# S&P 500 종목 목록 가져오기
sp500_tickers = collector.get_sp500_tickers()

# NASDAQ 100 종목 목록 가져오기
nasdaq100_tickers = collector.get_nasdaq100_tickers()

# 가격 데이터 수집
price_data = collector.get_price_data(
    symbol="AAPL",
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# 펀더멘털 데이터 수집
fundamentals = collector.get_fundamental_data(symbol="AAPL")

# 대량 다운로드 (더 빠름)
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
bulk_data = collector.download_bulk_data(
    symbols=symbols,
    start_date="2023-01-01",
    end_date="2024-01-01"
)
```

---

## 확장 데이터 수집

### 확장 펀더멘털 수집

```python
from src.data_collection import ExtendedDataCollector

collector = ExtendedDataCollector()

# 단일 종목 확장 데이터
extended_data = collector.get_extended_fundamentals("AAPL")

print(f"PEG Ratio: {extended_data['peg_ratio']}")
print(f"EV/EBITDA: {extended_data['ev_to_ebitda']}")
print(f"FCF Yield: {extended_data['fcf_yield']}")
print(f"Analyst Target: {extended_data['target_mean_price']}")
```

### 재무 건전성 스코어 계산

```python
# Piotroski F-Score 계산
f_score_data = collector.calculate_piotroski_f_score("AAPL")
print(f"F-Score: {f_score_data['f_score']}/9")

# Altman Z-Score 계산
z_score_data = collector.calculate_altman_z_score("AAPL")
print(f"Z-Score: {z_score_data['z_score']:.2f}")
print(f"Zone: {z_score_data['z_score_zone']}")
```

### 추가 데이터 수집

```python
# 배당 이력
dividends = collector.get_dividend_history("AAPL")

# 애널리스트 추천
recommendations = collector.get_analyst_recommendations("AAPL")

# 기관 보유 현황
institutional = collector.get_institutional_holders("AAPL")

# 내부자 거래
insider_txns = collector.get_insider_transactions("AAPL")

# 실적 이력 (실제 vs 예상)
earnings = collector.get_earnings_history("AAPL")
```

### 여러 종목 확장 데이터 수집

```python
# 여러 종목 확장 데이터 + 스코어 수집
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
extended_df = collector.collect_extended_data(
    symbols=symbols,
    include_scores=True,  # F-Score, Z-Score 포함
    delay=0.5  # API 제한 방지
)

# 결과 확인
print(extended_df[['symbol', 'peg_ratio', 'f_score', 'z_score', 'recommendation_key']])
```

---

## 데이터베이스 스키마

### 테이블 구조

#### stock_prices (가격 데이터)
```sql
CREATE TABLE stock_prices (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    adj_close REAL,
    market TEXT,
    UNIQUE(symbol, date)
);
```

#### stock_fundamentals (기본 펀더멘털)
```sql
CREATE TABLE stock_fundamentals (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    market_cap REAL,
    per REAL,
    pbr REAL,
    eps REAL,
    bps REAL,
    roe REAL,
    debt_ratio REAL,
    current_ratio REAL,
    revenue REAL,
    operating_income REAL,
    net_income REAL,
    UNIQUE(symbol, date)
);
```

#### extended_fundamentals (확장 펀더멘털)
```sql
CREATE TABLE extended_fundamentals (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    -- 60개 이상의 지표 포함
    -- 밸류에이션, 수익성, 성장, 현금흐름, 배당, 리스크,
    -- 거래량, 소유구조, 애널리스트 데이터 등
    UNIQUE(symbol, date)
);
```

#### financial_scores (재무 스코어)
```sql
CREATE TABLE financial_scores (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    f_score INTEGER,           -- Piotroski F-Score (0-9)
    z_score REAL,              -- Altman Z-Score
    z_score_zone TEXT,         -- Safe/Grey/Distress
    -- F-Score 구성요소 9개
    -- Z-Score 구성요소 5개
    UNIQUE(symbol, date)
);
```

---

## 데이터 수집 방법

### 수집 워크플로우

```
1. 종목 목록 업데이트
   └─> stock_info 테이블 갱신

2. 가격 데이터 수집
   └─> stock_prices 테이블 저장

3. 기본 펀더멘털 수집
   └─> stock_fundamentals 테이블 저장

4. 확장 펀더멘털 수집
   └─> extended_fundamentals 테이블 저장

5. 재무 스코어 계산
   └─> financial_scores 테이블 저장

6. 부가 데이터 수집 (선택)
   └─> dividend_history, analyst_recommendations,
       institutional_holdings, insider_transactions,
       earnings_history 테이블 저장
```

### 전체 수집 예시

```python
from src.data_collection import KoreanStockCollector, USStockCollector, ExtendedDataCollector
from src.utils.database import get_db

db = get_db()

# 1. 한국 주식 수집
kr_collector = KoreanStockCollector()
kr_collector.update_stock_list(market="ALL")

kr_symbols = db.get_all_symbols(market="KOSPI")[:100]  # 상위 100개
kr_prices = kr_collector.collect_multiple_stocks(kr_symbols, save_to_db=True)

# 2. 미국 주식 수집
us_collector = USStockCollector()
us_collector.update_stock_list(index="SP500")

us_symbols = us_collector.get_sp500_tickers()[:100]
us_prices = us_collector.download_bulk_data(us_symbols)
db.save_stock_prices(us_prices)

# 3. 확장 데이터 수집 (미국)
ext_collector = ExtendedDataCollector()
extended_data = ext_collector.collect_extended_data(us_symbols[:50], include_scores=True)
db.save_extended_fundamentals(extended_data)
```

---

## API 사용량 관리

### 제한 사항

| API | 제한 | 권장 딜레이 |
|-----|------|------------|
| pykrx (KRX) | 제한 없음 | 0.1초 |
| FinanceDataReader | 제한 없음 | 0.1초 |
| yfinance | 2,000 요청/시간 | 0.5초 |

### 권장 사항

```python
# 1. 대량 다운로드 활용 (미국)
collector.download_bulk_data(symbols)  # 개별 요청보다 훨씬 빠름

# 2. 적절한 딜레이 설정
collector.collect_extended_data(symbols, delay=0.5)

# 3. 점진적 수집
for batch in batches(symbols, size=50):
    data = collector.collect_extended_data(batch)
    db.save_extended_fundamentals(data)
    time.sleep(10)  # 배치 간 휴식
```

---

## 데이터 업데이트 스케줄

### 권장 스케줄

| 데이터 유형 | 업데이트 주기 | 시간 |
|------------|--------------|------|
| 가격 데이터 | 매일 | 시장 마감 후 |
| 기본 펀더멘털 | 주간 | 주말 |
| 확장 펀더멘털 | 주간 | 주말 |
| 재무 스코어 | 분기 | 실적 발표 후 |
| 배당 이력 | 월간 | 월초 |
| 애널리스트 | 주간 | 주말 |

### 자동화 예시 (cron)

```bash
# 매일 18:00 - 가격 데이터
0 18 * * 1-5 python -m src.scripts.update_prices

# 매주 토요일 00:00 - 펀더멘털
0 0 * * 6 python -m src.scripts.update_fundamentals

# 매월 1일 00:00 - 전체 갱신
0 0 1 * * python -m src.scripts.full_update
```

---

## 문제 해결

### 일반적인 오류

#### 1. API 요청 실패
```python
# 재시도 로직 추가
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_with_retry(symbol):
    return collector.get_price_data(symbol)
```

#### 2. 데이터 누락
```python
# 누락 데이터 확인
missing = df[df['close'].isna()]
print(f"Missing data: {len(missing)} rows")

# 누락 종목 재수집
missing_symbols = missing['symbol'].unique()
collector.collect_multiple_stocks(missing_symbols)
```

#### 3. 데이터베이스 연결 오류
```python
# 연결 재설정
db = get_db()
db.close()
db = DatabaseManager()  # 새 인스턴스 생성
```

### 로그 확인

```python
# 로그 레벨 설정
import logging
logging.getLogger('src.data_collection').setLevel(logging.DEBUG)

# 로그 파일 확인
tail -f logs/quant_investing.log
```

---

## 참고

- [yfinance 문서](https://github.com/ranaroussi/yfinance)
- [pykrx 문서](https://github.com/sharebook-kr/pykrx)
- [FinanceDataReader 문서](https://github.com/FinanceData/FinanceDataReader)
