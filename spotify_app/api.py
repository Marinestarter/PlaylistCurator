from typing import List

from ninja import NinjaAPI

from spotify_app.services.schemas import (
    PlaylistResponse,
    PlaylistConversionResponse,
    UserResponse,
    TrackResponse
)
from spotify_app.services.spotify_service import SpotifyService

api = NinjaAPI()
spotify_service = SpotifyService()


@api.get("/user", response=UserResponse)
def get_user(request):
    return spotify_service.get_user()


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
