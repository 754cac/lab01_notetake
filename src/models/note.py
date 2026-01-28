from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db
import json

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # store tags as JSON text
    tags = db.Column(db.Text, nullable=True, default='[]')
    # optional event dates
    event_start_date = db.Column(db.DateTime, nullable=True)
    event_end_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Note {self.title}>'

    def to_dict(self):
        # parse tags JSON text into a list
        tags_val = []
        if self.tags:
            try:
                tags_val = json.loads(self.tags)
            except Exception:
                # fall back to comma-separated
                tags_val = [t.strip() for t in (self.tags or '').split(',') if t.strip()]

        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'tags': tags_val,
            'event_start_date': self.event_start_date.isoformat() if self.event_start_date else None,
            'event_end_date': self.event_end_date.isoformat() if self.event_end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

