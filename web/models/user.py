"""
User model for authentication
"""
from datetime import datetime
from flask_login import UserMixin
from web import db, bcrypt, login_manager


class User(UserMixin, db.Model):
    """User model for authentication and profile management"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)

    # User preferences
    theme = db.Column(db.String(10), default='light')  # 'light' or 'dark'
    language = db.Column(db.String(10), default='ko')  # 'ko' or 'en'
    default_market = db.Column(db.String(10), default='KR')  # 'KR' or 'US'

    # Relationships
    backtests = db.relationship('BacktestResult', backref='user', lazy='dynamic')
    portfolios = db.relationship('Portfolio', backref='user', lazy='dynamic')
    strategies = db.relationship('SavedStrategy', backref='user', lazy='dynamic')

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check if provided password matches hash"""
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_admin': self.is_admin,
            'theme': self.theme,
            'language': self.language,
            'default_market': self.default_market
        }

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))
