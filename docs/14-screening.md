# 주식 스크리닝 가이드

이 문서는 Quantitative Investing 시스템의 주식 스크리닝 기능에 대한 상세한 설명을 제공합니다.

## 목차

1. [개요](#개요)
2. [스크리닝 구조](#스크리닝-구조)
3. [스크리닝 항목](#스크리닝-항목)
4. [필터 연산자](#필터-연산자)
5. [사전 정의 템플릿](#사전-정의-템플릿)
6. [커스텀 스크리닝](#커스텀-스크리닝)
7. [투자 스타일별 스크리닝](#투자-스타일별-스크리닝)
8. [복합 스코어 계산](#복합-스코어-계산)
9. [스크리닝 워크플로우](#스크리닝-워크플로우)
10. [고급 활용법](#고급-활용법)

---

## 개요

주식 스크리닝은 투자 유니버스에서 특정 조건을 만족하는 종목을 선별하는 과정입니다. Quantitative Investing 시스템은 80개 이상의 스크리닝 항목과 다양한 필터 연산자를 제공합니다.

### 스크리닝 프로세스

```
전체 종목 유니버스
       ↓
  [필터 1] 시가총액 > 1조원
       ↓
  [필터 2] PER < 15
       ↓
  [필터 3] ROE > 15%
       ↓
  [필터 4] F-Score >= 7
       ↓
  선별된 종목 리스트
       ↓
  복합 스코어 계산 (선택)
       ↓
  최종 순위화된 종목
```

---

## 스크리닝 구조

### 모듈 구조

```
src/screening/
├── __init__.py
└── stock_screener.py
    ├── FilterOperator      # 필터 연산자 열거형
    ├── ScreeningCriteria   # 단일 스크리닝 조건
    ├── StockScreener       # 메인 스크리너 클래스
    └── ScreeningPresets    # 사전 정의 프리셋
```

### 기본 사용법

```python
from src.screening import StockScreener, FilterOperator

# 스크리너 생성
screener = StockScreener()

# 조건 추가
screener.add_criterion('per', FilterOperator.LESS_THAN, 15, 'P/E < 15')
screener.add_criterion('roe', FilterOperator.GREATER_THAN, 0.15, 'ROE > 15%')
screener.add_criterion('market_cap', FilterOperator.GREATER_THAN, 1e12, '시총 > 1조')

# 스크리닝 실행
results = screener.screen()

print(f"선별된 종목: {len(results)}개")
print(results[['symbol', 'per', 'roe', 'market_cap']])
```

---

## 스크리닝 항목

### 1. 밸류에이션 항목

| 항목 | 필드명 | 설명 | 활용 |
|------|--------|------|------|
| 시가총액 | `market_cap` | 기업 규모 | 대/중/소형주 분류 |
| 기업가치 | `enterprise_value` | EV | 인수 관점 가치 |
| PER | `per` | 주가수익비율 | 저평가 종목 발굴 |
| 선행 PER | `forward_per` | 예상 실적 기준 | 성장 고려 가치평가 |
| PBR | `pbr` | 주가순자산비율 | 자산가치 대비 평가 |
| PSR | `psr` | 주가매출비율 | 매출 대비 평가 |
| PEG | `peg_ratio` | PER/성장률 | 성장 대비 가치 |
| EV/EBITDA | `ev_to_ebitda` | 기업가치/EBITDA | 업종 간 비교 |
| EV/Revenue | `ev_to_revenue` | 기업가치/매출 | 고성장주 평가 |

**활용 예시:**
```python
# 저평가 종목 스크리닝
screener.add_criterion('per', FilterOperator.BETWEEN, (5, 15), 'PER 5~15')
screener.add_criterion('pbr', FilterOperator.LESS_THAN, 1.5, 'PBR < 1.5')
screener.add_criterion('peg_ratio', FilterOperator.LESS_THAN, 1.0, 'PEG < 1')
```

### 2. 수익성 항목

| 항목 | 필드명 | 설명 | 기준 |
|------|--------|------|------|
| ROE | `roe` | 자기자본이익률 | 15% 이상 우수 |
| ROA | `roa` | 총자산이익률 | 5% 이상 양호 |
| 매출총이익률 | `gross_margin` | 매출총이익/매출 | 업종별 상이 |
| 영업이익률 | `operating_margin` | 영업이익/매출 | 10% 이상 양호 |
| 순이익률 | `profit_margin` | 순이익/매출 | 5% 이상 양호 |
| EBITDA 마진 | `ebitda_margin` | EBITDA/매출 | 20% 이상 우수 |

**활용 예시:**
```python
# 고수익 기업 스크리닝
screener.add_criterion('roe', FilterOperator.GREATER_THAN, 0.20, 'ROE > 20%')
screener.add_criterion('operating_margin', FilterOperator.GREATER_THAN, 0.15, '영업마진 > 15%')
```

### 3. 성장 항목

| 항목 | 필드명 | 설명 | 해석 |
|------|--------|------|------|
| 매출 성장률 | `revenue_growth` | YoY 매출 증가 | 양수면 성장 |
| 이익 성장률 | `earnings_growth` | YoY 이익 증가 | 양수면 성장 |
| 분기 이익 성장률 | `earnings_quarterly_growth` | QoQ 이익 증가 | 분기 추세 |

**활용 예시:**
```python
# 성장주 스크리닝
screener.add_criterion('revenue_growth', FilterOperator.GREATER_THAN, 0.20, '매출성장 > 20%')
screener.add_criterion('earnings_growth', FilterOperator.GREATER_THAN, 0.15, '이익성장 > 15%')
```

### 4. 재무 건전성 항목

| 항목 | 필드명 | 설명 | 기준 |
|------|--------|------|------|
| 부채비율 | `debt_ratio` | 부채/자본 | 100% 미만 양호 |
| 유동비율 | `current_ratio` | 유동자산/유동부채 | 1.5 이상 양호 |
| 당좌비율 | `quick_ratio` | (유동자산-재고)/유동부채 | 1 이상 양호 |
| 이자보상배율 | `interest_coverage` | 영업이익/이자비용 | 3 이상 양호 |
| F-Score | `f_score` | 피오트로스키 스코어 | 7 이상 우수 |
| Z-Score | `z_score` | 알트만 파산위험 | 2.99 이상 안전 |
| Z-Score 영역 | `z_score_zone` | Safe/Grey/Distress | Safe 선호 |

**활용 예시:**
```python
# 재무건전성 우수 기업 스크리닝
screener.add_criterion('f_score', FilterOperator.GREATER_EQUAL, 7, 'F-Score >= 7')
screener.add_criterion('z_score', FilterOperator.GREATER_THAN, 2.99, 'Z-Score > 2.99')
screener.add_criterion('debt_ratio', FilterOperator.LESS_THAN, 50, '부채비율 < 50%')
```

### 5. 현금흐름 항목

| 항목 | 필드명 | 설명 | 해석 |
|------|--------|------|------|
| 영업현금흐름 | `operating_cash_flow` | 영업 현금 창출 | 양수 필수 |
| 잉여현금흐름 | `free_cash_flow` | 투자 후 현금 | 양수 선호 |
| FCF 수익률 | `fcf_yield` | FCF/시총 | 높을수록 좋음 |
| 현금흐름/부채 | `cf_to_debt` | 부채 상환 능력 | 높을수록 좋음 |

**활용 예시:**
```python
# 현금흐름 우수 기업 스크리닝
screener.add_criterion('free_cash_flow', FilterOperator.GREATER_THAN, 0, 'FCF > 0')
screener.add_criterion('fcf_yield', FilterOperator.GREATER_THAN, 0.05, 'FCF수익률 > 5%')
```

### 6. 배당 항목

| 항목 | 필드명 | 설명 | 기준 |
|------|--------|------|------|
| 배당수익률 | `dividend_yield` | 연배당/주가 | 2% 이상 |
| 배당금 | `dividend_rate` | 연간 배당금 | - |
| 배당성향 | `payout_ratio` | 배당/순이익 | 70% 미만 지속가능 |
| 5년 평균 배당률 | `five_year_avg_dividend_yield` | 장기 평균 | 일관성 확인 |

**활용 예시:**
```python
# 배당주 스크리닝
screener.add_criterion('dividend_yield', FilterOperator.GREATER_THAN, 0.03, '배당률 > 3%')
screener.add_criterion('payout_ratio', FilterOperator.LESS_THAN, 0.60, '배당성향 < 60%')
screener.add_criterion('f_score', FilterOperator.GREATER_EQUAL, 5, '재무건전성')
```

### 7. 리스크 항목

| 항목 | 필드명 | 설명 | 해석 |
|------|--------|------|------|
| 베타 | `beta` | 시장 대비 변동성 | 1 미만=저변동 |
| 52주 최고가 | `fifty_two_week_high` | 1년 최고 | - |
| 52주 최저가 | `fifty_two_week_low` | 1년 최저 | - |
| 52주 고점 대비 | `price_to_52w_high` | 현재/고점 | 1에 가까우면 강세 |
| 52주 범위 위치 | `price_52w_range_pct` | 범위 내 위치 | 0~1 |

**활용 예시:**
```python
# 저변동 우량주 스크리닝
screener.add_criterion('beta', FilterOperator.LESS_THAN, 1.0, '베타 < 1')

# 52주 신고가 근접 종목
screener.add_criterion('price_52w_range_pct', FilterOperator.GREATER_THAN, 0.9, '52주 상위 10%')
```

### 8. 유동성 항목

| 항목 | 필드명 | 설명 | 기준 |
|------|--------|------|------|
| 평균 거래량 | `avg_volume` | 일평균 거래량 | 100만주 이상 |
| 10일 평균 거래량 | `avg_volume_10d` | 최근 거래량 | - |
| 유동주식수 | `float_shares` | 유통 가능 주식 | - |
| 공매도 비율 | `short_percent_of_float` | 공매도/유동주식 | 10% 이상 주의 |
| 공매도 일수 | `short_ratio` | 커버까지 일수 | 5일 이상 주의 |

**활용 예시:**
```python
# 유동성 충분한 종목 스크리닝
screener.add_criterion('avg_volume', FilterOperator.GREATER_THAN, 1000000, '거래량 > 100만')

# 높은 공매도 종목 (숏스퀴즈 가능성)
screener.add_criterion('short_percent_of_float', FilterOperator.GREATER_THAN, 0.15, '공매도 > 15%')
```

### 9. 소유 구조 항목

| 항목 | 필드명 | 설명 | 해석 |
|------|--------|------|------|
| 내부자 지분율 | `held_percent_insiders` | 경영진 보유 | 높으면 이해일치 |
| 기관 지분율 | `held_percent_institutions` | 기관투자자 보유 | 높으면 안정적 |

**활용 예시:**
```python
# 기관 선호 종목
screener.add_criterion('held_percent_institutions', FilterOperator.GREATER_THAN, 0.70, '기관 > 70%')

# 내부자 매수 관심 종목
screener.add_criterion('held_percent_insiders', FilterOperator.GREATER_THAN, 0.10, '내부자 > 10%')
```

### 10. 애널리스트 항목

| 항목 | 필드명 | 설명 | 기준 |
|------|--------|------|------|
| 목표가 (평균) | `target_mean_price` | 애널리스트 평균 | - |
| 추천 점수 | `recommendation_mean` | 1~5 점수 | 2 미만=매수 |
| 추천 등급 | `recommendation_key` | buy/hold/sell | buy 선호 |
| 애널리스트 수 | `number_of_analyst_opinions` | 커버리지 | 5명 이상 |
| 상승여력 | `upside_to_target` | (목표-현재)/현재 | 양수면 상승 기대 |

**활용 예시:**
```python
# 애널리스트 추천 종목
screener.add_criterion('recommendation_mean', FilterOperator.LESS_THAN, 2.0, '강력매수~매수')
screener.add_criterion('upside_to_target', FilterOperator.GREATER_THAN, 0.20, '상승여력 > 20%')
screener.add_criterion('number_of_analyst_opinions', FilterOperator.GREATER_THAN, 5, '애널리스트 5명+')
```

### 11. 섹터/업종 항목

| 항목 | 필드명 | 설명 | 활용 |
|------|--------|------|------|
| 섹터 | `sector` | 산업 대분류 | 섹터별 필터링 |
| 업종 | `industry` | 산업 소분류 | 업종별 필터링 |

**활용 예시:**
```python
# 특정 섹터 스크리닝
screener.add_criterion('sector', FilterOperator.IN,
    ['Technology', 'Healthcare'], '기술/헬스케어 섹터')

# 특정 섹터 제외
screener.add_criterion('sector', FilterOperator.NOT_IN,
    ['Energy', 'Utilities'], '에너지/유틸리티 제외')
```

---

## 필터 연산자

### 사용 가능한 연산자

| 연산자 | 코드 | 설명 | 예시 |
|--------|------|------|------|
| 초과 | `GREATER_THAN` / `gt` | > | PER > 10 |
| 이상 | `GREATER_EQUAL` / `gte` | >= | F-Score >= 7 |
| 미만 | `LESS_THAN` / `lt` | < | 부채비율 < 100 |
| 이하 | `LESS_EQUAL` / `lte` | <= | 베타 <= 1 |
| 같음 | `EQUAL` / `eq` | = | 섹터 = 'Technology' |
| 다름 | `NOT_EQUAL` / `ne` | != | 섹터 != 'Energy' |
| 범위 | `BETWEEN` | 사이 | 시총 500억~1조 |
| 포함 | `IN` | 목록 중 하나 | 섹터 in [IT, 금융] |
| 미포함 | `NOT_IN` | 목록에 없음 | 섹터 not in [에너지] |
| 상위 N | `TOP_N` | 상위 N개 | ROE 상위 20개 |
| 하위 N | `BOTTOM_N` | 하위 N개 | PER 하위 20개 |
| 상위 % | `TOP_PCT` | 상위 %tile | 시총 상위 10% |
| 하위 % | `BOTTOM_PCT` | 하위 %tile | PBR 하위 20% |

### 연산자 사용 예시

```python
from src.screening import StockScreener, FilterOperator

screener = StockScreener()

# 숫자 비교
screener.add_criterion('per', FilterOperator.LESS_THAN, 15)
screener.add_criterion('roe', FilterOperator.GREATER_THAN, 0.15)

# 범위 지정
screener.add_criterion('market_cap', FilterOperator.BETWEEN, (1e9, 10e9))

# 목록 필터
screener.add_criterion('sector', FilterOperator.IN, ['Technology', 'Healthcare'])

# 상위/하위 선택
screener.add_criterion('f_score', FilterOperator.TOP_N, 50)  # F-Score 상위 50개
screener.add_criterion('per', FilterOperator.BOTTOM_PCT, 0.20)  # PER 하위 20%
```

---

## 사전 정의 템플릿

### 사용 가능한 템플릿

| 템플릿 | 설명 | 주요 조건 |
|--------|------|----------|
| `value` | 가치주 | 낮은 PER/PBR/PEG, 높은 ROE |
| `growth` | 성장주 | 높은 매출/이익 성장률 |
| `quality` | 우량주 | 높은 F-Score, ROE, 낮은 부채 |
| `dividend` | 배당주 | 높은 배당률, 지속가능한 배당성향 |
| `momentum` | 모멘텀 | 52주 신고가 근접, 기관 매수 |
| `small_cap_value` | 소형 가치주 | 중소형주 + 가치 조건 |
| `large_cap_quality` | 대형 우량주 | 대형주 + 품질 조건 |
| `turnaround` | 턴어라운드 | 저점 매수, 개선 중인 기업 |
| `analyst_favorites` | 애널리스트 추천 | 매수 추천, 높은 상승여력 |
| `high_short_interest` | 높은 공매도 | 숏스퀴즈 가능성 |
| `insider_buying` | 내부자 매수 | 높은 내부자 지분 |

### 템플릿 사용법

```python
from src.screening import StockScreener

screener = StockScreener()

# 템플릿 로드
screener.load_template('value')

# 스크리닝 실행
results = screener.screen()

# 템플릿 조건 확인
for c in screener.criteria:
    print(f"{c.description}")
```

### 템플릿 상세 조건

#### 가치주 (value)
```python
criteria = [
    ('per', '<', 15),           # P/E < 15
    ('pbr', '<', 1.5),          # P/B < 1.5
    ('peg_ratio', '<', 1.0),    # PEG < 1
    ('roe', '>', 0.10),         # ROE > 10%
]
```

#### 성장주 (growth)
```python
criteria = [
    ('revenue_growth', '>', 0.15),    # 매출성장 > 15%
    ('earnings_growth', '>', 0.15),   # 이익성장 > 15%
    ('gross_margin', '>', 0.30),      # 매출총이익률 > 30%
]
```

#### 우량주 (quality)
```python
criteria = [
    ('f_score', '>=', 7),          # F-Score >= 7
    ('roe', '>', 0.15),            # ROE > 15%
    ('debt_ratio', '<', 100),      # 부채비율 < 100%
    ('current_ratio', '>', 1.5),   # 유동비율 > 1.5
]
```

#### 배당주 (dividend)
```python
criteria = [
    ('dividend_yield', '>', 0.03),   # 배당률 > 3%
    ('payout_ratio', '<', 0.70),     # 배당성향 < 70%
    ('f_score', '>=', 5),            # F-Score >= 5
]
```

---

## 커스텀 스크리닝

### 조건 조합하기

```python
from src.screening import StockScreener, FilterOperator

screener = StockScreener()

# 복합 조건 추가
screener.add_criterion('market_cap', FilterOperator.GREATER_THAN, 5e9, '대형주')
screener.add_criterion('per', FilterOperator.BETWEEN, (10, 20), '적정 PER')
screener.add_criterion('roe', FilterOperator.GREATER_THAN, 0.15, '높은 ROE')
screener.add_criterion('debt_ratio', FilterOperator.LESS_THAN, 50, '낮은 부채')
screener.add_criterion('dividend_yield', FilterOperator.GREATER_THAN, 0.02, '배당')
screener.add_criterion('f_score', FilterOperator.GREATER_EQUAL, 6, '건전성')

# 스크리닝 실행
results = screener.screen(return_scores=True)

# 상위 20개 추출
top_20 = screener.get_top_stocks(n=20, sort_by='composite_score')
```

### 메서드 체이닝

```python
results = (StockScreener()
    .add_criterion('per', 'lt', 15)
    .add_criterion('roe', 'gt', 0.15)
    .add_criterion('market_cap', 'gt', 1e9)
    .screen(return_scores=True))
```

---

## 투자 스타일별 스크리닝

### 워렌 버핏 스타일

```python
from src.screening import ScreeningPresets

screener = ScreeningPresets.warren_buffett_style()
results = screener.screen()
```

조건:
- ROE > 15%
- 부채비율 < 50%
- 순이익률 > 10%
- F-Score >= 6
- PER < 20

### 피터 린치 GARP 스타일

```python
screener = ScreeningPresets.peter_lynch_garp()
results = screener.screen()
```

조건:
- PEG < 1
- 이익 성장률 > 10%
- 부채비율 < 100%

### 고배당 전략

```python
screener = ScreeningPresets.dividend_aristocrat_style()
results = screener.screen()
```

조건:
- 배당수익률 > 2%
- 배당성향 < 60%
- 부채비율 < 100%
- 시가총액 > 50억 달러

### 모멘텀 돌파 전략

```python
screener = ScreeningPresets.momentum_breakout()
results = screener.screen()
```

조건:
- 52주 범위 상위 80%
- 평균 거래량 > 50만주
- 매출 성장률 > 10%

### 딥밸류 전략

```python
screener = ScreeningPresets.deep_value()
results = screener.screen()
```

조건:
- PBR < 1.0
- Z-Score > 1.81 (파산 위험 낮음)
- 유동비율 > 1.5

---

## 복합 스코어 계산

### 스코어 구성

스크리닝 결과에 복합 스코어를 계산하여 종목 간 순위를 매길 수 있습니다.

```python
results = screener.screen(return_scores=True)

# 생성되는 스코어 컬럼
# - per_score: PER 기반 (낮을수록 높은 점수)
# - pbr_score: PBR 기반 (낮을수록 높은 점수)
# - roe_score: ROE 기반 (높을수록 높은 점수)
# - f_score_score: F-Score 기반
# - z_score_score: Z-Score 기반
# - composite_score: 종합 점수
# - composite_rank: 종합 순위
```

### 스코어 계산 방식

```
composite_score = 평균(
    value_scores,      # 밸류에이션 (PER, PBR, PEG, EV/EBITDA)
    quality_scores,    # 품질 (ROE, ROA, 마진, F-Score)
    health_scores,     # 건전성 (유동비율, Z-Score)
    debt_scores,       # 부채 (낮을수록 좋음)
    growth_scores,     # 성장 (매출/이익 성장률)
    analyst_scores     # 애널리스트 (추천 점수)
)
```

### 상위 종목 추출

```python
# 복합 스코어 기준 상위 20개
top_stocks = screener.get_top_stocks(n=20, sort_by='composite_score')

# 특정 지표 기준 정렬
by_roe = screener.get_top_stocks(n=20, sort_by='roe', ascending=False)
by_per = screener.get_top_stocks(n=20, sort_by='per', ascending=True)
```

---

## 스크리닝 워크플로우

### 완전한 스크리닝 예시

```python
from src.data_collection import ExtendedDataCollector
from src.screening import StockScreener, FilterOperator
from src.utils.database import get_db

# 1. 데이터 수집 (필요시)
collector = ExtendedDataCollector()
db = get_db()

symbols = ['AAPL', 'MSFT', 'GOOGL', ...]  # 종목 리스트
extended_data = collector.collect_extended_data(symbols, include_scores=True)
db.save_extended_fundamentals(extended_data)

# 2. 스크리너 설정
screener = StockScreener()
screener.add_criterion('market_cap', FilterOperator.GREATER_THAN, 10e9)
screener.add_criterion('per', FilterOperator.BETWEEN, (10, 25))
screener.add_criterion('roe', FilterOperator.GREATER_THAN, 0.15)
screener.add_criterion('f_score', FilterOperator.GREATER_EQUAL, 6)
screener.add_criterion('recommendation_mean', FilterOperator.LESS_THAN, 2.5)

# 3. 스크리닝 실행
results = screener.screen(return_scores=True)

# 4. 결과 분석
print(f"선별된 종목: {len(results)}개")

top_10 = results.nlargest(10, 'composite_score')
print("\n=== Top 10 종목 ===")
print(top_10[['symbol', 'sector', 'per', 'roe', 'f_score', 'composite_score']])

# 5. 섹터별 분포
sector_dist = results.groupby('sector').size()
print("\n=== 섹터별 분포 ===")
print(sector_dist.sort_values(ascending=False))
```

---

## 고급 활용법

### 동적 조건 생성

```python
def create_dynamic_screener(market_condition: str):
    screener = StockScreener()

    if market_condition == 'bull':
        # 강세장: 성장/모멘텀 중시
        screener.add_criterion('revenue_growth', FilterOperator.GREATER_THAN, 0.15)
        screener.add_criterion('price_52w_range_pct', FilterOperator.GREATER_THAN, 0.7)
    elif market_condition == 'bear':
        # 약세장: 가치/방어주 중시
        screener.add_criterion('per', FilterOperator.LESS_THAN, 12)
        screener.add_criterion('dividend_yield', FilterOperator.GREATER_THAN, 0.03)
        screener.add_criterion('beta', FilterOperator.LESS_THAN, 1.0)
    else:
        # 보합: 균형잡힌 조건
        screener.load_template('quality')

    return screener.screen()
```

### 백테스팅 연계

```python
from src.screening import StockScreener
from src.backtesting import Backtester

# 1. 스크리닝으로 종목 선정
screener = StockScreener()
screener.load_template('quality')
selected = screener.screen()
symbols = selected['symbol'].tolist()[:20]

# 2. 선정된 종목으로 백테스트
backtester = Backtester(
    symbols=symbols,
    start_date='2020-01-01',
    end_date='2023-12-31'
)
results = backtester.run()
```

### 섹터 중립 스크리닝

```python
def sector_neutral_screen(screener, top_n_per_sector=5):
    """각 섹터에서 동일하게 종목 선택"""
    results = screener.screen(return_scores=True)

    sector_balanced = []
    for sector in results['sector'].unique():
        sector_stocks = results[results['sector'] == sector]
        top_in_sector = sector_stocks.nlargest(top_n_per_sector, 'composite_score')
        sector_balanced.append(top_in_sector)

    return pd.concat(sector_balanced)
```

### 다중 스크리닝 비교

```python
templates = ['value', 'growth', 'quality', 'dividend']
results_comparison = {}

for template in templates:
    screener = StockScreener()
    screener.load_template(template)
    results = screener.screen()
    results_comparison[template] = results['symbol'].tolist()

# 공통 종목 찾기
common = set(results_comparison['value'])
for template, symbols in results_comparison.items():
    common &= set(symbols)

print(f"모든 조건 만족 종목: {common}")
```

---

## 참고

- [스크리닝 API 레퍼런스](./api-reference.md#screening)
- [데이터 수집 가이드](./13-data-collection.md)
- [백테스팅 가이드](./15-backtesting.md)
