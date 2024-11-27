from spotipy import Spotify

from newMusicCleaner.settings import SP_CLIENT_ID, SP_CLIENT_SECRET
from .models import Token
from django.utils import timezone
from datetime import timedelta
from requests import post

BASE_URL = 'Https://api.spotify.com/v1/me'


def check_tokens(session_id):
    try:
        tokens = Token.objects.filter(user=session_id)
        if tokens:
            return tokens[0]
    except Token.DoesNotExist:
        return None


def create_or_update_tokens(session_id, access_token, refresh_token, expires_in, token_type):
    tokens = check_tokens(session_id)
    expires_in = timezone.now() + timedelta(seconds=expires_in)

    if tokens:
        tokens.access_token = access_token
        tokens.refresh_token = refresh_token
        tokens.expires_in = expires_in
        tokens.token_type = token_type
        tokens.save(update_fields=['access_token', 'refresh_token', 'expires_in', 'token_type'])
    else:
        tokens = Token(
            user=session_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            token_type=token_type
        )
        tokens.save()


def is_spotify_authenticated(session_id):
    tokens = check_tokens(session_id)

    if tokens:
        if tokens.expires_in <= timezone.now():
            refresh_token_func(session_id)
        return True
    return False


def refresh_token_func(session_id):
    refresh_token = check_tokens(session_id).refresh_token

    response = post('https://accounts.spotify.com/api/token', data={
        'grant_type': "refresh_token",
        'refresh_token': refresh_token,
        'client_id': SP_CLIENT_ID,
        'client_secret': SP_CLIENT_SECRET,

    }).json()

    access_token = response.get('access_token')
    expires_in = response.get('expires_in')
    token_type = response.get('token_type')

    create_or_update_tokens(
        session_id=session_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        token_type=token_type
    )


def get_spotify_client(session_id):
    tokens = check_tokens(session_id)
    print(f"Session ID: {session_id}")
    print(f"Tokens found: {tokens is not None}")

    if not tokens:
        print("No tokens found for session")
        return None

    if tokens.expires_in <= timezone.now():
        print("Token expired, attempting refresh")
        refresh_token_func(session_id)
        tokens = check_tokens(session_id)

    print(f"Creating Spotify client with token: {tokens.access_token[:10]}...")
    return Spotify(auth=tokens.access_token)
