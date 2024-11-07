# views.py
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from spotipy import oauth2, SpotifyOAuth
import spotipy

SPOTIPY_CLIENT_ID = 'be72da4625c24b18af5e51e8cc509f07'
SPOTIPY_CLIENT_SECRET = 'ff22df8effea4e79ae41b3ccc48ab7a8'
SPOTIPY_REDIRECT_URI = 'http://localhost:8000/spotify/callback/'
SCOPE = 'user-library-read'
CACHE = '.spotipyoauthcache'

sp_oauth = oauth2.SpotifyOAuth(
    SPOTIPY_CLIENT_ID,
    SPOTIPY_CLIENT_SECRET,
    SPOTIPY_REDIRECT_URI,
    scope=SCOPE,
    cache_path=CACHE
)


def spotify_login(request):
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="playlist-modify-public playlist-modify-private playlist-read-private"
    )
    auth_url = sp_oauth.get_authorize_url()
    return HttpResponseRedirect(auth_url)


def spotify_callback(request):
    code = request.GET.get('code')
    if code:
        sp_oauth = SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope="playlist-modify-public playlist-modify-private playlist-read-private"
        )
        token_info = sp_oauth.get_access_token(code)

        if token_info:
            request.session['token_info'] = token_info
            return JsonResponse({'status': 'Authorization successful', 'token_info': token_info})
        else:
            return JsonResponse({'error': 'Failed to get access token'})

    return JsonResponse({'error': 'Authorization failed'})


def index(request):
    access_token = ""
    token_info = sp_oauth.get_cached_token()

    if token_info:
        print("Found cached token!")
        access_token = token_info['access_token']
    else:
        url = request.build_absolute_uri()
        code = sp_oauth.parse_response_code(url)
        if code != url:
            print("Found Spotify auth code in Request URL! Trying to get valid access token...")
            token_info = sp_oauth.get_access_token(code)
            access_token = token_info['access_token']

    if access_token:
        print("Access token available! Trying to get user information...")
        sp = spotipy.Spotify(access_token)
        results = sp.current_user()
        return HttpResponse(str(results))
    else:
        return HttpResponse(htmlForLoginButton())


def htmlForLoginButton():
    auth_url = getSPOauthURI()
    htmlLoginButton = "<a href='" + auth_url + "'>Login to Spotify</a>"
    return htmlLoginButton


def getSPOauthURI():
    auth_url = sp_oauth.get_authorize_url()
    return auth_url


def spotify_interface(request):
    return render(request, 'index.html')
