# 웹 인터페이스 가이드

## 개요

퀀트 투자 시스템은 Flask 기반의 웹 인터페이스를 제공합니다. 이를 통해 스크리닝 기능을
시각적으로 사용하고, 실시간으로 작업 진행 상황을 모니터링할 수 있습니다.

### 주요 특징

- **비동기 작업 처리**: 오래 걸리는 스크리닝 작업을 백그라운드에서 실행
- **실시간 진행 상황**: WebSocket을 통한 실시간 진행률 및 로그 업데이트
- **반응형 UI**: Bootstrap 5 기반의 모바일 친화적 디자인
- **작업 관리**: 진행 중인 작업 모니터링 및 취소 기능

## 설치 및 실행

### 의존성 설치

```bash
pip install flask flask-socketio python-socketio gevent gevent-websocket
```

또는 전체 의존성 설치:

```bash
pip install -r requirements.txt
```

### 서버 실행

```bash
# 기본 실행 (개발 모드)
python src/web/app.py

# 또는 모듈로 실행
python -m src.web.app
```

### 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `FLASK_ENV` | 실행 환경 (development/production) | development |
| `FLASK_DEBUG` | 디버그 모드 | 1 (개발 환경) |
| `FLASK_PORT` | 포트 번호 | 5000 |
| `FLASK_HOST` | 호스트 주소 | 127.0.0.1 |

### 프로덕션 실행

```bash
export FLASK_ENV=production
export FLASK_DEBUG=0
export FLASK_HOST=0.0.0.0
python src/web/app.py
```

## 페이지 구조

### 1. 홈 (/)

시스템 개요 및 주요 기능 소개 페이지입니다.

### 2. 스크리닝 (/screening)

스크리닝 기능의 메인 페이지로, 두 가지 모드를 선택할 수 있습니다:
- 프리셋 스크리닝
- 커스텀 스크리닝

### 3. 프리셋 스크리닝 (/screening/preset)

미리 정의된 투자 전략을 선택하여 스크리닝을 실행합니다.

**사용 방법:**
1. 시장 선택 (한국/미국)
2. 프리셋 전략 선택
3. 파라미터 조정 (선택사항)
4. 스크리닝 실행

**제공 프리셋:**
- 가치주 발굴: 저PER, 저PBR 종목
- 성장주 발굴: 높은 매출/이익 성장률
- 배당주 발굴: 높은 배당수익률
- 모멘텀 전략: 상승 추세 종목
- GARP 전략: 합리적 가격의 성장주
- 소형 가치주: 소형주 중 저평가 종목
- 퀄리티 전략: 재무 건전성 우수
- 역발상 전략: 과매도 반등 기대
- 듀얼 모멘텀: 절대/상대 모멘텀 결합
- 통합 스코어: 종합 점수 기반

### 4. 커스텀 스크리닝 (/screening/custom)

개별 조건을 직접 조합하여 스크리닝을 실행합니다.

**사용 방법:**
1. 시장 선택
2. 카테고리 선택 (가격/기술적/펀더멘털/시장)
3. 조건 선택 및 파라미터 입력
4. 조건 추가 (여러 개 가능)
5. 조건 결합 방식 선택 (AND/OR)
6. 스크리닝 실행

**조건 카테고리:**
- 가격 조건: 가격 범위, 등락률, 신고가/신저가 등
- 기술적 조건: 이동평균, RSI, MACD, 볼린저밴드 등
- 펀더멘털 조건: PER, PBR, ROE, 배당수익률 등
- 시장 조건: 시가총액, 거래량, 외국인/기관 매매 등

### 5. 작업 관리 (/tasks)

실행 중인 작업과 완료된 작업을 확인하고 관리합니다.

**기능:**
- 전체 작업 목록 조회
- 작업 상태별 필터링 (실행 중/완료/실패)
- 작업 상세 정보 조회 (진행률, 로그)
- 실행 중인 작업 취소

## API 엔드포인트

### 스크리닝 API

#### 프리셋 목록 조회
```
GET /api/screening/presets
```

응답:
```json
{
  "presets": [
    {
      "name": "value_investing",
      "display_name": "가치주 발굴",
      "description": "저PER, 저PBR 종목을 발굴합니다."
    }
  ]
}
```

#### 프리셋 상세 정보
```
GET /api/screening/presets/{preset_name}/info?market=KR
```

응답:
```json
{
  "name": "value_investing",
  "display_name": "가치주 발굴",
  "description": "...",
  "parameters": [
    {
      "name": "max_per",
      "display_name": "최대 PER",
      "type": "float",
      "default": 10.0
    }
  ]
}
```

