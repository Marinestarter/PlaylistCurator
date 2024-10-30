from typing import List, Dict, Optional
from ninja import Schema


class ArtistSchema(Schema):
    id: str
    name: str
    uri: str


class TrackResponse(Schema):
    id: str
    name: str
    uri: str
    artists: List[ArtistSchema]
    explicit: bool
    external_urls: Dict[str, str]


class PlaylistResponse(Schema):
    id: str
    name: str
    tracks: Optional[List[TrackResponse]]


class UserResponse(Schema):
    id: str
    display_name: str
    external_urls: Dict[str, str]


class RemainingTrackSchema(Schema):
    name: str
    query_url: str


class PotentialMatchSchema(Schema):
    name: str
    link: str
    uri: str
    original_track_uri: str
    original_track_link: str


class PlaylistConversionResponse(Schema):
    playlist_id: str
    num_original_clean: str
    num_clean_found: str
    num_still_missing: List[RemainingTrackSchema]
    potential_matches: Dict[str, List[PotentialMatchSchema]]
