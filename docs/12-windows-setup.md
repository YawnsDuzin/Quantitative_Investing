# 윈도우 설치 가이드

Windows 환경에서 퀀트 투자 시스템을 설치하고 운영하는 방법을 설명합니다.

## 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [사전 설치](#사전-설치)
3. [시스템 설치](#시스템-설치)
4. [개발 환경 실행](#개발-환경-실행)
5. [프로덕션 환경 설정](#프로덕션-환경-설정)
6. [Windows 서비스 등록](#windows-서비스-등록)
7. [문제 해결](#문제-해결)

---

## 시스템 요구사항

### 최소 사양

| 구분 | 최소 | 권장 |
|------|------|------|
| OS | Windows 10 | Windows 10/11 64-bit |
| RAM | 4GB | 8GB 이상 |
| 저장소 | 5GB | 20GB 이상 |
| Python | 3.9 | 3.11 |

### 필수 소프트웨어

- Python 3.9 이상
- Git
- (선택) Visual Studio Build Tools

---

## 사전 설치

### 1. Python 설치

1. Python 공식 사이트 방문: https://www.python.org/downloads/
2. 최신 Python 3.11 다운로드
3. 설치 시 **"Add Python to PATH"** 체크 필수
4. 설치 완료 후 확인:

```powershell
python --version
pip --version
```

### 2. Git 설치

1. Git 공식 사이트 방문: https://git-scm.com/download/win
2. 다운로드 및 설치 (기본 옵션 사용)
3. 설치 확인:

```powershell
git --version
```

### 3. Visual Studio Build Tools (선택사항)

일부 Python 패키지 빌드에 필요합니다.

1. https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. "C++ 빌드 도구" 선택 설치

---

## 시스템 설치

### 1. PowerShell 관리자 권한으로 실행

시작 메뉴에서 "PowerShell" 검색 → 우클릭 → "관리자 권한으로 실행"

### 2. 프로젝트 클론

```powershell
cd C:\Users\$env:USERNAME
git clone https://github.com/YawnsDuzin/Quantitative_Investing.git
cd Quantitative_Investing
```

### 3. 가상 환경 생성

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**참고**: 스크립트 실행 권한 오류 시:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 4. 의존성 설치

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 환경 변수 설정

```powershell
# .env 파일 생성
@"
FLASK_CONFIG=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=true
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
"@ | Out-File -FilePath .env -Encoding utf8
```

### 6. 데이터베이스 초기화

```powershell
python -c "from web import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

---

## 개발 환경 실행

### 서버 시작

```powershell
# 가상 환경 활성화
.\venv\Scripts\Activate.ps1

# 서버 실행
python run.py
```

### 브라우저에서 접속

- 로컬: http://localhost:5000
- 네트워크: http://컴퓨터IP:5000

### 서버 중지

`Ctrl + C`를 눌러 중지

---

## 프로덕션 환경 설정

### 1. Waitress 설치 (WSGI 서버)

Windows에서는 Gunicorn 대신 Waitress를 사용합니다.

```powershell
pip install waitress
```

### 2. 프로덕션 실행 스크립트 생성

`run_production.py` 파일 생성:

```python
"""
Production server using Waitress
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from waitress import serve
from web import create_app

if __name__ == '__main__':
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Create app
    app = create_app('production')

    # Server configuration
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    threads = int(os.environ.get('WAITRESS_THREADS', 4))

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║   Quantitative Investing - Production Server                 ║
║   Running on http://{host}:{port}                              ║
║   Press Ctrl+C to stop                                       ║
╚══════════════════════════════════════════════════════════════╝
    """)

    serve(app, host=host, port=port, threads=threads)
```

### 3. 프로덕션 실행

```powershell
.\venv\Scripts\Activate.ps1
python run_production.py
```

---

## Windows 서비스 등록

### NSSM (Non-Sucking Service Manager) 사용

#### 1. NSSM 설치

1. https://nssm.cc/download 에서 다운로드
2. `nssm.exe`를 `C:\Windows\System32\`에 복사

#### 2. 서비스 생성 배치 파일

`install_service.bat` 파일 생성:

```batch
@echo off
echo Installing Quant Investing as Windows Service...

set SERVICE_NAME=QuantInvesting
set PYTHON_PATH=C:\Users\%USERNAME%\Quantitative_Investing\venv\Scripts\python.exe
set SCRIPT_PATH=C:\Users\%USERNAME%\Quantitative_Investing\run_production.py
set WORKING_DIR=C:\Users\%USERNAME%\Quantitative_Investing

nssm install %SERVICE_NAME% %PYTHON_PATH% %SCRIPT_PATH%
nssm set %SERVICE_NAME% AppDirectory %WORKING_DIR%
nssm set %SERVICE_NAME% AppStdout %WORKING_DIR%\logs\service_stdout.log
nssm set %SERVICE_NAME% AppStderr %WORKING_DIR%\logs\service_stderr.log
nssm set %SERVICE_NAME% Description "Quantitative Investing Web Application"
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START

echo Service installed. Starting...
nssm start %SERVICE_NAME%

echo Done!
pause
```

#### 3. 서비스 설치 및 시작

관리자 권한으로 `install_service.bat` 실행

#### 4. 서비스 관리

```powershell
# 서비스 상태 확인
nssm status QuantInvesting

# 서비스 시작
nssm start QuantInvesting

# 서비스 중지
nssm stop QuantInvesting

# 서비스 재시작
nssm restart QuantInvesting

# 서비스 제거
nssm remove QuantInvesting confirm
```

---

## 방화벽 설정

### Windows 방화벽에서 포트 열기

```powershell
# 관리자 권한으로 실행
netsh advfirewall firewall add rule name="Quant Investing" dir=in action=allow protocol=TCP localport=5000
```

### 또는 GUI에서 설정

1. Windows 검색 → "Windows Defender 방화벽"
2. "고급 설정" 클릭
3. "인바운드 규칙" → "새 규칙"
4. 포트 선택 → TCP, 5000 입력
5. 연결 허용 → 이름 지정 → 완료

---

## IIS 연동 (선택사항)

### 1. IIS 설치

```powershell
# 관리자 권한으로 실행
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole, IIS-WebServer, IIS-CGI
```

### 2. wfastcgi 설치

```powershell
pip install wfastcgi
wfastcgi-enable
```

### 3. IIS 설정

1. IIS 관리자 열기
2. 사이트 추가
3. FastCGI 설정 구성

(자세한 설정은 Microsoft 문서 참조)

---

## 문제 해결

### pip 설치 오류

```powershell
# 캐시 삭제 후 재시도
pip cache purge
pip install --no-cache-dir -r requirements.txt
```

### 포트 사용 중 오류

```powershell
# 포트 사용 확인
netstat -ano | findstr :5000

# 프로세스 종료 (PID로)
taskkill /PID <PID> /F
```

### 가상 환경 활성화 실패

```powershell
# PowerShell 실행 정책 변경
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 또는 CMD 사용
cmd
.\venv\Scripts\activate.bat
```

### 한글 인코딩 문제

```powershell
# PowerShell에서
$OutputEncoding = [System.Text.Encoding]::UTF8
```

### SQLite 잠금 오류

데이터베이스 파일을 사용 중인 다른 프로세스가 없는지 확인:

```powershell
# 파일 잠금 확인
handle.exe data\database\quant_investing.db
```

### 로그 확인

```powershell
# 서비스 로그
Get-Content .\logs\service_stdout.log -Tail 50 -Wait
Get-Content .\logs\service_stderr.log -Tail 50 -Wait
```

---

## 백업 및 복원

### 백업 스크립트 (backup.ps1)

```powershell
$date = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "C:\Backups\QuantInvesting"
$sourceDir = "C:\Users\$env:USERNAME\Quantitative_Investing"

# 백업 디렉토리 생성
New-Item -ItemType Directory -Force -Path $backupDir

# 데이터베이스 및 설정 백업
Compress-Archive -Path "$sourceDir\data", "$sourceDir\config", "$sourceDir\.env" `
    -DestinationPath "$backupDir\backup_$date.zip" -Force

Write-Host "Backup completed: $backupDir\backup_$date.zip"
```

### 자동 백업 설정 (작업 스케줄러)

1. 작업 스케줄러 열기
2. "작업 만들기" 클릭
3. 트리거: 매일 오전 3시
4. 동작: PowerShell 스크립트 실행

---

## 유용한 명령어

```powershell
# 가상 환경 활성화
.\venv\Scripts\Activate.ps1

# 서버 실행
python run.py

# 프로덕션 서버 실행
python run_production.py

# 패키지 업데이트
pip install --upgrade -r requirements.txt

# 데이터베이스 초기화
python -c "from web import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# 테스트 실행
pytest tests/
```

---

## 다음 단계

- [웹 인터페이스 사용 가이드](10-web-interface.md)
- [라즈베리파이 설치 가이드](11-raspberry-pi-setup.md)
