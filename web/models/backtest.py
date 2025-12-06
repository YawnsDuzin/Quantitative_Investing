"""
Backtest result models
"""
from datetime import datetime
from web import db
import json


class BacktestResult(db.Model):
    """Backtest execution results"""

    __tablename__ = 'backtest_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    strategy_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Backtest parameters
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    initial_capital = db.Column(db.Float, nullable=False)
    market = db.Column(db.String(20), default='KR')  # KR or US
    rebalance_frequency = db.Column(db.String(20), default='monthly')

    # Parameters stored as JSON
    parameters_json = db.Column(db.Text)

    # Performance metrics
    total_return = db.Column(db.Float)
    annual_return = db.Column(db.Float)
    volatility = db.Column(db.Float)
    sharpe_ratio = db.Column(db.Float)
    sortino_ratio = db.Column(db.Float)
    max_drawdown = db.Column(db.Float)
    calmar_ratio = db.Column(db.Float)
    win_rate = db.Column(db.Float)
    profit_factor = db.Column(db.Float)

    # Portfolio values stored as JSON
    portfolio_values_json = db.Column(db.Text)

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    error_message = db.Column(db.Text)

    # Relationships
    trades = db.relationship('BacktestTrade', backref='backtest', lazy='dynamic',
                            cascade='all, delete-orphan')

    @property
    def parameters(self):
        """Get parameters as dictionary"""
        if self.parameters_json:
            return json.loads(self.parameters_json)
        return {}

    @parameters.setter
    def parameters(self, value):
        """Set parameters from dictionary"""
        self.parameters_json = json.dumps(value)

    @property
    def portfolio_values(self):
        """Get portfolio values as dictionary"""
        if self.portfolio_values_json:
            return json.loads(self.portfolio_values_json)
        return {}

    @portfolio_values.setter
    def portfolio_values(self, value):
        """Set portfolio values from dictionary"""
        # Convert dates to strings if needed
        if isinstance(value, dict):
            converted = {}
            for k, v in value.items():
                if hasattr(k, 'isoformat'):
                    converted[k.isoformat()] = v
                else:
                    converted[str(k)] = v
            self.portfolio_values_json = json.dumps(converted)
        else:
            self.portfolio_values_json = json.dumps(value)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'strategy_name': self.strategy_name,
            'created_at': self.created_at.isoformat(),
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'initial_capital': self.initial_capital,
            'market': self.market,
            'rebalance_frequency': self.rebalance_frequency,
            'parameters': self.parameters,
            'total_return': self.total_return,
            'annual_return': self.annual_return,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'calmar_ratio': self.calmar_ratio,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'status': self.status
        }

    def __repr__(self):
        return f'<BacktestResult {self.name}>'


class BacktestTrade(db.Model):
    """Individual trades from backtest"""

    __tablename__ = 'backtest_trades'

    id = db.Column(db.Integer, primary_key=True)
    backtest_id = db.Column(db.Integer, db.ForeignKey('backtest_results.id'), nullable=False)

    date = db.Column(db.Date, nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    action = db.Column(db.String(10), nullable=False)  # BUY, SELL
    shares = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    value = db.Column(db.Float, nullable=False)
    commission = db.Column(db.Float, default=0)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'date': self.date.isoformat(),
            'symbol': self.symbol,
            'action': self.action,
            'shares': self.shares,
            'price': self.price,
            'value': self.value,
            'commission': self.commission
        }

    def __repr__(self):
        return f'<BacktestTrade {self.symbol} {self.action} {self.shares}>'
