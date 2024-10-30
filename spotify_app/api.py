from typing import List

from spotify_app.services.spotify_service import SpotifyService
from ninja import NinjaAPI, Schema
from spotify_app.services.schemas import(
    PlaylistResponse,
    PlaylistConversionResponse,
    UserResponse,
    TrackResponse
)

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
def convert_playlist(request, playlist_id: str, to_clean: bool = True) -> PlaylistConversionResponse:
    return spotify_service.convert_playlist(playlist_id, to_clean)
