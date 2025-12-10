# 라즈베리파이 설치 가이드

라즈베리파이에서 퀀트 투자 시스템을 설치하고 운영하는 방법을 설명합니다.

## 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [기본 설정](#기본-설정)
3. [시스템 설치](#시스템-설치)
4. [웹 서버 설정](#웹-서버-설정)
5. [자동 시작 설정](#자동-시작-설정)
6. [보안 설정](#보안-설정)
7. [성능 최적화](#성능-최적화)
8. [문제 해결](#문제-해결)

---

## 시스템 요구사항

### 하드웨어

| 구분 | 최소 사양 | 권장 사양 |
|------|----------|----------|
| 모델 | Raspberry Pi 3B+ | Raspberry Pi 4 (4GB+) |
| RAM | 2GB | 4GB 이상 |
| 저장소 | 16GB SD 카드 | 32GB+ SD 카드 또는 SSD |
| 네트워크 | Wi-Fi 또는 유선 | 유선 권장 |

### 소프트웨어

- Raspberry Pi OS (64-bit 권장)
- Python 3.9 이상
- Git

---

## 기본 설정

### 1. 라즈베리파이 OS 설치

1. Raspberry Pi Imager 다운로드: https://www.raspberrypi.com/software/
2. SD 카드에 Raspberry Pi OS (64-bit) 설치
3. SSH 활성화 설정

### 2. 초기 설정

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y git python3-pip python3-venv python3-dev \
    build-essential libffi-dev libssl-dev \
    libatlas-base-dev libopenblas-dev

# 타임존 설정 (한국)
sudo timedatectl set-timezone Asia/Seoul
```

### 3. 메모리 최적화 (2GB RAM인 경우)

```bash
# Swap 크기 증가
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

## 시스템 설치

### 1. 프로젝트 클론

```bash
cd ~
git clone https://github.com/YawnsDuzin/Quantitative_Investing.git
cd Quantitative_Investing
```

### 2. 가상 환경 생성

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치

```bash
# pip 업그레이드
pip install --upgrade pip

# 의존성 설치 (라즈베리파이용 최적화)
pip install wheel
pip install numpy pandas  # 먼저 설치
pip install -r requirements.txt
```

**참고**: 라즈베리파이에서 일부 패키지(예: TA-Lib)는 설치에 시간이 오래 걸릴 수 있습니다.

### 4. 데이터베이스 초기화

```bash
python -c "from web import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 5. 환경 변수 설정

```bash
# .env 파일 생성
cat > .env << 'EOF'
FLASK_CONFIG=production
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
EOF

# 권한 설정
chmod 600 .env
```

### 6. 테스트 실행

```bash
source venv/bin/activate
python run.py
```

브라우저에서 `http://라즈베리파이IP:5000` 접속 확인

---

## 웹 서버 설정

### Gunicorn + Nginx 설정

#### 1. Gunicorn 서비스 생성

```bash
sudo nano /etc/systemd/system/quant-investing.service
```

내용:

```ini
[Unit]
Description=Quantitative Investing Web Application
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/Quantitative_Investing
Environment="PATH=/home/pi/Quantitative_Investing/venv/bin"
EnvironmentFile=/home/pi/Quantitative_Investing/.env
ExecStart=/home/pi/Quantitative_Investing/venv/bin/gunicorn \
    --workers 2 \
    --threads 2 \
    --bind unix:quant-investing.sock \
    --access-logfile /var/log/quant-investing/access.log \
    --error-logfile /var/log/quant-investing/error.log \
    "web:create_app('production')"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### 2. 로그 디렉토리 생성

```bash
sudo mkdir -p /var/log/quant-investing
sudo chown pi:www-data /var/log/quant-investing
```

#### 3. 서비스 활성화

```bash
sudo systemctl daemon-reload
sudo systemctl enable quant-investing
sudo systemctl start quant-investing
sudo systemctl status quant-investing
```

#### 4. Nginx 설치 및 설정

```bash
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/quant-investing
```

내용:

```nginx
server {
    listen 80;
    server_name _;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/pi/Quantitative_Investing/quant-investing.sock;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /static {
        alias /home/pi/Quantitative_Investing/web/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    client_max_body_size 16M;
}
```

#### 5. Nginx 설정 활성화

```bash
sudo ln -s /etc/nginx/sites-available/quant-investing /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## 자동 시작 설정

### 부팅 시 자동 시작

위에서 설정한 systemd 서비스가 부팅 시 자동으로 시작됩니다.

```bash
# 상태 확인
sudo systemctl is-enabled quant-investing
sudo systemctl is-enabled nginx
```

### 서비스 관리 명령어

```bash
# 서비스 시작
sudo systemctl start quant-investing

# 서비스 중지
sudo systemctl stop quant-investing

# 서비스 재시작
sudo systemctl restart quant-investing

# 로그 확인
sudo journalctl -u quant-investing -f
```

---

## 보안 설정

### 1. 방화벽 설정

```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Fail2ban 설정

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. HTTPS 설정 (Let's Encrypt)

도메인이 있는 경우:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 4. 보안 헤더 추가

Nginx 설정에 추가:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

---

## 성능 최적화

### 1. RAM 사용 최적화

`/boot/config.txt` 수정:

```
# GPU 메모리 최소화 (헤드리스 운영 시)
gpu_mem=16
```

### 2. SD 카드 수명 연장

```bash
# 임시 파일을 RAM에 저장
echo 'tmpfs /tmp tmpfs defaults,noatime,mode=1777,size=100M 0 0' | sudo tee -a /etc/fstab
echo 'tmpfs /var/log tmpfs defaults,noatime,mode=0755,size=50M 0 0' | sudo tee -a /etc/fstab
```

### 3. SQLite 최적화

대용량 데이터의 경우 외부 SSD 사용 권장:

```bash
# 외부 SSD 마운트
sudo mkdir -p /mnt/ssd
sudo mount /dev/sda1 /mnt/ssd

# 데이터베이스 이동
mv ~/Quantitative_Investing/data/database /mnt/ssd/
ln -s /mnt/ssd/database ~/Quantitative_Investing/data/database
```

---

## 문제 해결

### 메모리 부족

```bash
# 현재 메모리 사용량 확인
free -h

# 프로세스별 메모리 사용량
ps aux --sort=-%mem | head -10

# Gunicorn 워커 수 줄이기
# --workers 1 로 변경
```

### 패키지 설치 실패

```bash
# 개별 패키지 설치 시도
pip install --no-cache-dir package_name

# 시스템 패키지로 설치
sudo apt install python3-numpy python3-pandas
```

### 서비스 시작 실패

```bash
# 로그 확인
sudo journalctl -u quant-investing -n 100 --no-pager

# 권한 확인
ls -la /home/pi/Quantitative_Investing/

# 소켓 파일 권한
sudo chown pi:www-data /home/pi/Quantitative_Investing/quant-investing.sock
```

### 네트워크 문제

```bash
# IP 주소 확인
ip addr show

# 고정 IP 설정
sudo nano /etc/dhcpcd.conf
```

추가:
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8
```

---

## 유용한 명령어 모음

```bash
# 시스템 상태 확인
htop

# 디스크 사용량
df -h

# 온도 확인
vcgencmd measure_temp

# 전체 서비스 상태
sudo systemctl status quant-investing nginx

# 애플리케이션 로그
tail -f /var/log/quant-investing/access.log
tail -f /var/log/quant-investing/error.log

# 백업
tar -czvf backup_$(date +%Y%m%d).tar.gz ~/Quantitative_Investing/data
```

---

## 다음 단계

- [윈도우 설치 가이드](12-windows-setup.md)
- [웹 인터페이스 사용 가이드](10-web-interface.md)
