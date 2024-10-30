# views.py
from django.http import HttpResponse
from spotipy import oauth2
import spotipy

SPOTIPY_CLIENT_ID = 'be72da4625c24b18af5e51e8cc509f07'
SPOTIPY_CLIENT_SECRET = 'ff22df8effea4e79ae41b3ccc48ab7a8'
SPOTIPY_REDIRECT_URI = 'http://localhost:8000'  # Changed from 8080 to Django's default
SCOPE = 'user-library-read'
CACHE = '.spotipyoauthcache'

sp_oauth = oauth2.SpotifyOAuth(
    SPOTIPY_CLIENT_ID,
    SPOTIPY_CLIENT_SECRET,
    SPOTIPY_REDIRECT_URI,
    scope=SCOPE,
    cache_path=CACHE
)


def index(request):
    access_token = ""
    token_info = sp_oauth.get_cached_token()

    if token_info:
        print("Found cached token!")
        access_token = token_info['access_token']
    else:
        url = request.build_absolute_uri()  # This is the only major change - using Django's URL builder
        code = sp_oauth.parse_response_code(url)
        if code != url:
            print("Found Spotify auth code in Request URL! Trying to get valid access token...")
            token_info = sp_oauth.get_access_token(code)
            access_token = token_info['access_token']

    if access_token:
        print("Access token available! Trying to get user information...")
        sp = spotipy.Spotify(access_token)
        results = sp.current_user()
        return HttpResponse(str(results))  # Changed to HttpResponse
    else:
        return HttpResponse(htmlForLoginButton())  # Changed to HttpResponse


def htmlForLoginButton():
    auth_url = getSPOauthURI()
    htmlLoginButton = "<a href='" + auth_url + "'>Login to Spotify</a>"
    return htmlLoginButton


def getSPOauthURI():
    auth_url = sp_oauth.get_authorize_url()
    return auth_url