#### 조건 목록 조회
```
GET /api/screening/conditions
```

#### 프리셋 스크리닝 실행
```
POST /api/screening/run/preset
Content-Type: application/json

{
  "preset_name": "value_investing",
  "market": "KR",
  "params": {
    "max_per": 15.0
  }
}
```

응답:
```json
{
  "success": true,
  "task_id": "uuid-string",
  "message": "스크리닝 작업이 시작되었습니다."
}
```

#### 커스텀 스크리닝 실행
```
POST /api/screening/run/custom
Content-Type: application/json

{
  "conditions": [
    {
      "class_name": "PERBelow",
      "params": {"threshold": 10.0}
    },
    {
      "class_name": "PBRBelow",
      "params": {"threshold": 1.0}
    }
  ],
  "combine_mode": "AND",
  "market": "KR"
}
```

### 작업 관리 API

#### 작업 목록 조회
```
GET /api/tasks/
```

#### 작업 상태 조회
```
GET /api/tasks/{task_id}
```

#### 작업 취소
```
POST /api/tasks/{task_id}/cancel
```

#### 작업 결과 조회
```
GET /api/tasks/{task_id}/result
```

## WebSocket 이벤트

네임스페이스: `/screening`

### 서버 → 클라이언트

#### progress
작업 진행 상황 업데이트

```javascript
socket.on('progress', (data) => {
  console.log(data.task_id, data.percentage, data.message);
});
```

#### completed
작업 완료 알림

```javascript
socket.on('completed', (data) => {
  console.log(data.task_id, data.result);
});
```

#### error
작업 오류 알림

```javascript
socket.on('error', (data) => {
  console.error(data.task_id, data.error);
});
```

## 프로젝트 구조

```
src/web/
├── __init__.py          # Flask 앱 팩토리
├── app.py               # 엔트리포인트
├── routes.py            # 메인 페이지 라우트
├── task_manager.py      # 백그라운드 작업 관리
├── api/
│   ├── __init__.py
│   ├── screening.py     # 스크리닝 API
│   └── tasks.py         # 작업 관리 API
├── templates/
│   ├── base.html        # 기본 레이아웃
│   ├── index.html       # 홈 페이지
│   ├── screening.html   # 스크리닝 메인
│   ├── screening_preset.html   # 프리셋 스크리닝
│   ├── screening_custom.html   # 커스텀 스크리닝
│   └── tasks.html       # 작업 관리
└── static/
    ├── css/
    │   └── style.css    # 커스텀 스타일
    └── js/
        ├── app.js       # 공통 JavaScript
        └── screening.js # 스크리닝 JavaScript
```

## 확장 가이드

### 새로운 페이지 추가

1. `routes.py`에 라우트 추가:
```python
@main_bp.route('/new-page')
def new_page():
    return render_template('new_page.html')
```

2. `templates/new_page.html` 생성:
```html
{% extends "base.html" %}
{% block content %}
<h1>새 페이지</h1>
{% endblock %}
```

### 새로운 API 추가

1. `api/` 디렉토리에 새 모듈 생성
2. Blueprint 등록 (`__init__.py`)

```python
# api/new_api.py
from flask import Blueprint, jsonify

new_bp = Blueprint('new', __name__)

@new_bp.route('/endpoint')
def endpoint():
    return jsonify({'success': True})
```

```python
# __init__.py
from .api.new_api import new_bp
app.register_blueprint(new_bp, url_prefix='/api/new')
```

## 트러블슈팅

### WebSocket 연결 실패

1. Flask-SocketIO 설치 확인:
```bash
pip install flask-socketio python-socketio
```

2. 브라우저 콘솔에서 WebSocket 지원 확인

3. 방화벽 설정 확인 (포트 5000)

### 작업이 시작되지 않음

1. 백그라운드 스레드 제한 확인
2. 메모리 사용량 확인
3. 로그 확인:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 스크리닝 결과가 없음

1. 데이터베이스 연결 확인
2. 조건 파라미터 확인 (너무 엄격한 조건)
3. 시장 데이터 존재 여부 확인

## 보안 고려사항

### 프로덕션 배포 시

1. `SECRET_KEY` 변경:
```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secure-key')
```

2. CORS 설정:
```python
socketio.init_app(app, cors_allowed_origins=['https://yourdomain.com'])
```

3. HTTPS 사용 권장

4. 인증/인가 시스템 추가 (필요시)

## 다음 단계

- [ ] 사용자 인증 시스템
- [ ] 스크리닝 결과 저장/내보내기
- [ ] 포트폴리오 관리 페이지
- [ ] 백테스팅 UI
- [ ] 알림 설정 페이지
