from datetime import timedelta
from django.utils import timezone
from requests import post

from newMusicCleaner.settings import YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_SCOPES
from .models import Youtube_token
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def check_tokens(session_id):
    try:
        tokens = Youtube_token.objects.filter(user=session_id)
        if tokens:
            return tokens[0]
    except Youtube_token.DoesNotExist:
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
        tokens = Youtube_token(
            user=session_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            token_type=token_type
        )
        tokens.save()


def is_youtube_authenticated(session_id):
    tokens = check_tokens(session_id)
    if tokens:
        if tokens.expires_in <= timezone.now():
            refresh_token_func(session_id)
        return True
    return False


def refresh_token_func(session_id):
    tokens = check_tokens(session_id)
    if not tokens:
        return None

    response = post('https://oauth2.googleapis.com/token', data={
        'client_id': YOUTUBE_CLIENT_ID,
        'client_secret': YOUTUBE_CLIENT_SECRET,
        'refresh_token': tokens.refresh_token,
        'grant_type': 'refresh_token'
    }).json()

    access_token = response.get('access_token')
    expires_in = response.get('expires_in')
    token_type = response.get('token_type')

    create_or_update_tokens(
        session_id=session_id,
        access_token=access_token,
        refresh_token=tokens.refresh_token,
        expires_in=expires_in,
        token_type=token_type
    )


def get_youtube_client(session_id):
    tokens = check_tokens(session_id)
    if not tokens:
        return None

    if tokens.expires_in <= timezone.now():
        refresh_token_func(session_id)
        tokens = check_tokens(session_id)

    credentials = Credentials(
        token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=YOUTUBE_SCOPES
    )

    return build('youtube', 'v3', credentials=credentials)
