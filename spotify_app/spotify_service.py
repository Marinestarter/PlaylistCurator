import logging
from typing import Dict, List
from urllib.parse import quote
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

import spotipy
from fuzzywuzzy import fuzz
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)


class SpotifyService:
    def __init__(self):
        self._spotify = None
        self._user = None
        self.max_workers = 10

    @property
    def spotify(self) -> spotipy.Spotify:
        if self._spotify is None:
            self._spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id='be72da4625c24b18af5e51e8cc509f07',
                client_secret='ff22df8effea4e79ae41b3ccc48ab7a8',
                redirect_uri='http://localhost:8000/spotify/callback/',
                scope="playlist-modify-public playlist-modify-private playlist-read-private"
            ))
        return self._spotify

    def get_user(self) -> Dict:
        """Get current user information"""
        if self._user is None:
            try:
                self._user = self.spotify.current_user()
            except Exception as e:
                print(f"Failed to get user: {e}")
                raise
        return self._user

    def get_playlists(self) -> List[Dict]:
        try:
            results = self.spotify.current_user_playlists()
            playlists = []

            # Process each playlist in the results
            for playlist in results['items']:  # Access 'items' from results
                playlist_data = {
                    'id': playlist['id'],
                    'name': playlist['name'],
                    'external_urls': playlist['external_urls'],
                    'tracks': None  # Matches the Optional[List[TrackResponse]] in schema
                }
                playlists.append(playlist_data)

            return playlists
        except Exception as e:
            logger.error(f"Failed to fetch playlists: {e}")
            raise

    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        try:
            tracks = []
            results = self.spotify.playlist_items(playlist_id)

            while results:
                # Appends tracks if they exist in items
                for item in results.get('items', []):
                    track = item.get('track')
                    if track:
                        tracks.append(track)

                results = self.spotify.next(results) if results.get('next') else None

        except Exception as e:
            print(f"Failed to get tracks: {e}")
            raise
        return tracks

    def contain_same_artists(self, first: Dict, second: Dict) -> bool:
        """Check if two tracks have the same artists"""
        if len(first['artists']) != len(second['artists']):
            return False

        for i in range(len(first['artists'])):
            if first['artists'][i]['name'] != second['artists'][i]['name']:
                return False
        return True

    def search_and_process_track(self, track: Dict) -> Dict:
        """Search for a single track and process results"""
        query = track['query'].replace('#', '').strip()

        try:
            search_results = self.spotify.search(q=query, type='track', limit=50)['tracks']['items']
        except Exception as e:
            logger.error(f"Failed to search track {query}: {e}")
            return {
                'track': track,
                'found_match': False,
                'converted_uri': None,
                'potential_matches': [],
            }

        found_match = False
        converted_uri = None
        potential_matches = []

        for result in search_results:
            if not result['explicit'] and self.contain_same_artists(track, result):
                similarity = fuzz.ratio(result['name'], track['name'])
                if similarity == 100:
                    found_match = True
                    converted_uri = result['uri']
                    break
                elif similarity > 1:
                    potential_matches.append({
                        'name': result['name'],
                        'artists': result['artists'][0]['name'],
                        'link': result['external_urls']['spotify'],
                        'uri': result['uri'],
                        'original_track_uri': track['uri'],
                        'original_track_link': track['link']
                    })

        return {
            'track': track,
            'found_match': found_match,
            'converted_uri': converted_uri,
            'potential_matches': potential_matches,
        }

    def convert_playlist(self, playlist_id: str, to_clean: bool = True) -> Dict:
        try:
            # Get original playlist
            original_playlist = self.spotify.playlist(playlist_id)

            # Get tracks
            tracks = self.get_playlist_tracks(playlist_id)

            # Process and categorize tracks
            clean_tracks_uris = []
            tracks_to_convert = []

            #iterates each track, adding explicit to tracks_to_convert list
            for track in tracks:
                if not track['explicit']:
                    clean_tracks_uris.append(track['uri'])
                else:
                    tracks_to_convert.append({
                        'query': f"{track['name']} {track['artists'][0]['name']}",
                        'name': track['name'],
                        'artists': track['artists'],
                        'uri': track['uri'],
                        'link': track['external_urls']['spotify']
                    })

            # Parallel search and match
            converted_tracks_uris = []
            remaining_songs = []
            potential_matches = {}

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all searches to the thread pool
                future_to_track = {
                    executor.submit(self.search_and_process_track, track): track
                    for track in tracks_to_convert
                }

                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_track):
                    result = future.result()

                    if result['found_match']:
                        converted_tracks_uris.append(result['converted_uri'])
                    else:
                        track = result['track']
                        if result['potential_matches']:
                            potential_matches[track['name']] = result['potential_matches']
                        else:
                            remaining_songs.append({
                                'name': track['name'],
                                'artists': track['artists'][0]['name'],
                                'query_url': f"https://open.spotify.com/search/{quote(track['query'])}"
                            })

            user = self.get_user()
            playlist_name = f"{original_playlist['name']} ({'Cleaned' if to_clean else 'explicit'})"
            new_playlist = self.spotify.user_playlist_create(
                user['id'],
                playlist_name,
                public=True
            )

            all_tracks = clean_tracks_uris + converted_tracks_uris
            for i in range(0, len(all_tracks), 100):
                batch = all_tracks[i:i + 100]
                if batch:
                    self.spotify.playlist_add_items(new_playlist['id'], batch)

            return {
                'playlist_id': new_playlist['id'],
                'num_original_clean': len(clean_tracks_uris),
                'num_clean_found': len(converted_tracks_uris),
                'num_still_missing': len(remaining_songs),
                'still_missing': remaining_songs,
                'potential_matches': potential_matches,
            }

        except Exception as e:
            logging.error(f"Failed to convert playlist: {e}")
            raise
    def add_additional_songs(self, playlist_id: str, song_uris: List) -> str:
        try:
            if song_uris:
                self.spotify.playlist_add_items(playlist_id, song_uris)
                return "successfully added!"
        except Exception as e:
            logging.error(f"Failed to add songs: {e}")
