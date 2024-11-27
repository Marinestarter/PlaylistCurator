from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from requests import Request, post
from rest_framework.views import APIView

from newMusicCleaner.settings import SP_REDIRECT_URI, SP_CLIENT_ID, SP_CLIENT_SECRET
from .extras import create_or_update_tokens, is_spotify_authenticated


def spotify_interface(request):
    # This will be your main interface view
    if not is_spotify_authenticated(request.session.session_key):
        return redirect('spotify-auth')
    return JsonResponse({"status": "authenticated"})


class AuthenticationURL(APIView):
    def get(self, request, format=None):
        scopes = "playlist-modify-public playlist-modify-private playlist-read-private user-library-read"
        url = Request('GET', 'https://accounts.spotify.com/authorize', params={
            'scope': scopes,
            'response_type': 'code',
            'redirect_uri': SP_REDIRECT_URI,
            'client_id': SP_CLIENT_ID
        }).prepare().url
        return HttpResponseRedirect(url)


def spotify_redirect(request, format=None):
    code = request.GET.get('code')
    error = request.GET.get('error')
    if error:
        # Old: return error
        # Added proper error redirect
        return HttpResponseRedirect('/error')
    print(f"Got auth code: {code[:10]}...")

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

    print(access_token)

    if not all([access_token, refresh_token, expires_in, token_type]):
        return HttpResponseRedirect('/error?message=invalid_token_response')


    if not request.session.session_key:
        request.session.create()

    print(f"Got access token: {access_token[:10]}...")
    print(f"Session key: {request.session.session_key}")
    authKey = request.session.session_key

    create_or_update_tokens(
        session_id=authKey,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        token_type=token_type
    )

    #create a redirect URL to the current song details
    redirect_url = "/api/docs"
    return HttpResponseRedirect(redirect_url)

    # Check whether the user has been authenticated by Spotify


class CheckAuthentication(APIView):
    def get(self, request, format=None):
        if not request.session.session_key:
            request.session.create()

        session_id = request.session.session_key
        is_authenticated = is_spotify_authenticated(session_id)

        if is_authenticated:
            redirect_url = ""
            return HttpResponseRedirect(redirect_url)
        else:
            redirect_url = ""
            return HttpResponseRedirect(redirect_url)
