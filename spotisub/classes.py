"""Spotisub classes"""

from spotisub import configuration_db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class ComparisonHelper:
    def __init__(self, track, artist_spotify, found,
                 excluded, song_ids, track_helper):
        self.track = track
        self.artist_spotify = artist_spotify
        self.found = found
        self.excluded = excluded
        self.song_ids = song_ids
        self.track_helper = track_helper

@login.user_loader
def load_user(id):
    """Load user by their ID"""
    return User.query.get(int(id))

class User(configuration_db.Model, UserMixin):
    """User table"""
    id = configuration_db.Column(configuration_db.Integer, primary_key=True)
    username = configuration_db.Column(configuration_db.String(32), unique=True, index=True)
    password_hash = configuration_db.Column(configuration_db.String(128))

    def __repr__(self):
        return f'User: {self.username}'

    def set_password(self, password):
        """Hash user password befor storage"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Confirms a user's password"""
        return check_password_hash(self.password_hash, password)