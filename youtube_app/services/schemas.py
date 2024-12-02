from ninja import Schema
from typing import List, Optional, Dict


class YouTubeUserResponse(Schema):
    id: str
    name: str
    external_urls: str

class TrackMetadataResponse(Schema):
    id: str
    title: str
    artists: List[str]
    explicit: Optional[bool]
    url: str

class PlaylistResponse(Schema):
    id: str
    name: str
    tracks: Optional[List[TrackMetadataResponse]]
    external_urls: Dict[str, str]

class TrackResponse(Schema):
    id: str
    title: str
    artists: str
    album: Optional[str]
    duration: Optional[str]
    explicit: Optional[bool]
    url: str

class PlaylistConversionResponse(Schema):
    playlist_id: str
    num_original_clean: int
    num_converted: int
    num_still_missing: int
    still_missing: List[dict[str, str]]  # Each dict should have name, artists, query_url
    potential_matches: dict[str, List[dict]]