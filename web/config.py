"""
Flask Configuration for Quantitative Investing Web Application
"""
import os
from pathlib import Path
from datetime import timedelta

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Base configuration"""

    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'quant-investing-secret-key-change-in-production'

    # Database - PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:postgres@localhost:5432/quant_web'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Quantitative system database connection
    QUANT_DB_URI = os.environ.get('QUANT_DATABASE_URL') or \
        'postgresql://postgres:postgres@localhost:5432/quant_investing'

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # File upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    UPLOAD_FOLDER = BASE_DIR / 'data' / 'uploads'

    # Pagination
    ITEMS_PER_PAGE = 20

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Chart settings
    CHART_DEFAULT_THEME = 'light'  # 'light' or 'dark'

    # Backtest settings
    BACKTEST_TIMEOUT = 300  # 5 minutes max for backtest

    # Data collection settings
    DATA_UPDATE_INTERVAL = 3600  # 1 hour in seconds


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

    # PostgreSQL for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:postgres@localhost:5432/quant_web'

    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'

    # Disable CSRF for easier API testing (enable in production)
    WTF_CSRF_ENABLED = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Require a strong secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'prod-secret-key-must-be-set'

    @classmethod
    def init_app(cls, app):
        """Validate production configuration"""
        if not os.environ.get('SECRET_KEY'):
            import warnings
            warnings.warn("No SECRET_KEY set for production configuration")

    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    # Stricter session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    LOG_LEVEL = 'INFO'


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True

    # Use separate PostgreSQL database for testing
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'postgresql://postgres:postgres@localhost:5432/quant_web_test'

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    LOG_LEVEL = 'DEBUG'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
