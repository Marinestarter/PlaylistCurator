import spotipy
from spotify.models import playlist
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, jsonify, render_template, request, redirect, url_for
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


@app.route('/', methods=['GET','POST'])
def playlist_input():
    if request.method == 'POST':
        playlist_link = request.form['playlist_link']
        playlist_id = playlist_link.split('/')[-1].split('?')[0]
        return redirect(url_for('get_playlist_songs', playlist_id=playlist_id))
    return render_template('search.html')


@app.route('/playlist/<playlist_id>')
def get_playlist_songs(playlist_id):
    playlist = sp.playlist(playlist_id)
    playlist_songs = []

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

        playlist_songs.append({
            'id': song.spotify_id,
            'name': song.name,
            'artists': song.artists,
            'album': song.album,
            'explicit': song.explicit
        })
    return render_template('songs.html', songs=playlist_songs)

@app.route('/view_db')
def view_db():
    songs = Song.query.all()
    output = ""
    for song in songs:
        output += f"ID: {song.id}, Name:    {song.name}, Artists: {song.artists}, Album: {song.album}, Explicit: {song.explicit}\n"
    return f"<pre>{output}</pre>"


if __name__ == '__main__':
    app.run(debug=True)
