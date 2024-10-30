#newMusicCleaner/spotify_app/api.py
from ninja import NinjaAPI, Schema
from .services.spotify_service import get_playlist_tracks, find_clean_ver
from typing import List
from ninja.errors import HttpError

api = NinjaAPI()


class PlaylistIn(Schema):
    playlist_link: str


class PlaylistOut(Schema):
    tracks: list[dict]


class TrackOut(Schema):
    name: str
    artists: list[str]
    album: str
    explicit: bool
    id: str


@api.post("/playlist", response=list[TrackOut])
def get_playlist(request, data: PlaylistIn) -> list[TrackOut]:
    try:
        playlist_id = data.playlist_link.split("/")[-1].split("?")[0]
        tracks = get_playlist_tracks(playlist_id)
        return [TrackOut(**track) for track in tracks]
    except Exception as e:
        raise HttpError(400, f"Error processing playlist: {str(e)}")


@api.post('/cleaner', response=list[TrackOut])
def get_clean_version(request, tracks: list[dict]) -> list[TrackOut]:
    clean_track = find_clean_ver(tracks)
    return [TrackOut(**track) for track in clean_track]
