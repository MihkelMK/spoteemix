import re
import sys
from random import randint

import click
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from tqdm import tqdm

pl_regex = re.compile(r".*\/playlist\/(\w*)(\?.*)?")


def get_spotify_playlist_id(pl_link):
    if not (pl_match := re.search(pl_regex, pl_link)):
        sys.exit()

    pl_id = pl_match.group(1)
    return f"spotify:playlist:{pl_id}"


def get_spotify_playlist_info(sp, pl_id):
    playlist_info = sp.playlist(pl_id)
    click.secho(f"\nParsing playlist {playlist_info['name']}", fg="blue", nl=False)
    click.echo(" by ", nl=False)
    click.secho(f"{playlist_info['owner']['display_name']}.", fg="magenta")

    return playlist_info["tracks"]["total"]


def shuffle_playlist(client_secret, client_id, playlist_link, iterations):
    # Used for getting info, no changes being made with this instance
    sp = spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
    )

    playlist_id = get_spotify_playlist_id(playlist_link)
    track_count = get_spotify_playlist_info(sp, playlist_id)

    # Needed for playlist modifications
    scope = "playlist-modify-private"  # playlist-modify-public doesn't work
    sp_oauth = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://127.0.0.1:8888",
        )
    )

    # Spotify uses this to track the playlist state
    # this program knows of when making changes
    snapshot_id = ""

    for _ in tqdm(
        range(iterations),
        desc="Shuffling playlist",
        bar_format="{desc}: {percentage:3.0f}% {bar} {n:3.0f}/{total_fmt}",
        ascii="⣿⣦⣀",
    ):
        # This API asks for a range start index, range length and insert index
        # It will move <range_length> tracks starting from index <range_start>
        # And move those tracks before the track on index <insert_before>
        range_start = randint(0, track_count - 1)

        # Using -2 and the following if statement makes it biased towards 1
        range_length = randint(-2, min(4, track_count - range_start))
        if range_length < 1:
            range_length = 1

        insert_before = randint(0, track_count - range_length + 1)

        response = sp_oauth.playlist_reorder_items(
            playlist_id, range_start, insert_before, range_length, snapshot_id
        )
        snapshot_id = response["snapshot_id"]
