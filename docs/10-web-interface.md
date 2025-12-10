# 웹 인터페이스 사용 가이드

퀀트 투자 시스템의 웹 인터페이스를 사용하는 방법을 설명합니다.

## 목차

1. [개요](#개요)
2. [설치 및 실행](#설치-및-실행)
3. [기능 소개](#기능-소개)
4. [사용자 가이드](#사용자-가이드)
5. [관리자 가이드](#관리자-가이드)
6. [API 레퍼런스](#api-레퍼런스)
7. [문제 해결](#문제-해결)

---

## 개요

웹 인터페이스는 Flask 기반으로 구현되었으며, 다음 기능을 제공합니다:

- **사용자 인증**: 회원가입, 로그인, 프로필 관리
- **대시보드**: 포트폴리오 현황 및 성과 요약
- **전략 관리**: 투자 전략 생성, 수정, 복제
- **백테스트**: 전략 검증 및 성과 분석
- **데이터 관리**: 주식 데이터 수집 및 조회
- **설정**: 시스템 설정 관리
- **라이트/다크 테마**: 사용자 선호에 따른 테마 변경

---

## 설치 및 실행

### 빠른 시작

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 설정 (선택)
export FLASK_CONFIG=development
export SECRET_KEY=your-secret-key

# 3. 서버 실행
python run.py
```

### 프로덕션 환경

```bash
# Gunicorn으로 실행
gunicorn -w 4 -b 0.0.0.0:5000 "web:create_app('production')"
```

---

## 기능 소개

### 1. 대시보드

로그인 후 첫 화면으로, 다음 정보를 한눈에 확인할 수 있습니다:

- 총 백테스트 수
- 포트폴리오 개수
- 총 자산 현황
- 최고 샤프비율
- 최근 백테스트 결과
- 빠른 실행 메뉴

### 2. 전략 관리

#### 기본 전략

시스템에서 제공하는 5가지 기본 전략:

| 전략 | 설명 |
|------|------|
| 모멘텀 | 과거 12개월 수익률 기반 |
| 가치 | PBR, PER 기반 저평가 종목 |
| 퀄리티 | ROE, 부채비율 기반 우량주 |
| 멀티팩터 | 복합 팩터 가중 평균 |
| 소형주 | 시가총액 기반 |

#### 커스텀 전략

사용자가 직접 팩터 비중과 파라미터를 설정하여 전략을 생성할 수 있습니다.

### 3. 백테스트

전략의 과거 성과를 검증합니다:

- **기간 설정**: 시작일, 종료일
- **초기 자본**: 시뮬레이션 시작 금액
- **거래 비용**: 수수료, 슬리피지
- **성과 지표**: 수익률, 샤프비율, MDD 등
- **시각화**: 포트폴리오 가치 차트, 누적 수익률 차트

### 4. 데이터 관리

주식 데이터를 수집하고 관리합니다:

- **한국 시장**: KOSPI, KOSDAQ
- **미국 시장**: NYSE, NASDAQ
- **데이터 유형**: 가격(OHLCV), 재무(PER, PBR, ROE 등)

### 5. 설정

시스템 전반의 설정을 관리합니다:

- 데이터 수집 설정
- 전략 기본값
- 백테스팅 파라미터
- 데이터베이스 연결
- 기술적 지표 설정
- 알림 설정 (Telegram, Email)

---

## 사용자 가이드

### 회원가입 및 로그인

1. 홈페이지에서 "회원가입" 클릭
2. 사용자명, 이메일, 비밀번호 입력
3. 가입 완료 후 로그인

### 첫 백테스트 실행

1. 대시보드에서 "새 백테스트" 클릭
2. 백테스트 이름 입력
3. 전략 선택 (예: 멀티팩터)
4. 시장 선택 (한국/미국)
5. 기간 및 자본금 설정
6. "백테스트 실행" 클릭
7. 결과 확인

### 커스텀 전략 생성

1. "전략" 메뉴 클릭
2. "새 전략" 버튼 클릭
3. 전략 이름 및 설명 입력
4. 팩터 비중 조정 (모멘텀, 가치, 퀄리티, 사이즈)
5. 리스크 관리 설정 (손절, 최대 비중 등)
6. 저장

### 테마 변경

- 네비게이션 바의 테마 아이콘(달/해) 클릭
- 라이트 ↔ 다크 테마 전환
- 설정은 자동 저장됨

---

## 관리자 가이드

### 데이터베이스 초기화

```python
from web import create_app, db

app = create_app()
with app.app_context():
    db.create_all()
```

### 관리자 계정 생성

```python
from web import create_app, db
from web.models import User

app = create_app()
with app.app_context():
    admin = User(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    admin.is_admin = True
    db.session.add(admin)
    db.session.commit()
```

### 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| FLASK_CONFIG | 설정 환경 | development |
| FLASK_HOST | 호스트 | 0.0.0.0 |
| FLASK_PORT | 포트 | 5000 |
| FLASK_DEBUG | 디버그 모드 | true |
| SECRET_KEY | 세션 암호화 키 | (자동 생성) |
| DATABASE_URL | DB 연결 문자열 | sqlite:///... |

---

## API 레퍼런스

### 인증이 필요한 API

모든 API 요청에는 로그인이 필요합니다.

### 엔드포인트

#### 대시보드 통계

```
GET /api/dashboard/stats
```

응답:
```json
{
  "total_backtests": 10,
  "completed_backtests": 8,
  "total_portfolios": 2,
  "total_strategies": 5,
  "best_strategy": {
    "name": "멀티팩터 전략",
    "sharpe_ratio": 1.25,
    "annual_return": 0.158
  }
}
```

#### 종목 검색

```
GET /api/stock-search?q=삼성&market=KR
```

#### 테마 변경

```
POST /api/theme
Content-Type: application/json

{"theme": "dark"}
```

#### 포트폴리오 최적화

```
POST /api/portfolio-optimizer
Content-Type: application/json

{
  "symbols": ["005930", "000660", "035420"],
  "method": "mean_variance",
  "objective": "sharpe"
}
```

---

## 문제 해결

### 서버가 시작되지 않음

1. Python 버전 확인 (3.8 이상 필요)
2. 의존성 설치 확인: `pip install -r requirements.txt`
3. 포트 충돌 확인: `netstat -tlnp | grep 5000`

### 데이터베이스 오류

1. data/database 디렉토리 존재 확인
2. 쓰기 권한 확인
3. 데이터베이스 파일 손상 시 삭제 후 재생성

### 백테스트 실패

1. 데이터 수집 여부 확인
2. 선택한 기간에 데이터가 있는지 확인
3. 로그 확인: `logs/quant_investing.log`

### 테마가 적용되지 않음

1. 브라우저 캐시 삭제
2. localStorage 확인: `localStorage.getItem('quant-theme')`
3. CSS 파일 로드 확인

---

## 다음 단계

- [라즈베리파이 설치 가이드](11-raspberry-pi-setup.md)
- [윈도우 설치 가이드](12-windows-setup.md)
