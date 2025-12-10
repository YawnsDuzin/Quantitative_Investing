#!/usr/bin/env python
"""
퀀트 투자 시스템 - Flask 웹 애플리케이션 엔트리포인트

사용법:
    python -m src.web.app
    또는
    python src/web/app.py

환경 변수:
    FLASK_ENV: 실행 환경 (development, production)
    FLASK_DEBUG: 디버그 모드 (1 또는 0)
    FLASK_PORT: 포트 번호 (기본값: 5000)
    FLASK_HOST: 호스트 주소 (기본값: 127.0.0.1)
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.web import create_app, socketio


def main():
    """Flask 애플리케이션 실행"""
    # 환경 설정
    env = os.environ.get('FLASK_ENV', 'development')
    debug = os.environ.get('FLASK_DEBUG', '1' if env == 'development' else '0') == '1'
    port = int(os.environ.get('FLASK_PORT', 5000))
    host = os.environ.get('FLASK_HOST', '127.0.0.1')

    # 앱 생성
    app = create_app(env)

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                 퀀트 투자 시스템 웹 서버                           ║
╠══════════════════════════════════════════════════════════════════╣
║  환경: {env:12s}                                               ║
║  디버그: {'활성화' if debug else '비활성화':10s}                                             ║
║  주소: http://{host}:{port:<6d}                                       ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # SocketIO로 서버 실행
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True  # 개발 환경용
    )


if __name__ == '__main__':
    main()
