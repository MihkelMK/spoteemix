from datetime import datetime
from typing import Any, TypedDict


class Track(TypedDict):
    added_at: datetime
    added_by: ArtistOrAddedBy
    is_local: bool
    item: ItemOrTrack
    primary_color: None
    track: ItemOrTrack
    video_thumbnail: VideoThumbnail


class ArtistOrAddedBy(TypedDict):
    external_urls: ExternalUrls
    href: str
    id: str
    name: str | None
    type: str
    uri: str


class ItemOrTrack(TypedDict):
    album: TrackAlbum
    artists: list[ArtistOrAddedBy]
    available_markets: list[str]
    disc_number: int
    duration_ms: int
    episode: bool
    explicit: bool
    external_ids: ExternalIds
    external_urls: ExternalUrls
    href: str
    id: str
    is_local: bool
    name: str
    popularity: int
    preview_url: None
    track: bool
    track_number: int
    type: str
    uri: str


class TrackAlbum(TypedDict):
    album_type: str
    artists: list[ArtistOrAddedBy]
    available_markets: list[str]
    external_urls: ExternalUrls
    href: str
    id: str
    images: list[Image]
    name: str
    release_date: str
    release_date_precision: str
    total_tracks: int
    type: str
    uri: str


class Image(TypedDict):
    height: int
    url: str
    width: int


class ExternalIds(TypedDict):
    isrc: str


class VideoThumbnail(TypedDict):
    url: None


class Album(TypedDict):
    album_type: str
    artists: list[Artist]
    available_markets: list[str]
    copyrights: list[Copyright]
    external_ids: ExternalIds
    external_urls: ExternalUrls
    genres: list[Any]
    href: str
    id: str
    images: list[Image]
    label: str
    name: str
    popularity: int
    release_date: str
    release_date_precision: str
    total_tracks: int
    tracks: Tracks
    type: str
    uri: str


class Owner(TypedDict):
    external_urls: ExternalUrls
    href: str
    id: str
    type: str
    uri: str
    display_name: str


class Playlist(TypedDict):
    collaborative: bool
    description: str
    external_urls: ExternalUrls
    href: str
    id: str
    images: list[Image]
    name: str
    owner: Owner
    public: bool
    snapshot_id: str
    items: list[Item]
    tracks: list[Item]
    type: str
    uri: str


class Artist(TypedDict):
    external_urls: ExternalUrls
    href: str
    id: str
    name: str
    type: str
    uri: str


class Copyright(TypedDict):
    text: str
    type: str


class ExternalUrls(TypedDict):
    spotify: str


class Tracks(TypedDict):
    href: str
    items: list[Item]
    limit: int
    next: None
    offset: int
    previous: None
    total: int


class Item(TypedDict):
    artists: list[Artist]
    available_markets: list[str]
    disc_number: int
    duration_ms: int
    explicit: bool
    external_urls: ExternalUrls
    href: str
    id: str
    is_local: bool
    name: str
    preview_url: None
    track_number: int
    type: str
    uri: str
