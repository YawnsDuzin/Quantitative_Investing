"""
Portfolio models
"""
from datetime import datetime
from web import db
import json


class Portfolio(db.Model):
    """User portfolio"""

    __tablename__ = 'portfolios'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Portfolio settings
    initial_capital = db.Column(db.Float, default=100000000)
    market = db.Column(db.String(20), default='KR')
    strategy_name = db.Column(db.String(50))
    rebalance_frequency = db.Column(db.String(20), default='monthly')

    # Current value
    current_value = db.Column(db.Float)
    last_rebalanced = db.Column(db.DateTime)

    # Strategy parameters as JSON
    strategy_params_json = db.Column(db.Text)

    # Relationships
    holdings = db.relationship('PortfolioHolding', backref='portfolio', lazy='dynamic',
                              cascade='all, delete-orphan')

    @property
    def strategy_params(self):
        """Get strategy parameters as dictionary"""
        if self.strategy_params_json:
            return json.loads(self.strategy_params_json)
        return {}

    @strategy_params.setter
    def strategy_params(self, value):
        """Set strategy parameters from dictionary"""
        self.strategy_params_json = json.dumps(value)

    def get_total_value(self):
        """Calculate total portfolio value"""
        total = 0
        for holding in self.holdings:
            if holding.current_price:
                total += holding.quantity * holding.current_price
            else:
                total += holding.quantity * holding.avg_price
        return total

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'initial_capital': self.initial_capital,
            'market': self.market,
            'strategy_name': self.strategy_name,
            'rebalance_frequency': self.rebalance_frequency,
            'current_value': self.current_value or self.get_total_value(),
            'last_rebalanced': self.last_rebalanced.isoformat() if self.last_rebalanced else None,
            'strategy_params': self.strategy_params
        }

    def __repr__(self):
        return f'<Portfolio {self.name}>'


class PortfolioHolding(db.Model):
    """Individual holdings in a portfolio"""

    __tablename__ = 'portfolio_holdings'

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)

    symbol = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100))
    quantity = db.Column(db.Float, nullable=False)
    avg_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float)
    target_weight = db.Column(db.Float)  # Target portfolio weight
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def market_value(self):
        """Calculate market value"""
        price = self.current_price or self.avg_price
        return self.quantity * price

    @property
    def profit_loss(self):
        """Calculate unrealized profit/loss"""
        if self.current_price:
            return (self.current_price - self.avg_price) * self.quantity
        return 0

    @property
    def profit_loss_pct(self):
        """Calculate profit/loss percentage"""
        if self.current_price and self.avg_price > 0:
            return ((self.current_price - self.avg_price) / self.avg_price) * 100
        return 0

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'quantity': self.quantity,
            'avg_price': self.avg_price,
            'current_price': self.current_price,
            'target_weight': self.target_weight,
            'market_value': self.market_value,
            'profit_loss': self.profit_loss,
            'profit_loss_pct': self.profit_loss_pct
        }

    def __repr__(self):
        return f'<PortfolioHolding {self.symbol} {self.quantity}>'
