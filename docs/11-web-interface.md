# 웹 인터페이스 가이드

## 개요

퀀트 투자 시스템은 Flask 기반의 웹 인터페이스를 제공합니다. 이를 통해 백테스팅, 전략 관리,
데이터 수집, 종목 스크리닝 등의 기능을 시각적으로 사용할 수 있습니다.

### 주요 특징

- **통합 대시보드**: 백테스트 결과, 포트폴리오 현황 한눈에 확인
- **종목 스크리닝**: 프리셋 전략 및 커스텀 조건으로 종목 필터링
- **비동기 작업 처리**: 오래 걸리는 작업을 백그라운드에서 실행
- **반응형 UI**: Bootstrap 5 기반의 모바일 친화적 디자인
- **사용자 인증**: 회원가입, 로그인, 개인별 데이터 관리

## 설치 및 실행

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 서버 실행

```bash
# 기본 실행
python run.py

# 환경 변수 설정 후 실행
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
python run.py
```

### 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `FLASK_CONFIG` | 실행 환경 (development/production) | development |
| `FLASK_DEBUG` | 디버그 모드 | true |
| `FLASK_PORT` | 포트 번호 | 5000 |
| `FLASK_HOST` | 호스트 주소 | 0.0.0.0 |

## 메뉴 구조

### 1. 대시보드 (/dashboard)
- 최근 백테스트 결과 요약
- 포트폴리오 현황
- 전략 성과 분석

### 2. 전략 (/strategies)
- 투자 전략 관리
- 새 전략 생성 및 설정

### 3. 백테스트 (/backtest)
- 백테스트 실행
- 결과 분석 및 시각화
- 성과 지표 확인

### 4. 스크리닝 (/screening)
- **프리셋 스크리닝**: 미리 정의된 투자 전략으로 빠른 필터링
- **커스텀 스크리닝**: 개별 조건 조합으로 맞춤 필터링
- **스크리닝 이력**: 과거 실행 결과 조회

### 5. 데이터 (/data)
- 주식 데이터 수집
- 데이터베이스 관리

### 6. 설정 (/settings)
- 사용자 설정
- 시스템 설정

## 스크리닝 기능

### 프리셋 스크리닝

미리 정의된 10가지 투자 전략을 선택하여 빠르게 종목을 필터링합니다.

**제공 프리셋:**
| 프리셋 | 설명 |
|--------|------|
| 가치주 발굴 | 저PER, 저PBR 종목 |
| 성장주 발굴 | 높은 매출/이익 성장률 |
| 배당주 발굴 | 높은 배당수익률 |
| 모멘텀 전략 | 상승 추세 종목 |
| 퀄리티 전략 | 재무 건전성 우수 |
| 소형 가치주 | 소형주 중 저평가 종목 |
| GARP 전략 | 합리적 가격의 성장주 |
| 역발상 전략 | 과매도 반등 기대 |
| 듀얼 모멘텀 | 절대/상대 모멘텀 결합 |
| 통합 스코어 | 종합 점수 기반 |

### 커스텀 스크리닝

개별 조건을 직접 선택하고 조합하여 나만의 스크리닝 전략을 구성합니다.

**조건 카테고리:**
- **가격 조건**: 현재가 범위, 등락률, 52주 신고가/신저가
- **기술적 조건**: 이동평균, RSI, MACD, 볼린저밴드
- **펀더멘털 조건**: PER, PBR, ROE, 배당수익률, 부채비율
- **시장 조건**: 시가총액, 거래량, 거래대금

**조건 결합:**
- AND: 모든 조건을 만족하는 종목
- OR: 하나라도 만족하는 종목

## API 엔드포인트

### 스크리닝 API

#### 프리셋 목록 조회
```
GET /screening/api/presets
```

#### 프리셋 상세 정보
```
GET /screening/api/presets/{preset_name}
```

#### 조건 목록 조회
```
GET /screening/api/conditions
```

#### 프리셋 스크리닝 실행
```
POST /screening/api/run/preset
Content-Type: application/json

{
  "preset_name": "value",
  "market": "KR",
  "params": {
    "max_per": 15.0,
    "max_pbr": 1.5
  }
}
```

