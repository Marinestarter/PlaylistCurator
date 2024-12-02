from django.http import HttpResponse
from django.template.loader import render_to_string
from ninja import NinjaAPI
from typing import List
from spotify_app.services.schemas import (
    PlaylistResponse,
    PlaylistConversionResponse,
    UserResponse,
    TrackResponse
)
from youtube_app.services.schemas import (
    PlaylistResponse as YoutubePlaylistResponse,
YouTubeUserResponse,
    PlaylistConversionResponse as YoutubeConversionResponse,
    TrackResponse as YoutubeTrackResponse,
    TrackMetadataResponse as YoutubeTrackMetadataResponse)
from spotify_app.spotify_service import SpotifyService
from youtube_app.yt_services import YouTubeMusicService

api = NinjaAPI()


@api.get("/user", response=UserResponse)
def get_user(request):
    if not request.session.session_key:
        request.session.create()
    spotify_service = SpotifyService(request.session.session_key)
    return spotify_service.get_user()


@api.get("/playlists")
def get_playlists(request):
    """HTMX endpoint for fetching playlists"""
    if not request.session.session_key:
        request.session.create()

    spotify_service = SpotifyService(request.session.session_key)
    playlists = spotify_service.get_playlists()

    # Check if it's an HTMX request
    if request.headers.get('HX-Request'):
        # Render only the playlist items
        html = render_to_string('components/playlist_list.html', {
            'playlists': playlists
        })
        return HttpResponse(html)

    # For non-HTMX requests, return JSON
    return playlists


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


@api.get("/youtube/user", response=YouTubeUserResponse)
def get_youtube_user(request):
    if not request.session.session_key:
        request.session.create()
    youtube_service = YouTubeMusicService(request.session.session_key)
    return youtube_service.get_user()


@api.get("/youtube/playlists", response=List[YoutubePlaylistResponse])
def get_youtube_playlists(request):
    if not request.session.session_key:
        request.session.create()
    youtube_service = YouTubeMusicService(request.session.session_key)
    return youtube_service.get_playlists()


@api.get("/youtube/playlists/{playlist_id}/tracks", response=List[YoutubeTrackMetadataResponse])
def get_youtube_playlist_tracks(request, playlist_id: str):
    if not request.session.session_key:
        request.session.create()
    youtube_service = YouTubeMusicService(request.session.session_key)
    return youtube_service.get_playlist_tracks(playlist_id)


@api.post("/youtube/playlist/{playlist_id}/convert")
def convert_youtube_playlist(request, playlist_id: str, to_clean: bool = True) -> YoutubeConversionResponse:
    if not request.session.session_key:
        request.session.create()
    youtube_service = YouTubeMusicService(request.session.session_key)
    result = youtube_service.convert_playlist(playlist_id, to_clean)
    return PlaylistConversionResponse(**result)


@api.get("/youtube/search")
def search_youtube_tracks(request, query: str) -> List[YoutubeTrackResponse]:
    """Search for tracks on YouTube Music"""
    if not request.session.session_key:
        request.session.create()
    youtube_service = YouTubeMusicService(request.session.session_key)
    return youtube_service.search_track(query)


@api.post("/youtube/playlist/create")
def create_youtube_playlist(request, title: str, description: str = "", privacy_status: str = "private") -> dict:
    """Create a new YouTube playlist"""
    if not request.session.session_key:
        request.session.create()
    youtube_service = YouTubeMusicService(request.session.session_key)
    return youtube_service.create_playlist(title, description, privacy_status)


@api.post("/youtube/playlist/{playlist_id}/tracks")
def add_tracks_to_playlist(request, playlist_id: str, video_ids: List[str]) -> dict:
    """Add multiple tracks to a YouTube playlist"""
    if not request.session.session_key:
        request.session.create()
    youtube_service = YouTubeMusicService(request.session.session_key)

    results = {
        'successful': [],
        'failed': []
    }

    for video_id in video_ids:
        if youtube_service.add_track_to_playlist(playlist_id, video_id):
            results['successful'].append(video_id)
        else:
            results['failed'].append(video_id)

    return results


