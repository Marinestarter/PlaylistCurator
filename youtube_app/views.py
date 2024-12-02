from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from requests import Request, post
from rest_framework.views import APIView
from .extras import create_or_update_tokens, is_youtube_authenticated
from newMusicCleaner.settings import YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REDIRECT_URI, YOUTUBE_SCOPES


def youtube_interface(request):
    if not is_youtube_authenticated(request.session.session_key):
        return redirect('youtube-auth')
    return JsonResponse({"status": "authenticated"})


class YouTubeAuthURL(APIView):
    def get(self, request, format=None):
        scopes=YOUTUBE_SCOPES
        url = Request('GET', 'https://accounts.google.com/o/oauth2/v2/auth', params={
            'scope': scopes,
            'response_type': 'code',
            'redirect_uri': YOUTUBE_REDIRECT_URI,
            'client_id': YOUTUBE_CLIENT_ID,
            'access_type': 'offline',
            'prompt': 'consent'
        }).prepare().url
        return HttpResponseRedirect(url)


def youtube_redirect(request, format=None):
    code = request.GET.get('code')
    error = request.GET.get('error')

    if error:
        return HttpResponseRedirect('/error')

    response = post('https://oauth2.googleapis.com/token', data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': YOUTUBE_REDIRECT_URI,
        'client_id': YOUTUBE_CLIENT_ID,
        'client_secret': YOUTUBE_CLIENT_SECRET
    }).json()

    access_token = response.get('access_token')
    refresh_token = response.get('refresh_token')
    expires_in = response.get('expires_in')
    token_type = response.get('token_type')

    if not all([access_token, refresh_token, expires_in, token_type]):
        return HttpResponseRedirect('/error?message=invalid_token_response')

    if not request.session.session_key:
        request.session.create()

    create_or_update_tokens(
        session_id=request.session.session_key,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        token_type=token_type
    )

    return HttpResponseRedirect('/api/docs')
