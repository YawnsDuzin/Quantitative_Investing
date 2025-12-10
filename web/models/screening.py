"""
Screening models - Database models for stock screening results
"""
from datetime import datetime
from web import db


class ScreeningResult(db.Model):
    """Model for storing screening results"""
    __tablename__ = 'screening_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Screening info
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    market = db.Column(db.String(10), default='KR')  # KR or US
    screening_type = db.Column(db.String(20), default='preset')  # preset or custom
    preset_name = db.Column(db.String(50))  # If using preset

    # Conditions (JSON format for custom screening)
    conditions_json = db.Column(db.Text)
    parameters_json = db.Column(db.Text)

    # Results
    total_stocks = db.Column(db.Integer, default=0)
    filtered_count = db.Column(db.Integer, default=0)
    results_json = db.Column(db.Text)  # JSON array of stock results

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    progress = db.Column(db.Integer, default=0)
    current_step = db.Column(db.String(100))
    error_message = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', backref=db.backref('screening_results', lazy='dynamic'))

    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'market': self.market,
            'screening_type': self.screening_type,
            'preset_name': self.preset_name,
            'total_stocks': self.total_stocks,
            'filtered_count': self.filtered_count,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'results': json.loads(self.results_json) if self.results_json else [],
            'conditions': json.loads(self.conditions_json) if self.conditions_json else [],
            'parameters': json.loads(self.parameters_json) if self.parameters_json else {}
        }

    def __repr__(self):
        return f'<ScreeningResult {self.id}: {self.name}>'


class SavedScreener(db.Model):
    """Model for saved screening configurations"""
    __tablename__ = 'saved_screeners'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    market = db.Column(db.String(10), default='KR')
    screening_type = db.Column(db.String(20), default='custom')
    preset_name = db.Column(db.String(50))

    # Configuration
    conditions_json = db.Column(db.Text)
    parameters_json = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('saved_screeners', lazy='dynamic'))

    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'market': self.market,
            'screening_type': self.screening_type,
            'preset_name': self.preset_name,
            'conditions': json.loads(self.conditions_json) if self.conditions_json else [],
            'parameters': json.loads(self.parameters_json) if self.parameters_json else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<SavedScreener {self.id}: {self.name}>'
