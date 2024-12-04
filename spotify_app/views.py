from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from requests import Request, post
from rest_framework.views import APIView

from newMusicCleaner.settings import SP_REDIRECT_URI, SP_CLIENT_ID, SP_CLIENT_SECRET
from .extras import create_or_update_tokens, is_spotify_authenticated
from .spotify_service import SpotifyService


def spotify_interface(request):
    """Main interface view that displays the Spotify converter interface"""
    if not request.session.session_key:
        request.session.create()

    if not is_spotify_authenticated(request.session.session_key):
        return redirect('spotify-auth')

    spotify_service = SpotifyService(request.session.session_key)

    try:
        # Get user info and playlists
        user_info = spotify_service.get_user()
        playlists = spotify_service.get_playlists()

        # Limit playlists to 60 as per original implementation
        limited_playlists = playlists[:60] if playlists else []

        context = {
            'user': user_info,
            'playlists': limited_playlists,
        }

        return render(request, 'index.html', context)
    except Exception as e:
        return render(request, 'index.html', {'error': str(e)})


def playlist_tracks(request, playlist_id):
    """View for displaying tracks of a specific playlist"""
    if not request.session.session_key:
        request.session.create()

    if not is_spotify_authenticated(request.session.session_key):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    spotify_service = SpotifyService(request.session.session_key)

    try:
        tracks = spotify_service.get_playlist_tracks(playlist_id)
        limited_tracks = tracks[:60] if tracks else []

        context = {
            'tracks': limited_tracks,
            'playlist_id': playlist_id
        }

        # Handle HTMX requests differently
        if request.headers.get('HX-Request'):
            html = render_to_string('components/track_list.html', context)
            return HttpResponse(html)

        return JsonResponse(context)
    except Exception as e:
        error_message = f"Error fetching tracks: {str(e)}"
        if request.headers.get('HX-Request'):
            return HttpResponse(f'<div class="alert alert-danger">{error_message}</div>')
        return JsonResponse({'error': error_message}, status=500)


def convert_playlist(request, playlist_id):
    """View for handling playlist conversion"""
    if not request.session.session_key:
        request.session.create()

    if not is_spotify_authenticated(request.session.session_key):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    spotify_service = SpotifyService(request.session.session_key)

    try:
        # Default to clean version
        to_clean = request.GET.get('to_clean', 'true').lower() == 'true'
        result = spotify_service.convert_playlist(playlist_id, to_clean)

        if request.headers.get('HX-Request'):
            return render(request, 'components/conversion_result.html', {
                'result': result
            })

        return JsonResponse(result)
    except Exception as e:
        error_message = f"Error converting playlist: {str(e)}"
        if request.headers.get('HX-Request'):
            return HttpResponse(f'<div class="alert alert-danger">{error_message}</div>')
        return JsonResponse({'error': error_message}, status=500)


class AuthenticationURL(APIView):
    """View for handling Spotify authentication URL generation"""

    def get(self, request, format=None):
        if not request.session.session_key:
            request.session.create()

        scopes = "playlist-modify-public playlist-modify-private playlist-read-private user-library-read"

        url = Request('GET', 'https://accounts.spotify.com/authorize', params={
            'scope': scopes,
            'response_type': 'code',
            'redirect_uri': SP_REDIRECT_URI,
            'client_id': SP_CLIENT_ID,
            'state': request.session.session_key
        }).prepare().url

        return HttpResponseRedirect(url)


def spotify_redirect(request, format=None):
    """View for handling Spotify OAuth redirect"""
    if not request.session.session_key:
        request.session.create()

    code = request.GET.get('code')
    error = request.GET.get('error')
    state = request.GET.get('state')

    if error:
        return HttpResponseRedirect('/error')

    if not code:
        return HttpResponseRedirect('/error?message=no_code')

    try:
        response = post('https://accounts.spotify.com/api/token', data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': SP_REDIRECT_URI,
            'client_id': SP_CLIENT_ID,
            'client_secret': SP_CLIENT_SECRET
        }).json()

        access_token = response.get('access_token')
        refresh_token = response.get('refresh_token')
        expires_in = response.get('expires_in')
        token_type = response.get('token_type')

        if not all([access_token, refresh_token, expires_in, token_type]):
            return HttpResponseRedirect('/error?message=invalid_token_response')

        create_or_update_tokens(
            session_id=request.session.session_key,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            token_type=token_type
        )

        return HttpResponseRedirect('/spotify/')
    except Exception as e:
        return HttpResponseRedirect(f'/error?message=token_exchange_failed&details={str(e)}')


class CheckAuthentication(APIView):
    """View for checking authentication status"""

    def get(self, request, format=None):
        if not request.session.session_key:
            request.session.create()

        is_authenticated = is_spotify_authenticated(request.session.session_key)

        if request.headers.get('HX-Request'):
            if is_authenticated:
                return HttpResponse('<div class="alert alert-success">Authenticated</div>')
            return HttpResponse('<div class="alert alert-warning">Not authenticated</div>')

        return JsonResponse({
            'is_authenticated': is_authenticated,
            'session_id': request.session.session_key
        })


def error_view(request):
    """View for displaying errors"""
    error_message = request.GET.get('message', 'An unknown error occurred')
    error_details = request.GET.get('details', '')

    context = {
        'error_message': error_message,
        'error_details': error_details
    }

    return render(request, '/api/docs', context)