#### 커스텀 스크리닝 실행
```
POST /screening/api/run/custom
Content-Type: application/json

{
  "conditions": [
    {"class_name": "PERBelow", "params": {"threshold": 10}},
    {"class_name": "ROEAbove", "params": {"threshold": 15}}
  ],
  "combine_mode": "AND",
  "market": "KR"
}
```

#### 스크리닝 상태 조회
```
GET /screening/api/status/{result_id}
```

#### 스크리닝 결과 조회
```
GET /screening/api/results/{result_id}
```

## 프로젝트 구조

```
web/
├── __init__.py              # Flask 앱 팩토리
├── config.py                # 설정 클래스
├── models/
│   ├── __init__.py
│   ├── user.py              # 사용자 모델
│   ├── backtest.py          # 백테스트 모델
│   ├── portfolio.py         # 포트폴리오 모델
│   ├── strategy.py          # 전략 모델
│   └── screening.py         # 스크리닝 모델
├── routes/
│   ├── __init__.py
│   ├── main.py              # 메인 페이지
│   ├── auth.py              # 인증
│   ├── dashboard.py         # 대시보드
│   ├── strategies.py        # 전략
│   ├── backtest.py          # 백테스트
│   ├── screening.py         # 스크리닝
│   ├── data.py              # 데이터
│   ├── settings.py          # 설정
│   └── api.py               # API
├── forms/                   # WTForms 폼 클래스
├── templates/               # Jinja2 템플릿
│   ├── base.html
│   ├── auth/
│   ├── dashboard/
│   ├── backtest/
│   ├── screening/           # 스크리닝 템플릿
│   │   ├── index.html
│   │   ├── preset.html
│   │   ├── custom.html
│   │   ├── results.html
│   │   └── history.html
│   └── ...
└── static/                  # 정적 파일
    ├── css/
    └── js/
```

## 데이터베이스 모델

### ScreeningResult

스크리닝 실행 결과를 저장합니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | Primary Key |
| user_id | Integer | 사용자 ID (FK) |
| name | String | 스크리닝 이름 |
| market | String | 시장 (KR/US) |
| screening_type | String | 유형 (preset/custom) |
| preset_name | String | 프리셋 이름 |
| conditions_json | Text | 조건 JSON |
| parameters_json | Text | 파라미터 JSON |
| total_stocks | Integer | 전체 종목 수 |
| filtered_count | Integer | 필터링 결과 수 |
| results_json | Text | 결과 데이터 JSON |
| status | String | 상태 (pending/running/completed/failed) |
| progress | Integer | 진행률 (0-100) |
| created_at | DateTime | 생성일 |
| completed_at | DateTime | 완료일 |

### SavedScreener

저장된 스크리너 설정을 관리합니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | Primary Key |
| user_id | Integer | 사용자 ID (FK) |
| name | String | 스크리너 이름 |
| market | String | 시장 |
| screening_type | String | 유형 |
| conditions_json | Text | 조건 JSON |
| parameters_json | Text | 파라미터 JSON |

## 확장 가이드

### 새로운 프리셋 추가

`web/routes/screening.py`의 `PRESET_STRATEGIES` 딕셔너리에 추가:

```python
PRESET_STRATEGIES = {
    'my_preset': {
        'name': 'my_preset',
        'display_name': '나만의 전략',
        'description': '전략 설명...',
        'parameters': [
            {'name': 'param1', 'display_name': '파라미터1', 'type': 'float', 'default': 10.0},
        ]
    }
}
```

### 새로운 조건 추가

`CONDITION_CATEGORIES`에 조건 추가:

```python
CONDITION_CATEGORIES = {
    'my_category': {
        'name': '새 카테고리',
        'conditions': [
            {
                'class_name': 'MyCondition',
                'display_name': '새 조건',
                'params': [{'name': 'threshold', 'type': 'float', 'default': 50}]
            }
        ]
    }
}
```

## 다음 단계

- [ ] 실시간 주가 데이터 연동
- [ ] 스크리닝 결과 알림 기능
- [ ] 포트폴리오 관리 강화
- [ ] 차트 시각화 확장
- [ ] 모바일 앱 지원
