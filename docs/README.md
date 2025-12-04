# Quantitative Investing System - Documentation

퀀트 투자 시스템의 상세 매뉴얼입니다.

## 문서 목차

| 문서 | 설명 |
|------|------|
| [01. 시작하기](./01-getting-started.md) | 설치, 환경 설정, 빠른 시작 가이드 |
| [02. 데이터 수집](./02-data-collection.md) | 한국/미국 주식 데이터 수집 방법 |
| [03. 기술적 지표](./03-technical-indicators.md) | 기술적 지표 계산 및 사용법 |
| [04. 팩터 분석](./04-factor-analysis.md) | 퀀트 팩터(모멘텀, 가치, 퀄리티 등) 계산 |
| [05. 투자 전략](./05-strategies.md) | 내장 투자 전략 및 커스텀 전략 작성법 |
| [06. 포트폴리오 최적화](./06-portfolio-optimizer.md) | 동일가중, 평균-분산 최적화 등 |
| [07. 백테스팅](./07-backtesting.md) | 전략 시뮬레이션 및 성과 분석 |
| [08. 설정 파일](./08-configuration.md) | config.yaml 상세 설정 항목 |
| [09. 데이터베이스](./09-database.md) | 데이터베이스 스키마 및 사용법 |

## 시스템 아키텍처

```
Quantitative_Investing/
├── config/
│   └── config.yaml          # 전체 설정 파일
├── data/
│   └── database/            # SQLite 데이터베이스
├── src/
│   ├── data_collection/     # 데이터 수집 모듈
│   │   ├── kr_stock_collector.py   # 한국 주식
│   │   └── us_stock_collector.py   # 미국 주식
│   ├── data_processing/     # 데이터 처리 모듈
│   │   ├── indicators.py           # 기술적 지표
│   │   └── feature_engineering.py  # 팩터 계산
│   ├── strategies/          # 투자 전략 모듈
│   │   ├── base_strategy.py        # 기본 전략 클래스
│   │   └── quant_strategies.py     # 퀀트 전략들
│   ├── portfolio/           # 포트폴리오 모듈
│   │   └── portfolio_optimizer.py  # 최적화
│   ├── backtesting/         # 백테스팅 모듈
│   │   ├── backtester.py           # 백테스팅 엔진
│   │   ├── performance_metrics.py  # 성과 지표
│   │   └── visualizer.py           # 시각화
│   └── utils/               # 유틸리티 모듈
│       ├── config_loader.py        # 설정 로더
│       ├── database.py             # DB 관리
│       ├── logger.py               # 로깅
│       └── helpers.py              # 헬퍼 함수
├── tests/                   # 테스트 코드
└── notebooks/               # Jupyter 노트북
```

## 주요 기능

### 1. 데이터 수집
- **한국 시장**: KOSPI, KOSDAQ (pykrx, FinanceDataReader 사용)
- **미국 시장**: NYSE, NASDAQ (yfinance 사용)
- 가격 데이터 (OHLCV), 펀더멘털 데이터, 시가총액 데이터

### 2. 팩터 분석
- **모멘텀 팩터**: 12개월 수익률 (최근 1개월 제외)
- **가치 팩터**: PBR, PER 기반
- **퀄리티 팩터**: ROE, 부채비율 기반
- **사이즈 팩터**: 시가총액 기반

### 3. 투자 전략
- 모멘텀 전략 (Momentum Strategy)
- 가치 전략 (Value Strategy)
- 퀄리티 전략 (Quality Strategy)
- 멀티팩터 전략 (Multi-Factor Strategy)
- 사이즈 전략 (Size Strategy)

### 4. 포트폴리오 최적화
- 동일가중 (Equal Weight)
- 평균-분산 최적화 (Mean-Variance Optimization)
  - 최대 샤프비율
  - 최소 변동성
  - 최대 수익률

### 5. 백테스팅
- 리밸런싱 시뮬레이션
- 거래 비용 및 슬리피지 반영
- 다양한 성과 지표 계산

## 빠른 시작

```python
from src.data_collection.kr_stock_collector import KoreanStockCollector
from src.strategies.quant_strategies import create_strategy
from src.backtesting.backtester import run_backtest

# 1. 데이터 수집
collector = KoreanStockCollector()
data = collector.collect_multiple_stocks(['005930', '000660'], save_to_db=True)

# 2. 전략 생성
strategy = create_strategy('momentum')

# 3. 백테스팅 실행
results, summary = run_backtest(strategy, data, initial_capital=100000000)

# 4. 결과 확인
print(summary)
```

## 라이선스

MIT License
