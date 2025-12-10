"""
Quantitative Investing Web Application
Flask-based web interface for managing quantitative investment strategies
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
import os
from pathlib import Path

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
bcrypt = Bcrypt()


def create_app(config_name=None):
    """
    Application factory for creating Flask app

    Args:
        config_name: Configuration name ('development', 'production', 'testing')

    Returns:
        Flask application instance
    """
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    app.config.from_object(f'web.config.{config_name.capitalize()}Config')

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Ensure database directory exists
    db_path = Path(app.config.get('QUANT_DB_PATH', 'data/database'))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '로그인이 필요합니다.'
    login_manager.login_message_category = 'warning'

    # Register blueprints
    from web.routes.main import main_bp
    from web.routes.auth import auth_bp
    from web.routes.dashboard import dashboard_bp
    from web.routes.strategies import strategies_bp
    from web.routes.backtest import backtest_bp
    from web.routes.data import data_bp
    from web.routes.settings import settings_bp
    from web.routes.api import api_bp
    from web.routes.screening import screening_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(strategies_bp, url_prefix='/strategies')
    app.register_blueprint(backtest_bp, url_prefix='/backtest')
    app.register_blueprint(screening_bp, url_prefix='/screening')
    app.register_blueprint(data_bp, url_prefix='/data')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Create database tables
    with app.app_context():
        db.create_all()

        # Add new columns to existing tables if needed (for progress tracking)
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                # Check if progress column exists in backtest_results
                result = conn.execute(text("PRAGMA table_info(backtest_results)"))
                columns = [row[1] for row in result.fetchall()]

                if 'progress' not in columns:
                    conn.execute(text("ALTER TABLE backtest_results ADD COLUMN progress INTEGER DEFAULT 0"))
                if 'current_step' not in columns:
                    conn.execute(text("ALTER TABLE backtest_results ADD COLUMN current_step VARCHAR(100)"))
                if 'total_days' not in columns:
                    conn.execute(text("ALTER TABLE backtest_results ADD COLUMN total_days INTEGER"))
                if 'processed_days' not in columns:
                    conn.execute(text("ALTER TABLE backtest_results ADD COLUMN processed_days INTEGER DEFAULT 0"))
                if 'started_at' not in columns:
                    conn.execute(text("ALTER TABLE backtest_results ADD COLUMN started_at DATETIME"))
                conn.commit()
        except Exception as e:
            app.logger.warning(f"Migration warning: {e}")

    # Register error handlers
    register_error_handlers(app)

    # Register context processors
    register_context_processors(app)

    return app


def register_error_handlers(app):
    """Register custom error handlers"""

    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403


def register_context_processors(app):
    """Register context processors for templates"""

    @app.context_processor
    def inject_globals():
        """Inject global variables into templates"""
        return {
            'app_name': 'Quant Investing',
            'app_version': '1.0.0'
        }
