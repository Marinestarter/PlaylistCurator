import logging
from typing import Dict, List

from django.contrib.admin.templatetags.admin_list import results
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class YouTubeService:
    def __init__(self):
        self._youtube = None
        self._user = None

    @property
    def youtube(self):
        if self._youtube is None:
            # Similar to your Spotify OAuth but using Google's flow
            credentials = Credentials(
                token=None,  # You'll get this from OAuth flow
                refresh_token=None,  # You'll get this from OAuth flow
                client_id='YOUR_CLIENT_ID',
                client_secret='YOUR_CLIENT_SECRET',
                token_uri='https://oauth2.googleapis.com/token',
                scopes=['https://www.googleapis.com/auth/youtube.force-ssl']
            )
            self._youtube = build('youtube', 'v3', credentials = credentials)

    def get_user(self) -> Dict:
        if self._user is None:
            try:
                response = self.youtube.channels().list(
                    part = 'snippet,id,topicDetails',
                    mine = True).execute()
                self._user = response['items'][0]
            except Exception as e:
                logger.error(f"Failed to get user: {e}")
                raise
            return self._user

    def get_playlists(self) -> List[Dict]:
        try:
            playlists = []
            request = self.youtube.playlists().list(
                part='snippet',
                mine=True,
                maxResults=50
            )

            while request:
                response = request.execute()
                playlists.extend([{
                    'id': item['id'],
                    'name': item['snippet']['title'],
                    'external_urls': {
                        'youtube': f"https://www.youtube.com/playlist?list={item['id']}"
                    },
                    'tracks': None
                } for item in response.get('items', [])])

                request = self.youtube.playlists().list_next(request, response)

            return playlists

        except Exception as e:
            logger.error(f"Failed to fetch playlists: {e}")
            raise

    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        try:
            tracks = []
            request = self.youtube.playlistItems().list(
                part='snippet',
                playlist_id=playlist_id,
                maxResults = 50
            )






