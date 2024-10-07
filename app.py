import spotipy
from spotify.models import playlist
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, jsonify, render_template
from spotipy import SpotifyOAuth

app = Flask(__name__)

SPOTIPY_CLIENT_ID = 'be72da4625c24b18af5e51e8cc509f07'
SPOTIPY_CLIENT_SECRET = 'ff22df8effea4e79ae41b3ccc48ab7a8'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8000/callback/'
SCOPE = 'playlist-modify-public playlist-modify-private'

from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///songs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=SCOPE))


class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    artists = db.Column(db.String(200), nullable=False)
    album = db.Column(db.String(200), nullable=False)
    explicit = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f'<Song {self.name}>'


with app.app_context():
    db.create_all()


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/test')
def get_playlist_songs():
    playlist_id = '0wE7D85LoyR2KtHACnBZ3q'
    playlist = sp.playlist(playlist_id)
    songs = []

    for item in playlist['tracks']['items']:
        track = item['track']
        existing_song = Song.query.filter_by(spotify_id=track['id']).first()
        if not existing_song:
            song = Song(
                spotify_id=track['id'],
                name=track['name'],
                artists=', '.join([artist['name'] for artist in track['artists']]),
                album=track['album']['name'],
                explicit=track['explicit'])
            db.session.add(song)
            db.session.commit()
            print("added " + song.name)

        else:
            song = existing_song

        songs.append({
            'id': song.spotify_id,
            'name': song.name,
            'artists': song.artists,
            'album': song.album,
            'explicit': song.explicit
        })
    return render_template('songs.html', songs=songs)


if __name__ == '__main__':
    app.run(debug=True)
