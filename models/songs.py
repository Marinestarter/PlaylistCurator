from flask_sqlalchemy import SQLAlchemy


class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    artists = db.Column(db.String(200), nullable=False)
    album = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Song {self.name}>'
