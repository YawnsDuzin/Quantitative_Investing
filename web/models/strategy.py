"""
Saved strategy models
"""
from datetime import datetime
from web import db
import json


class SavedStrategy(db.Model):
    """User saved custom strategy configurations"""

    __tablename__ = 'saved_strategies'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Strategy type
    strategy_type = db.Column(db.String(50), nullable=False)  # momentum, value, quality, multifactor, custom

    # Market settings
    market = db.Column(db.String(20), default='KR')  # KR, US, BOTH

    # Configuration stored as JSON
    config_json = db.Column(db.Text, nullable=False)

    # Performance metrics from last backtest
    last_backtest_id = db.Column(db.Integer, db.ForeignKey('backtest_results.id'))
    last_sharpe_ratio = db.Column(db.Float)
    last_annual_return = db.Column(db.Float)
    last_max_drawdown = db.Column(db.Float)

    # Is this a template/public strategy?
    is_template = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False)

    @property
    def config(self):
        """Get configuration as dictionary"""
        if self.config_json:
            return json.loads(self.config_json)
        return {}

    @config.setter
    def config(self, value):
        """Set configuration from dictionary"""
        self.config_json = json.dumps(value)

    def get_factor_weights(self):
        """Get factor weights from config"""
        config = self.config
        return config.get('factor_weights', {})

    def get_risk_settings(self):
        """Get risk management settings from config"""
        config = self.config
        return {
            'stop_loss': config.get('stop_loss', 0.15),
            'max_position_size': config.get('max_position_size', 0.1),
            'max_positions': config.get('max_positions', 20),
            'min_positions': config.get('min_positions', 10)
        }

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'strategy_type': self.strategy_type,
            'market': self.market,
            'config': self.config,
            'last_sharpe_ratio': self.last_sharpe_ratio,
            'last_annual_return': self.last_annual_return,
            'last_max_drawdown': self.last_max_drawdown,
            'is_template': self.is_template,
            'is_public': self.is_public
        }

    def __repr__(self):
        return f'<SavedStrategy {self.name}>'
