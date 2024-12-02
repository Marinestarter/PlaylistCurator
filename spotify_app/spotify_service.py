import logging
from typing import Dict, List
from urllib.parse import quote
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

import spotipy
from fuzzywuzzy import fuzz
from spotipy.oauth2 import SpotifyOAuth

from spotify_app.extras import get_spotify_client

logger = logging.getLogger(__name__)


class SpotifyService:
    def __init__(self, session_id=None):
        self._spotify = None
        self._user = None
        self.session_id = session_id
        self.max_workers = 10

    def initialize_client(self):
        if not self._spotify:
            self._spotify = get_spotify_client(self.session_id)
            if not self._spotify:
                raise Exception("Failed to initialize Spotify client")
        return self._spotify

    def get_user(self) -> Dict:
        """Get current user information"""
        if self._user is None:
            try:
                # Initialize the client if not already done
                self.initialize_client()
                self._user = self._spotify.current_user()
            except Exception as e:
                print(f"Failed to get user: {e}")
                raise
        return self._user

    def get_playlists(self) -> List[Dict]:
        try:
            self.initialize_client()
            results = self._spotify.current_user_playlists()

            if not results:
                logger.error("No results returned from Spotify API")
                return []

            if 'items' not in results:
                logger.error(f"Unexpected API response format: {results}")
                return []

            playlists = []

            for playlist in results['items']:
                if not playlist:
                    logger.warning("Encountered None playlist in results")
                    continue

                try:
                    playlist_data = {
                        'id': playlist['id'],
                        'name': playlist['name'],
                        'external_urls': playlist['external_urls'],
                        'tracks': None
                    }
                    playlists.append(playlist_data)
                except KeyError as ke:
                    logger.error(f"Missing key in playlist data: {ke}")
                    logger.debug(f"Playlist object: {playlist}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing playlist: {e}")
                    continue

            return playlists

        except Exception as e:
            logger.error(f"Failed to fetch playlists: {e}", exc_info=True)
            raise

    def contain_same_artists(self, first: Dict, second: Dict) -> bool:
        """Check if two tracks have the same artists"""
        if len(first['artists']) != len(second['artists']):
            return False

        for i in range(len(first['artists'])):
            if first['artists'][i]['name'] != second['artists'][i]['name']:
                return False
        return True

    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        try:
            tracks = []
            self.initialize_client()
            results = self._spotify.playlist_items(playlist_id)

            while results:
                # Appends tracks if they exist in items
                for item in results.get('items', []):
                    track = item.get('track')
                    if track:
                        tracks.append(track)

                results = self._spotify.next(results) if results.get('next') else None

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
            self.initialize_client()
            search_results = self._spotify.search(q=query, type='track', limit=50)['tracks']['items']
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
            self.initialize_client()
            # Get original playlist
            original_playlist = self._spotify.playlist(playlist_id)

            # Get tracks
            tracks = self.get_playlist_tracks(playlist_id)

            # Process and categorize tracks
            clean_tracks_uris = []
            tracks_to_convert = []

            # iterates each track, adding explicit to tracks_to_convert list
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
            new_playlist = self._spotify.user_playlist_create(
                user['id'],
                playlist_name,
                public=True
            )

            all_tracks = clean_tracks_uris + converted_tracks_uris
            for i in range(0, len(all_tracks), 100):
                batch = all_tracks[i:i + 100]
                if batch:
                    self._spotify.playlist_add_items(new_playlist['id'], batch)

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

    def add_additional_songs(self, playlist_id: str, song_uris: List) -> str:
        try:
            if song_uris:
                self.initialize_client()
                self._spotify.playlist_add_items(playlist_id, song_uris)
                return "successfully added!"
        except Exception as e:
            logging.error(f"Failed to add songs: {e}")


