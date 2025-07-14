from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pickle

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    points = db.Column(db.Integer, default=0)
    recent_activity = db.Column(db.PickleType, default=list)

    last_challenge_date = db.Column(db.String(50), nullable=True)  # stores YYYY-MM-DD
    last_challenge_result = db.Column(db.String(20), nullable=True)  # "success", "fail"

    story_progress = db.Column(db.PickleType, default=dict)

    def add_activity(self, activity):
        """Append a new activity (max 3 recent kept)"""
        if self.recent_activity is None:
            self.recent_activity = []
        self.recent_activity.insert(0, activity)
        self.recent_activity = self.recent_activity[:3]
