"""
WTForms forms for Quantitative Investing Web Application
"""

from web.forms.auth import LoginForm, RegistrationForm, ProfileForm, ChangePasswordForm
from web.forms.backtest import BacktestForm
from web.forms.strategy import StrategyForm
from web.forms.portfolio import PortfolioForm

__all__ = [
    'LoginForm',
    'RegistrationForm',
    'ProfileForm',
    'ChangePasswordForm',
    'BacktestForm',
    'StrategyForm',
    'PortfolioForm'
]
