# 08. 설정 파일 (Configuration)

`config/config.yaml` 파일의 모든 설정 항목에 대한 상세 매뉴얼입니다.

## 목차

1. [설정 파일 구조](#설정-파일-구조)
2. [데이터 수집 설정](#데이터-수집-설정)
3. [전략 설정](#전략-설정)
4. [백테스팅 설정](#백테스팅-설정)
5. [데이터베이스 설정](#데이터베이스-설정)
6. [로깅 설정](#로깅-설정)
7. [기술적 지표 설정](#기술적-지표-설정)
8. [종목 스크리닝 설정](#종목-스크리닝-설정)
9. [알림 설정](#알림-설정)
10. [설정 사용법](#설정-사용법)

---

## 설정 파일 구조

**파일 위치**: `config/config.yaml`

```yaml
# 전체 구조
data_collection:     # 데이터 수집 설정
  kr_stock:          # 한국 주식
  us_stock:          # 미국 주식
  update_schedule:   # 업데이트 스케줄
  start_date:        # 시작 날짜
  end_date:          # 종료 날짜

strategy:            # 전략 설정
  rebalancing_frequency:  # 리밸런싱 주기
  max_positions:          # 최대 종목 수
  factor_weights:         # 팩터 가중치

backtesting:         # 백테스팅 설정
  initial_capital:   # 초기 자본금
  commission:        # 수수료
  slippage:          # 슬리피지

database:            # 데이터베이스 설정
  type:              # 데이터베이스 종류
  path:              # 파일 경로

logging:             # 로깅 설정
  level:             # 로그 레벨
  file:              # 로그 파일

indicators:          # 기술적 지표 설정
  sma_periods:       # 이동평균 기간
  rsi_period:        # RSI 기간

screening:           # 종목 스크리닝 설정
  defaults:          # 기본 조건
  price:             # 가격 조건
  technical:         # 기술적 조건
  fundamental:       # 펀더멘털 조건
  presets:           # 프리셋 전략
  results:           # 결과 설정

notification:        # 알림 설정
  telegram:          # 텔레그램 설정
  email:             # 이메일 설정
```

---

## 데이터 수집 설정

### data_collection

```yaml
data_collection:
  # 한국 주식 설정
  kr_stock:
    market: ["KOSPI", "KOSDAQ"]     # 수집할 시장
    min_market_cap: 50000000000     # 최소 시가총액 (500억 원)
    exclude_sectors: []              # 제외할 섹터

  # 미국 주식 설정
  us_stock:
    market: ["NYSE", "NASDAQ"]      # 수집할 시장
    min_market_cap: 1000000000      # 최소 시가총액 (10억 달러)
    exclude_sectors: []              # 제외할 섹터

  # 데이터 업데이트 스케줄
  update_schedule:
    daily: "09:00"                  # 일간 업데이트 시간
    fundamental: "weekly"           # 펀더멘털 업데이트 주기

  # 데이터 기간
  start_date: "2018-01-01"          # 수집 시작일
  end_date: null                    # 종료일 (null = 오늘)
```

### 상세 설명

| 항목 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `kr_stock.market` | List[str] | ["KOSPI", "KOSDAQ"] | 한국 시장 (KOSPI, KOSDAQ) |
| `kr_stock.min_market_cap` | int | 50000000000 | 최소 시가총액 (원) |
| `us_stock.market` | List[str] | ["NYSE", "NASDAQ"] | 미국 시장 |
| `us_stock.min_market_cap` | int | 1000000000 | 최소 시가총액 (USD) |
| `start_date` | str | "2018-01-01" | 데이터 수집 시작일 |
| `end_date` | str/null | null | 종료일 (null = 오늘) |

### 사용 예시

```python
from src.utils.config_loader import get_config

config = get_config()

# 한국 주식 설정 조회
kr_config = config.get('data_collection.kr_stock')
markets = kr_config['market']  # ['KOSPI', 'KOSDAQ']
min_cap = kr_config['min_market_cap']  # 50000000000

# 날짜 범위 조회
start_date = config.get('data_collection.start_date')  # '2018-01-01'
```

---

## 전략 설정

### strategy

```yaml
strategy:
  # 리밸런싱 설정
  rebalancing_frequency: "monthly"  # daily, weekly, monthly, quarterly
  rebalancing_day: 1                # 월간 리밸런싱일 (1일)

  # 포트폴리오 설정
  max_positions: 20                 # 최대 보유 종목 수
  min_positions: 10                 # 최소 보유 종목 수
  equal_weight: true                # 동일 가중 여부

  # 리스크 관리
  stop_loss: 0.15                   # 손절 비율 (15%)
  take_profit: null                 # 익절 비율 (null = 사용 안함)
  max_position_size: 0.1            # 최대 개별 종목 비중 (10%)

  # 팩터 가중치 (합계 = 1.0)
  factor_weights:
    momentum: 0.4                   # 모멘텀 40%
    value: 0.3                      # 가치 30%
    quality: 0.2                    # 퀄리티 20%
    size: 0.1                       # 사이즈 10%
```

### 상세 설명

| 항목 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `rebalancing_frequency` | str | "monthly" | 리밸런싱 주기 |
| `rebalancing_day` | int | 1 | 월간 리밸런싱 날짜 |
| `max_positions` | int | 20 | 최대 보유 종목 수 |
| `min_positions` | int | 10 | 최소 보유 종목 수 |
| `equal_weight` | bool | true | 동일 가중 적용 여부 |
| `stop_loss` | float | 0.15 | 손절 비율 (15%) |
| `take_profit` | float/null | null | 익절 비율 |
| `max_position_size` | float | 0.1 | 최대 개별 종목 비중 |

### 리밸런싱 주기 옵션

| 값 | 설명 | 연간 리밸런싱 횟수 |
|------|------|------------------|
| `daily` | 매일 | ~252회 |
| `weekly` | 매주 금요일 | ~52회 |
| `monthly` | 매월 초 | 12회 |
| `quarterly` | 분기 초 | 4회 |

### 팩터 가중치

가중치의 합은 자동으로 1.0으로 정규화됩니다.

```yaml
# 모멘텀 집중 전략
factor_weights:
  momentum: 0.7
  value: 0.1
  quality: 0.1
  size: 0.1

# 가치 집중 전략
factor_weights:
  momentum: 0.2
  value: 0.5
  quality: 0.2
  size: 0.1

# 밸런스 전략
factor_weights:
  momentum: 0.25
  value: 0.25
  quality: 0.25
  size: 0.25
```

---

## 백테스팅 설정

### backtesting

```yaml
backtesting:
  initial_capital: 100000000    # 초기 자본금 (1억 원)
  commission: 0.0015            # 거래 수수료 (0.15%)
  slippage: 0.001               # 슬리피지 (0.1%)

  # 성과 평가
  benchmark: "SPY"              # 벤치마크 (SPY, KOSPI 등)
  risk_free_rate: 0.03          # 무위험 수익률 (연 3%)
```

### 상세 설명

| 항목 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `initial_capital` | int | 100000000 | 초기 자본금 |
| `commission` | float | 0.0015 | 거래 수수료 (0.15%) |
| `slippage` | float | 0.001 | 슬리피지 (0.1%) |
| `benchmark` | str | "SPY" | 벤치마크 지수 |
| `risk_free_rate` | float | 0.03 | 연간 무위험 수익률 |

### 비용 설정 가이드

**한국 시장**:
```yaml
backtesting:
  commission: 0.00015     # 증권사 수수료 (0.015%)
  slippage: 0.001         # 슬리피지 (0.1%)
  # 참고: 매도 시 증권거래세 0.23% 별도
```

**미국 시장**:
```yaml
backtesting:
  commission: 0.0         # 대부분 무료
  slippage: 0.0005        # 슬리피지 (0.05%)
```

---

## 데이터베이스 설정

### database

```yaml
database:
  type: "sqlite"                              # sqlite, postgresql, mysql
  path: "data/database/quant_investing.db"    # SQLite 경로

  # PostgreSQL 설정 (type: postgresql일 때)
  # host: "localhost"
  # port: 5432
  # name: "quant_investing"
  # user: "user"
  # password: "password"

  # MySQL 설정 (type: mysql일 때)
  # host: "localhost"
  # port: 3306
  # name: "quant_investing"
  # user: "root"
  # password: "password"
```

### 데이터베이스 타입별 설정

#### SQLite (기본, 권장)

```yaml
database:
  type: "sqlite"
  path: "data/database/quant_investing.db"
```

**장점**: 설치 불필요, 파일 기반, 백업 간편

#### PostgreSQL

```yaml
database:
  type: "postgresql"
  host: "localhost"
  port: 5432
  name: "quant_investing"
  user: "postgres"
  password: "your_password"
```

**장점**: 대용량 데이터, 동시 접속, 고급 기능

#### MySQL

```yaml
database:
  type: "mysql"
  host: "localhost"
  port: 3306
  name: "quant_investing"
  user: "root"
  password: "your_password"
```

---

## 로깅 설정

### logging

```yaml
logging:
  level: "INFO"                                              # DEBUG, INFO, WARNING, ERROR
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/quant_investing.log"                           # 로그 파일 경로
  max_bytes: 10485760                                        # 최대 파일 크기 (10MB)
  backup_count: 5                                            # 백업 파일 수
```

### 로그 레벨

| 레벨 | 설명 | 용도 |
|------|------|------|
| `DEBUG` | 상세 디버그 정보 | 개발/디버깅 |
| `INFO` | 일반 정보 | 운영 (권장) |
| `WARNING` | 경고 메시지 | 잠재적 문제 |
| `ERROR` | 오류 메시지 | 실패한 작업 |

### 로그 파일 관리

- `max_bytes`: 파일이 이 크기에 도달하면 새 파일 생성
- `backup_count`: 유지할 이전 로그 파일 수

```
logs/
├── quant_investing.log       # 현재 로그
├── quant_investing.log.1     # 이전 로그 1
├── quant_investing.log.2     # 이전 로그 2
└── ...
```

---

## 기술적 지표 설정

### indicators

```yaml
indicators:
  # 이동평균
  sma_periods: [20, 50, 200]     # SMA 계산 기간
  ema_periods: [12, 26]          # EMA 계산 기간

  # 모멘텀 지표
  rsi_period: 14                 # RSI 기간
  macd_fast: 12                  # MACD 빠른 EMA
  macd_slow: 26                  # MACD 느린 EMA
  macd_signal: 9                 # MACD 시그널 기간

  # 변동성 지표
  bollinger_period: 20           # 볼린저 밴드 기간
  bollinger_std: 2               # 표준편차 배수
  atr_period: 14                 # ATR 기간
```

### 상세 설명

| 항목 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `sma_periods` | List[int] | [20, 50, 200] | SMA 계산 기간 |
| `ema_periods` | List[int] | [12, 26] | EMA 계산 기간 |
| `rsi_period` | int | 14 | RSI 기간 |
| `macd_fast` | int | 12 | MACD 빠른 EMA |
| `macd_slow` | int | 26 | MACD 느린 EMA |
| `macd_signal` | int | 9 | MACD 시그널 기간 |
| `bollinger_period` | int | 20 | 볼린저 밴드 기간 |
| `bollinger_std` | float | 2 | 볼린저 표준편차 배수 |
| `atr_period` | int | 14 | ATR 기간 |

---

## 종목 스크리닝 설정

### screening

```yaml
screening:
  # 기본 조건
  defaults:
    exclude_administrative: true  # 관리종목 제외
    exclude_trading_halt: true    # 거래정지 제외
    exclude_etf: true             # ETF 제외
    min_market_cap: 50000000000   # 최소 시가총액 (500억)
    min_volume: 10000             # 최소 거래량

  # 가격 조건
  price:
    min_price: 1000       # 최소 주가
    max_price: null       # 최대 주가 (null = 무제한)

  # 기술적 지표 조건
  technical:
    rsi_oversold: 30      # RSI 과매도 기준
    rsi_overbought: 70    # RSI 과매수 기준
    sma_periods: [20, 50, 200]  # 이동평균 기간

  # 펀더멘털 조건
  fundamental:
    max_per: 20           # 최대 PER
    max_pbr: 3.0          # 최대 PBR
    min_roe: 5            # 최소 ROE (%)
    max_debt_ratio: 200   # 최대 부채비율 (%)

  # 프리셋 전략
  presets:
    default: "value"      # 기본 프리셋 전략
    # 사용 가능: value, growth, momentum, dividend,
    #           small_cap_value, quality, turnaround,
    #           oversold_bounce, breakout, income

  # 결과 설정
  results:
    max_stocks: 50        # 최대 결과 종목 수
    sort_by: "market_cap" # 정렬 기준
    sort_ascending: false # 정렬 방향
```

### 상세 설명

| 항목 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `defaults.exclude_administrative` | bool | true | 관리종목 제외 |
| `defaults.exclude_trading_halt` | bool | true | 거래정지 제외 |
| `defaults.exclude_etf` | bool | true | ETF 제외 |
| `defaults.min_market_cap` | int | 50000000000 | 최소 시가총액 (500억) |
| `defaults.min_volume` | int | 10000 | 최소 거래량 |
| `price.min_price` | int | 1000 | 최소 주가 |
| `technical.rsi_oversold` | int | 30 | RSI 과매도 기준 |
| `technical.rsi_overbought` | int | 70 | RSI 과매수 기준 |
| `fundamental.max_per` | float | 20 | 최대 PER |
| `fundamental.max_pbr` | float | 3.0 | 최대 PBR |
| `fundamental.min_roe` | float | 5 | 최소 ROE (%) |
| `presets.default` | str | "value" | 기본 프리셋 |
| `results.max_stocks` | int | 50 | 최대 결과 종목 수 |

### 프리셋 전략 옵션

| 값 | 설명 |
|------|------|
| `value` | 가치 투자 (낮은 PER/PBR, 높은 ROE) |
| `growth` | 성장 투자 (높은 EPS/매출 성장률) |
| `momentum` | 모멘텀 (이동평균 돌파, RSI) |
| `dividend` | 배당 투자 (고배당, 재무 안정) |
| `small_cap_value` | 소형 가치주 |
| `quality` | 퀄리티 (높은 ROE/ROA) |
| `turnaround` | 턴어라운드 (저점 매수) |
| `oversold_bounce` | 과매도 반등 |
| `breakout` | 돌파 (신고가, 골든크로스) |
| `income` | 인컴 (고배당 대형주) |

### 사용 예시

```python
from src.utils.config_loader import get_config
from src.screening import get_preset_strategy

config = get_config()

# 기본 프리셋 조회
default_preset = config.get('screening.presets.default', 'value')

# 프리셋으로 스크리너 생성
screener = get_preset_strategy(default_preset)

# 설정값으로 조건 생성
max_per = config.get('screening.fundamental.max_per', 20)
min_roe = config.get('screening.fundamental.min_roe', 5)
```

---

## 알림 설정

### notification

```yaml
notification:
  enabled: false                 # 알림 활성화 여부

  telegram:
    enabled: false               # 텔레그램 알림 사용
    bot_token: ""                # 봇 토큰
    chat_id: ""                  # 채팅 ID

  email:
    enabled: false               # 이메일 알림 사용
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    sender: ""                   # 발신자 이메일
    receiver: ""                 # 수신자 이메일
    password: ""                 # 앱 비밀번호
```

### 텔레그램 설정 방법

1. @BotFather로 봇 생성
2. 봇 토큰 받기
3. @userinfobot으로 채팅 ID 확인
4. 설정 파일에 입력

```yaml
notification:
  enabled: true
  telegram:
    enabled: true
    bot_token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    chat_id: "987654321"
```

### 이메일 설정 방법 (Gmail)

1. Google 계정 → 보안 → 앱 비밀번호 생성
2. 생성된 앱 비밀번호 사용

```yaml
notification:
  enabled: true
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    sender: "your.email@gmail.com"
    receiver: "target.email@example.com"
    password: "xxxx xxxx xxxx xxxx"  # 앱 비밀번호
```

---

## 설정 사용법

### ConfigLoader 클래스

**파일 위치**: `src/utils/config_loader.py`

```python
from src.utils.config_loader import get_config, reload_config

# 설정 로드 (싱글톤)
config = get_config()

# 설정 새로고침
config = reload_config()
```

### 설정값 조회

```python
# 단일 값 조회
value = config.get('strategy.max_positions', default=20)

# 중첩된 키 (점 표기법)
commission = config.get('backtesting.commission', default=0.0015)

# 섹션 전체 조회
strategy_config = config.get_strategy_config()
database_config = config.get_database_config()
```

### 환경변수 사용

`.env` 파일로 민감한 정보를 관리할 수 있습니다:

```bash
# config/.env
DB_PASSWORD=your_secure_password
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
```

```python
from src.utils.config_loader import get_config

config = get_config()
db_password = config.get_env('DB_PASSWORD')
```

### 설정 수정 및 저장

```python
# 설정 수정
config.update_config('strategy.max_positions', 30)

# 파일로 저장
config.save_config('config/config_backup.yaml')
```

---

## 예제: 전체 설정 파일

```yaml
# config/config.yaml - 완전한 예제

# 데이터 수집 설정
data_collection:
  kr_stock:
    market: ["KOSPI", "KOSDAQ"]
    min_market_cap: 50000000000
    exclude_sectors: []
  us_stock:
    market: ["NYSE", "NASDAQ"]
    min_market_cap: 1000000000
    exclude_sectors: []
  update_schedule:
    daily: "09:00"
    fundamental: "weekly"
  start_date: "2018-01-01"
  end_date: null

# 전략 설정
strategy:
  rebalancing_frequency: "monthly"
  rebalancing_day: 1
  max_positions: 20
  min_positions: 10
  equal_weight: true
  stop_loss: 0.15
  take_profit: null
  max_position_size: 0.1
  factor_weights:
    momentum: 0.4
    value: 0.3
    quality: 0.2
    size: 0.1

# 백테스팅 설정
backtesting:
  initial_capital: 100000000
  commission: 0.0015
  slippage: 0.001
  benchmark: "SPY"
  risk_free_rate: 0.03

# 데이터베이스 설정
database:
  type: "sqlite"
  path: "data/database/quant_investing.db"

# 로깅 설정
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/quant_investing.log"
  max_bytes: 10485760
  backup_count: 5

# 기술적 지표 설정
indicators:
  sma_periods: [20, 50, 200]
  ema_periods: [12, 26]
  rsi_period: 14
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9
  bollinger_period: 20
  bollinger_std: 2
  atr_period: 14

# 알림 설정
notification:
  enabled: false
  telegram:
    enabled: false
    bot_token: ""
    chat_id: ""
  email:
    enabled: false
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    sender: ""
    receiver: ""
    password: ""
```

---

## 다음 단계

- [09. 데이터베이스](./09-database.md) - 데이터베이스 스키마 및 사용법
- [10. 종목 스크리닝](./10-stock-screener.md) - 조건 기반 종목 필터링
