# spotify_auth.py

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

class SpotifyAuthService:
    def __init__(self, scope: str = None, cache_path: str = None):
        self.scope = scope or "user-library-read playlist-modify-public playlist-modify-private"
        self.cache_path = cache_path or '.cache'

        self.sp_oauth = SpotifyOAuth(
            client_id='be72da4625c24b18af5e51e8cc509f07',
            client_secret='ff22df8effea4e79ae41b3ccc48ab7a8',
            redirect_uri='http://localhost:8000/spotify/callback/',
            scope=self.scope,
            cache_path=self.cache_path
        )

    def get_auth_url(self) -> str:
        return self.sp_oauth.get_authorize_url()

    def get_token_info(self, code: str) -> dict:
        return self.sp_oauth.get_access_token(code)

    def get_cached_token(self) -> dict:
        return self.sp_oauth.get_cached_token()

    def is_token_expired(self, token_info: dict) -> bool:
        return self.sp_oauth.is_token_expired(token_info)

    def refresh_access_token(self, refresh_token: str) -> dict:
        return self.sp_oauth.refresh_access_token(refresh_token)
