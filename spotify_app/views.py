# views.py

from django.shortcuts import redirect
from django.http import JsonResponse
from .spotify_auth import SpotifyAuthService
import spotipy

from .spotify_service import SpotifyService


def spotify_login(request):
    auth_service = SpotifyAuthService()
    auth_url = auth_service.get_auth_url()
    return redirect(auth_url)

def spotify_callback(request):
    code = request.GET.get('code')
    if code:
        auth_service = SpotifyAuthService()
        token_info = auth_service.get_token_info(code)
        request.session['token_info'] = token_info
        return redirect('spotify_interface')  # Redirect to your main interface
    else:
        return JsonResponse({'error': 'Authorization failed'})

def get_spotify_client(request):
    auth_service = SpotifyAuthService()
    token_info = request.session.get('token_info')

    if not token_info:
        return None  # User is not authenticated

    if auth_service.is_token_expired(token_info):
        token_info = auth_service.refresh_access_token(token_info['refresh_token'])
        request.session['token_info'] = token_info

    access_token = token_info['access_token']
    return spotipy.Spotify(auth=access_token)
def spotify_interface(request):
    spotify_client = get_spotify_client(request)
    if not spotify_client:
        return redirect('spotify_login')  # Redirect to login if not authenticated

    spotify_service = SpotifyService(spotify_client)
    playlists = spotify_service.get_playlists()
    return render(request, 'index.html', {'playlists': playlists})