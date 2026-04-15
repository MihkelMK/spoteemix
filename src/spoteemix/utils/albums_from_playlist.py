import re
import shutil
import sys
import textwrap
from collections import Counter
from dataclasses import dataclass
from typing import Any

import click
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from tqdm import tqdm

from spoteemix.types.spotify import Album, Playlist, Track

pl_regex = re.compile(r".*\/playlist\/(\w*)(\?.*)?")


@dataclass
class AlbumTableLine:
    index: int
    count: int
    tracks: int
    title: str
    artist: str


@dataclass
class AlbumTableLengths:
    index: int
    count: int
    tracks: int
    title: int
    artist: int


@dataclass
class Meta:
    limit: int
    offset: int
    total: int


def get_spotify_playlist_id(pl_link: str) -> str:
    if not (pl_match := re.search(pl_regex, pl_link)):
        sys.exit()

    pl_id = pl_match.group(1)
    return f"spotify:playlist:{pl_id}"


def get_spotify_playlist_info(sp: Any, pl_id: str) -> tuple[str, int]:
    playlist_info: dict[str, Any] = sp.playlist(pl_id, additional_types=[])

    name: str = playlist_info["name"]
    total: int = playlist_info["items"]["total"]
    return (name, total)


def get_spotify_playlist_items(
    sp: Any, pl_id: str, offset: int = 0, limit: int = 50
) -> tuple[list[Track], Meta]:
    playlist_info: dict[str, Any] = sp.playlist_items(pl_id, limit=limit, offset=offset)

    tracks: list[Track] = playlist_info["items"]
    meta = Meta(
        limit=playlist_info["limit"],
        offset=playlist_info["offset"],
        total=playlist_info["total"],
    )
    return (tracks, meta)


def get_album_ids(sp: Any, pl_id: str, total: int | None = None) -> Counter[str]:
    tracks: list[Track] = []
    offset: int = 0

    # Digits of total track count, for n_fmt padding
    total_digits = str(len(str(total)))
    t = tqdm(
        total=total,
        desc="Finding album ids",
        bar_format="{desc}: {percentage:3.0f}% {bar} {n:"
        + total_digits
        + ".0f}/{total_fmt}",
        ascii="⣿⣦⣀",
    )

    while True:
        left: int | None = total - offset if total else None
        limit: int = min(left, 50) if left else 50

        new_tracks, meta = get_spotify_playlist_items(
            sp, pl_id, offset=offset, limit=limit
        )

        if total != meta.total:
            total = meta.total

        tracks.extend(new_tracks)

        t.update(meta.limit)
        offset += meta.limit

        if offset >= meta.total:
            break

    t.close()

    albums = Counter(track["item"]["album"]["id"] for track in tracks)
    return albums


def get_album(sp: Any, album_id: str) -> Album:
    album: Album = sp.album(album_id)
    return album


def get_albums_from_ids(sp: Any, ids: Counter[str]) -> list[tuple[Album, int]]:
    albums: list[tuple[Album, int]] = []

    # Digits of total track count, for n_fmt padding
    total_digits = str(len(str(len(ids))))

    for id, count in tqdm(
        ids.items(),
        desc="Looking up albums",
        bar_format="{desc}: {percentage:3.0f}% {bar} {n:"
        + total_digits
        + ".0f}/{total_fmt}",
        ascii="⣿⣦⣀",
    ):
        if count > 1:
            albums.append((get_album(sp, id), count))

    return sorted(
        albums, key=lambda x: (x[1], x[0].get("total_tracks", 0)), reverse=True
    )


def get_user_playlists(
    sp_oauth: Any, offset: int = 0, limit: int = 50
) -> tuple[list[Playlist], Meta]:
    playlist_info: dict[str, Any] = sp_oauth.current_user_playlists(
        limit=limit, offset=offset
    )

    playlists = playlist_info["items"]
    meta = Meta(
        limit=playlist_info["limit"],
        offset=playlist_info["offset"],
        total=playlist_info["total"],
    )
    return (playlists, meta)


def find_user_playlist(sp_oauth: Any, pl_name: str) -> str | None:
    playlists: list[Playlist] = []
    total: int | None = None
    offset: int = 0

    while True:
        left: int | None = total - offset if total else None
        limit: int = min(left, 50) if left else 50

        new_playlists, meta = get_user_playlists(sp_oauth, offset=offset, limit=limit)

        if total != meta.total:
            total = meta.total

        playlists.extend(new_playlists)

        offset += meta.limit
        if offset >= meta.total:
            break

    for playlist in playlists:
        if playlist["name"] == pl_name:
            return playlist["id"]

    return None


def create_playlist(sp_oauth: Any, name: str, description: str) -> str:
    response = sp_oauth.current_user_playlist_create(
        name=name, public=False, description=description
    )
    return response["id"]


def add_tracks_to_playlist(
    sp_oauth: Any, pl_id: str, item_uris: list[str], replace: bool = False
) -> None:
    if replace:
        sp_oauth.playlist_replace_items(playlist_id=pl_id, items=item_uris)
    else:
        sp_oauth.playlist_add_items(playlist_id=pl_id, items=item_uris)


