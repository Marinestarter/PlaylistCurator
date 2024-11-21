from ninja import NinjaAPI
from typing import List

from . import spotify_service
from .services.schemas import PlaylistResponse, TrackResponse, PlaylistConversionResponse
from .spotify_auth import SpotifyAuthService
from .spotify_service import SpotifyService
from django.shortcuts import redirect

from .views import get_spotify_client

api = NinjaAPI()

@api.get("/user")
def get_user(request):
    spotify_client = get_spotify_client(request)
    if not spotify_client:
        return redirect('spotify_login')  # Redirect to login if not authenticated

    spotify_service = SpotifyService(spotify_client)
    user_info = spotify_service.get_user()
    return user_info


@api.get("/playlists", response=List[PlaylistResponse])
def get_playlists(request):
    return spotify_service.get_playlists()  


@api.get("/playlists/{playlist_id}/tracks", response=List[TrackResponse])
def get_playlist_tracks(request, playlist_id: str):
    return spotify_service.get_playlist_tracks(playlist_id)


@api.post("/playlist/{playlist_id}/convert")
def convert_playlist(request, playlist_id: str) -> PlaylistConversionResponse:
    result = spotify_service.convert_playlist(playlist_id)
    return PlaylistConversionResponse(**result)


@api.post("/playlist/{playlist_id}/additionalSongs")
def missing_songs(request, playlist_id: str, song_uris: List[str]) -> str:
    return spotify_service.add_additional_songs(playlist_id, song_uris)
