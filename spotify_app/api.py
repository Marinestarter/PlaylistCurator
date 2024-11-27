from ninja import NinjaAPI
from typing import List
from spotify_app.services.schemas import (
    PlaylistResponse,
    PlaylistConversionResponse,
    UserResponse,
    TrackResponse
)
from spotify_app.spotify_service import SpotifyService

api = NinjaAPI()


@api.get("/user", response=UserResponse)
def get_user(request):
    if not request.session.session_key:
        request.session.create()
    spotify_service = SpotifyService(request.session.session_key)
    return spotify_service.get_user()


@api.get("/playlists", response=List[PlaylistResponse])
def get_playlists(request):
    if not request.session.session_key:
        request.session.create()
    spotify_service = SpotifyService(request.session.session_key)
    return spotify_service.get_playlists()


@api.get("/playlists/{playlist_id}/tracks", response=List[TrackResponse])
def get_playlist_tracks(request, playlist_id: str):
    if not request.session.session_key:
        request.session.create()
    spotify_service = SpotifyService(request.session.session_key)
    return spotify_service.get_playlist_tracks(playlist_id)


@api.post("/playlist/{playlist_id}/convert")
def convert_playlist(request, playlist_id: str) -> PlaylistConversionResponse:
    if not request.session.session_key:
        request.session.create()
    spotify_service = SpotifyService(request.session.session_key)
    result = spotify_service.convert_playlist(playlist_id)
    return PlaylistConversionResponse(**result)


@api.post("/playlist/{playlist_id}/additionalSongs")
def missing_songs(request, playlist_id: str, song_uris: List[str]) -> str:
    if not request.session.session_key:
        request.session.create()
    spotify_service = SpotifyService(request.session.session_key)
    return spotify_service.add_additional_songs(playlist_id, song_uris)
