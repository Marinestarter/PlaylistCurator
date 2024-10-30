#newMusicCleaner/spotify_app/services/spotify_service.py
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

CLIENT_ID = 'be72da4625c24b18af5e51e8cc509f07'
CLIENT_SECRET = 'ff22df8effea4e79ae41b3ccc48ab7a8'

client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def transform_track(item: dict) -> dict:
    track = item['track']
    return {
        'name': track['name'],
        'artists': [artist['name'] for artist in track['artists']],
        'album': track['album']['name'],
        'explicit': track['explicit'],
        'id': track['id']
    }


def get_playlist_tracks(playlist_id: str) -> list[dict]:
    response = sp.playlist_items(
        playlist_id,
        fields='items(track(name,artists(name),album(name),explicit,id)),total'
    )
    results = [transform_track(item) for item in response["items"]]

    # subsequently runs until it hits the user-defined limit or has read all songs in the library
    while len(results) < response["total"]:
        response = sp.playlist_items(
            playlist_id,
            fields='items(track(name,artists(name),album(name),explicit,id)),total',
            offset=len(results)
        )
        results.extend(transform_track(item) for item in response["items"])
    return results


def find_clean_ver(tracks: list[dict]) -> list[dict]:
    clean_tracks = []

    #Iterate through each track
    for track in tracks:

        #Checks if the current track is explicit
        if track['explicit']:
            track_name = track['name']
            artist_name = track['artists'][0]
            query = f'track:{track_name} artist:{artist_name}'

            #Search Spotify by track name and primary artist
            results = sp.search(q=query, type='track', limit=10)

            #Iterates through each search result for a viable clean version
            for song in results['tracks']['items']:
                if (not song['explicit'] and
                        track['name'] == song['name'] and
                        track['id'] != song['id'] and
                        track['artists'][0].lower() == song['artists'][0]['name'].lower()):
                    # Creates an new object containing key info about clean alternative
                    clean_song = {
                        'name': song['name'],
                        'artists': [artist['name'] for artist in song['artists']],
                        'album': song['album']['name'],
                        'explicit': song['explicit'],
                        'id': song['id']
                    }
                    #Adds it to the clean version playlist
                    clean_tracks.append(clean_song)
                    break
        #If song is not tagged as explicit, adds it back to the playlist
        else:
            clean_tracks.append(track)

    for stuff in clean_tracks:
        print(stuff, "\n")
    return clean_tracks