def print_album_table(lines: list[AlbumTableLine]) -> None:
    longest_lines = AlbumTableLengths(index=0, count=0, tracks=0, title=0, artist=0)

    for line in lines:
        if (index_len := len(str(line.index))) > longest_lines.index:
            longest_lines.index = index_len
        if (count_len := len(str(line.count))) > longest_lines.count:
            longest_lines.count = count_len
        if (tracks_len := len(str(line.tracks))) > longest_lines.tracks:
            longest_lines.tracks = tracks_len
        if (title_len := len(line.title)) > longest_lines.title:
            longest_lines.title = title_len
        if (artist_len := len(line.artist)) > longest_lines.artist:
            longest_lines.artist = artist_len

    terminal_width = shutil.get_terminal_size().columns

    # [index] + ] + space = index + 2, plus " | " separators (3 chars each x3) and trailing fields
    fixed_width = (
        (longest_lines.index + 2)
        + (longest_lines.count)
        + (longest_lines.tracks)
        + 3 * 3
    )
    available = terminal_width - fixed_width - 3  # -3 for the " | " after title

    max_title = min(longest_lines.title, int(available * 0.6))
    max_artist = min(longest_lines.artist, available - max_title)

    # Blank prefix for continuation lines, mirrors the fixed columns
    fixed_blank = " " * (
        longest_lines.index + 2 + 3 + longest_lines.count + 3 + longest_lines.tracks + 3
    )

    print("idx".rjust(longest_lines.index + 2), end=" | ")
    print("#".rjust(longest_lines.count), end=" | ")
    print("♫".rjust(longest_lines.tracks), end=" | ")
    print("title".ljust(max_title), end=" | ")
    print("artist".ljust(max_artist))
    print("-" * terminal_width)

    for line in lines:
        title_lines = textwrap.wrap(line.title, max_title) or [""]
        artist_lines = textwrap.wrap(line.artist, max_artist) or [""]

        row_height = max(len(title_lines), len(artist_lines))
        title_lines += [""] * (row_height - len(title_lines))
        artist_lines += [""] * (row_height - len(artist_lines))

        for i, (title_part, artist_part) in enumerate(
            zip(title_lines, artist_lines, strict=True)
        ):
            if i == 0:
                print(f"[{line.index + 1}]".rjust(longest_lines.index + 2), end=" | ")
                print(str(line.count).rjust(longest_lines.count), end=" | ")
                print(str(line.tracks).rjust(longest_lines.tracks), end=" | ")
            else:
                print(fixed_blank, end="")
            print(title_part.ljust(max_title), end=" | ")
            print(artist_part.ljust(max_artist))


def parse_selection(selection: str) -> list[int]:
    if "-" in selection:
        start, stop = [int(index) for index in selection.split("-")]
        return [i for i in range(start, stop + 1)]
    else:
        return [int(index) for index in selection.split(" ")]


def print_album_selection(albums: list[Album]) -> None:
    print("\nSelected albums:")
    for album in albums:
        print(f"* {album['name']} - {album['artists'][0]['name']}")


def prompt_album_select(albums: list[tuple[Album, int]]):
    table: list[AlbumTableLine] = []
    for i, [album, count] in enumerate(albums):
        artist = album["artists"][0]["name"]
        table.append(
            AlbumTableLine(
                index=i,
                count=count,
                tracks=album["total_tracks"],
                title=album["name"],
                artist=artist,
            )
        )

    print()
    print_album_table(table)
    print()
    selection = click.prompt("Select album ids (eg: 1 2 3 or 1-3)")
    ids = parse_selection(selection)

    if (out_of_range := min(ids)) == 0 or (out_of_range := max(ids)) > len(table):
        raise click.ClickException(f"index {out_of_range} out of range")

    selected_albums = [albums[i - 1][0] for i in ids]
    return selected_albums


def main(client_secret: str, client_id: str, playlist_link: str) -> None:
    # Used for getting info, no changes being made with this instance
    sp: Any = spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
    )

    playlist_id = get_spotify_playlist_id(playlist_link)
    playlist_name, total_tracks = get_spotify_playlist_info(sp, playlist_id)

    print(f"Found playlist: '{playlist_name}' ({total_tracks} tracks)")

    album_ids = get_album_ids(sp, playlist_id, total_tracks)
    albums = get_albums_from_ids(sp, album_ids)

    selected_albums: list[Album] = prompt_album_select(albums)
    print_album_selection(selected_albums)

    new_playlist_name = f"Albums from {playlist_name}"
    new_playlist_description = (
        f"Most frequent albums from playlist '{playlist_name}'. Generated by spoteemix"
    )
    click.confirm(
        f"Add these into new playlist '{new_playlist_name}'?",
        default=True,
        abort=True,
    )

    track_uris: list[str] = []
    for album in selected_albums:
        track_uris.extend([track["uri"] for track in album["tracks"]["items"]])

    # Needed for playlist modifications
    scope = "playlist-read-private,playlist-modify-private"
    sp_oauth: Any = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://127.0.0.1:8888",
        )
    )

    replace_tracks = False
    if pl_id := find_user_playlist(sp_oauth, new_playlist_name):
        click.confirm(
            "Playlist with that name exist. Overwrite?", default=True, abort=True
        )
        replace_tracks = True
    else:
        pl_id = create_playlist(sp_oauth, new_playlist_name, new_playlist_description)

    add_tracks_to_playlist(sp_oauth, pl_id, track_uris, replace=replace_tracks)
