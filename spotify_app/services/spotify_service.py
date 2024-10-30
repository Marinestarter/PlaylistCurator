# newMusicCleaner/spotify_app/services/spotify_service.py
import logging
from typing import List, Dict
from urllib.parse import quote

import spotipy
from django.core.cache import cache
from fuzzywuzzy import fuzz
from spotipy.oauth2 import SpotifyOAuth


class SpotifyConfig:
    client_id: str
    client_secret: str


class SpotifyService:
    def __init__(self):
        self._spotify = None

    @property
    def spotify(self) -> spotipy.Spotify:
        """Lazy initialization of Spotify client"""
        if self._spotify is None:
            self._spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id='be72da4625c24b18af5e51e8cc509f07',
                client_secret='ff22df8effea4e79ae41b3ccc48ab7a8',
                redirect_uri='http://localhost/',
                scope="playlist-modify-public playlist-modify-private playlist-read-private"
            ))
        return self._spotify

    def get_user(self):
        """Get current user information"""
        cache_key = f"spotify_user_{self.spotify.auth_manager.get_cached_token()['access_token']}"
        user = cache.get(cache_key)

        if not user:
            try:
                user = self.spotify.current_user()
                cache.set(cache_key, user, timeout=3600)
            except Exception as e:
                logging.error(f"Failed to get user: {e}")
                raise
        return user

    def get_playlists(self) -> List[Dict]:
        try:
            results = self.spotify.current_user_playlists()
            return results['items']
        except Exception as e:
            logging.error(f"Failed to get playlists: {e}")
            raise

    def get_playlist_tracks(self, playlist_id: str) -> list[dict]:
        """
        Retrieve all tracks from a playlist with pagination support.
        Args:
           playlist_id: Spotify playlist ID
        Returns:
           List of transformed track dictionaries
        """
        cache_key = f"spotify_playlist_tracks_{playlist_id}"
        tracks = cache.get(cache_key)

        if not tracks:
            try:
                tracks = []
                results = self.spotify.playlist_items(playlist_id)

                while results:
                    # Append tracks if they exist in items
                    for item in results.get('items', []):
                        track = item.get('track')
                        if track:
                            tracks.append(track)

                    # Check for pagination, retrieve next page if 'next' exists
                    results = self.spotify.next(results) if results.get('next') else None

                # Cache the result for future access
                cache.set(cache_key, tracks, timeout=300)

            except Exception as e:
                logging.error(f"Failed to get tracks: {e}")
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

    def search_for_track(self, query: str) -> List[Dict]:
        """search for tracks matching query"""
        try:
            results = self.spotify.search(q=query, type='track', limit=50)
            return results['tracks']['items']
        except Exception as e:
            logging.error(f"Failure to search for track: {e}")
            raise

    def convert_playlist(self, playlist_id: str, to_clean: bool = True) -> Dict:
        try:
            original_playlist = self.spotify.playlist(playlist_id)
            tracks = self.get_playlist_tracks(playlist_id)

            clean_track_uris = []
            tracks_to_convert = []

            for track in tracks:
                if to_clean != track['explicit']:
                    clean_track_uris.append(track['uri'])

                else:
                    tracks_to_convert.append({
                        'query': f"{track['name']} {track['artists'][0]['name']}",
                        'name': track['name'],
                        'artists': track['artists'],
                        'uri': track['uri'],
                        'link': track['external_urls']['spotify']
                    })

            converted_track_uris = []
            remaining_songs = []
            potential_matches = {}

            for track in tracks_to_convert:
                query = track['query'].replace('#', '').strip()
                search_results = self.search_for_track(query)

                found_match = False
                for result in search_results:
                    if to_clean != result['explicit'] and self.contain_same_artists(track, result):
                        similarity = fuzz.ratio(result['name'], track['name'])
                        if similarity == 100:
                            found_match = True
                            converted_track_uris.append(result['uri'])
                            break

                        elif similarity > 1:
                            if track['name'] not in potential_matches:
                                potential_matches[track['name']] = []
                            potential_matches[track['name']].append({
                                'name': result['name'],
                                'link': result['external_urls']['spotify'],
                                'uri': result['uri'],
                                'original_track_uri': track['uri'],
                                'original_track_link': track['link']
                            })
                if not found_match:
                    remaining_songs.append({
                        'name': track['name'],
                        'query_url': f"https://open.spotify.com/search/{quote(track['query'])}"
                    })

            user = self.get_user()
            playlist_name = f"{original_playlist['name']} ({'Cleaned' if to_clean else 'explicit'})"
            new_playlist = self.spotify.user_playlist_create(
                user['id'],
                playlist_name,
                public=True
            )

            all_tracks = clean_track_uris + converted_track_uris
            for i in range(0, len(all_tracks), 100):
                batch = all_tracks[i:i + 100]
                if batch:
                    self.spotify.playlist_add_items(new_playlist['id'], batch)
            return {
                'playlist_id': new_playlist['id'],
                'num_original_clean': len(clean_track_uris),
                'num_clean_found': len(converted_track_uris),
                'num_still_missing': remaining_songs,
                'potential_matches': potential_matches
            }

        except Exception as e:
            logging.error(f"Failed to convert playlist: {e}")
            raise
