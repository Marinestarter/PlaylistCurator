import logging
from typing import Dict, List
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from fuzzywuzzy import fuzz
from ytmusicapi import YTMusic

from youtube_app.extras import get_youtube_client

logger = logging.getLogger(__name__)


class YouTubeMusicService:
    def __init__(self, session_id=None):
        self._youtube = None
        self._ytmusic = None
        self._user = None
        self.session_id = session_id
        self.max_workers = 10

    def initialize_clients(self):
        if not self._youtube:
            self._youtube = get_youtube_client(self.session_id)
            if not self._youtube:
                raise Exception("Failed to initialize YouTube client")

        if not self._ytmusic:
            self._ytmusic = YTMusic()

        return self._youtube, self._ytmusic

    def get_user(self) -> Dict:
        """Get current user channel information"""
        if self._user is None:
            try:
                self.initialize_clients()
                response = self._youtube.channels().list(
                    part='snippet',
                    mine=True
                ).execute()

                if response['items']:
                    channel = response['items'][0]
                    custom_url = channel.get("snippet", {}).get("customUrl")
                    self._user = {
                        'id': channel['id'],
                        'name': channel['snippet']['title'],
                        'external_urls': f"https://music.youtube.com/{custom_url}"
                    }
            except Exception as e:
                logger.error(f"Failed to get user: {e}")
                raise
        return self._user

    def get_playlists(self) -> List[Dict]:
        try:
            self.initialize_clients()
            playlists = []
            request = self._youtube.playlists().list(
                part='snippet',
                mine=True,
                maxResults=50
            )

            while request:
                response = request.execute()

                for playlist in response['items']:
                    playlist_id = playlist['id']
                    playlist_data = {
                        'id': playlist_id,
                        'name': playlist['snippet']['title'],
                        'tracks': None,
                        'external_urls': {
                            'youtube': f"https://music.youtube.com/playlist?list={playlist_id}"
                        }
                    }

                    playlists.append(playlist_data)

                request = self._youtube.playlists().list_next(request, response)

            return playlists
        except Exception as e:
            logger.error(f"Failed to fetch playlists: {e}")
            raise

    def get_song_metadata(self, video_id: str, title: str, channel: str) -> Dict:
        try:
            _, ytmusic = self.initialize_clients()

            # Search using title and channel name
            search_query = f"{title} {channel}"
            search_results = ytmusic.search(search_query, filter='songs', limit=4)

            # Look for a result matching our video ID
            matching_result = next(
                (result for result in search_results if result.get('videoId') == video_id),
                None
            )

            # returns needed metadata if a matching song is found
            if matching_result:
                return {
                    'id': video_id,
                    'title': matching_result.get('title'),
                    'artists': [artist['name'] for artist in matching_result.get('artists', [])],
                    'explicit': matching_result.get('isExplicit', False),
                    'url': f"https://www.music.youtube.com/watch?v={video_id}"
                }
        except Exception as e:
            logger.error(f"Failed to get song metadata: {e}")
            raise

    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """Get tracks from a playlist with detailed music metadata using parallel processing"""
        try:
            youtube, _ = self.initialize_clients()
            tracks = []

            # Request with videoOwnerChannelTitle in snippet
            request = youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                fields='items(snippet(title,videoOwnerChannelTitle),contentDetails(videoId)),nextPageToken'
            )

            while request:
                response = request.execute()

                # Process videos in parallel
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Create a list of futures for metadata retrieval
                    future_to_item = {
                        executor.submit(
                            self.get_song_metadata,
                            item['contentDetails']['videoId'],
                            item['snippet']['title'],
                            item['snippet'].get('videoOwnerChannelTitle', '')
                        ): item
                        for item in response.get('items', [])
                    }

                    # Process completed futures
                    for future in concurrent.futures.as_completed(future_to_item):
                        item = future_to_item[future]
                        try:
                            track_data = future.result()
                            if track_data:
                                tracks.append(track_data)
                            else:
                                # Fallback to basic metadata if no match found
                                basic_track = {
                                    'id': item['contentDetails']['videoId'],
                                    'title': item['snippet']['title'],
                                    'artists': [item['snippet'].get('videoOwnerChannelTitle', 'Unknown Artist')],
                                    'explicit': False,
                                    'url': f"https://www.youtube.com/watch?v={item['contentDetails']['videoId']}"
                                }
                                tracks.append(basic_track)
                        except Exception as e:
                            logger.error(f"Error processing track {item['snippet']['title']}: {e}")

                request = youtube.playlistItems().list_next(request, response)

            return tracks

        except Exception as e:
            logger.error(f"Failed to get tracks: {e}")
            raise

    def search_track(self, query: str) -> List[Dict]:
        """Search for tracks on YTMusic"""
        try:
            _, ytmusic = self.initialize_clients()
            search_results = ytmusic.search(query, filter="songs", limit=20)

            tracks = []
            for result in search_results:
                if result['resultType'] == 'song':
                    track_data = {
                        'id': result['videoId'],
                        'title': result['title'],
                        'artists': [artist['name'] for artist in result.get('artists', [])],
                        'explicit': result.get('explicit', False),
                        'url': f"https://www.youtube.com/watch?v={result['videoId']}"
                    }
                    tracks.append(track_data)

            return tracks
        except Exception as e:
            logger.error(f"Failed to search tracks: {e}")
            return []

    def create_playlist(self, title: str, description: str = "", privacy_status: str = "private") -> Dict:
        """Create a new playlist"""
        try:
            youtube, _ = self.initialize_clients()
            response = youtube.playlists().insert(
                part='snippet,status',
                body={
                    'snippet': {
                        'title': title,
                        'description': description
                    },
                    'status': {
                        'privacyStatus': privacy_status
                    }
                }
            ).execute()

            return {
                'id': response['id'],
                'name': response['snippet']['title'],
                'description': response['snippet']['description']
            }
        except Exception as e:
            logger.error(f"Failed to create playlist: {e}")
            raise

    def add_track_to_playlist(self, playlist_id: str, video_id: str) -> bool:
        """Add a track to a playlist"""
        try:
            youtube, _ = self.initialize_clients()
            youtube.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': playlist_id,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': video_id
                        }
                    }
                }
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to add track to playlist: {e}")
            return False

    def find_clean_version(self, track: Dict) -> Dict:
        """Find clean version of a track using basic fuzzy matching"""
        try:
            _, ytmusic = self.initialize_clients()

            # Create search query using title and first artist
            query = f"{track['title']} {track['artists'][0]}"
            search_results = ytmusic.search(query, filter="songs", limit=10)

            best_match = None
            best_ratio = 0

            for result in search_results:
                if result['resultType'] == 'song' and not result.get('isExplicit', False):
                    # Compare titles using fuzzy matching
                    ratio = fuzz.ratio(
                        track['title'].lower().strip(),
                        result['title'].lower().strip()
                    )

                    # If we find a very good match (over 85%), use it
                    if ratio > 85 and ratio > best_ratio:
                        best_ratio = ratio
                        best_match = {
                            'id': result['videoId'],
                            'title': result['title'],
                            'artists': [artist['name'] for artist in result.get('artists', [])],
                            'explicit': result.get('isExplicit', False),
                            'url': f"https://www.youtube.com/watch?v={result['videoId']}"
                        }

            return best_match
        except Exception as e:
            logger.error(f"Failed to find clean version: {e}")
            return []

    def convert_playlist(self, playlist_id: str, to_clean: bool = True) -> Dict:
        """Convert a playlist to clean/explicit versions"""
        try:
            # Get all tracks from the playlist with metadata
            tracks = self.get_playlist_tracks(playlist_id)

            # Create new playlist
            original_playlist = self._youtube.playlists().list(
                part='snippet',
                id=playlist_id
            ).execute()['items'][0]

            new_playlist = self.create_playlist(
                title=f"{original_playlist['snippet']['title']} ({'Clean' if to_clean else 'Explicit'})",
                description=f"Converted from: {original_playlist['snippet']['title']}"
            )

            clean_tracks = []
            converted_tracks = []
            remaining_tracks = []
            potential_matches = {}

            for track in tracks:
                if track.get('explicit', False):
                    clean_tracks.append(track)
                    self.add_track_to_playlist(new_playlist['id'], track['id'])
                else:
                    # Find alternative version
                    alternative = self.find_clean_version(track)
                    converted_tracks.append(alternative)
                    self.add_track_to_playlist(new_playlist['id'], alternative['id'])
                    potential_matches[track['title']] = [alternative]
                    # Format the remaining track according to schema
                    remaining_track = {
                        'name': track['title'],
                        'artists': ', '.join(track['artists']),  # Join artists into a single string
                        'query_url': track['url']
                    }
                    remaining_tracks.append(remaining_track)

            return {
                'playlist_id': new_playlist['id'],
                'num_original_clean': len(clean_tracks),
                'num_converted': len(converted_tracks),
                'num_still_missing': len(remaining_tracks),
                'still_missing': remaining_tracks,
                'potential_matches': potential_matches,
            }

        except Exception as e:
            logger.error(f"Failed to convert playlist: {e}")
            raise
