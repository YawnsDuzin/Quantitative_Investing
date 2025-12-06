"""
Flask routes for Quantitative Investing Web Application
"""

from web.routes.main import main_bp
from web.routes.auth import auth_bp
from web.routes.dashboard import dashboard_bp
from web.routes.strategies import strategies_bp
from web.routes.backtest import backtest_bp
from web.routes.data import data_bp
from web.routes.settings import settings_bp
from web.routes.api import api_bp

__all__ = [
    'main_bp',
    'auth_bp',
    'dashboard_bp',
    'strategies_bp',
    'backtest_bp',
    'data_bp',
    'settings_bp',
    'api_bp'
]
