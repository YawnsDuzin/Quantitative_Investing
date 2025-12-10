"""
Web Application Module
Flask 웹 애플리케이션 모듈

스크리닝 기능을 위한 웹 인터페이스를 제공합니다.
"""

from flask import Flask
from flask_socketio import SocketIO

# SocketIO 인스턴스 (전역)
socketio = SocketIO()


def create_app(config_name: str = 'default') -> Flask:
    """
    Flask 앱 팩토리

    Args:
        config_name: 설정 이름 ('default', 'development', 'production')

    Returns:
        Flask 앱 인스턴스
    """
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # 설정 로드
    app.config['SECRET_KEY'] = 'quant-investing-secret-key-change-in-production'
    app.config['JSON_AS_ASCII'] = False  # 한글 JSON 지원

    # SocketIO 초기화
    socketio.init_app(app, async_mode='threading', cors_allowed_origins="*")

    # 블루프린트 등록
    from .api.screening import screening_bp
    from .api.tasks import tasks_bp

    app.register_blueprint(screening_bp, url_prefix='/api/screening')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')

    # 메인 라우트
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
