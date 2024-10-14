from pathlib import Path

import click

from spoteemix.convert.file_spotify import file_sp_convert
from spoteemix.convert.spotify_deemix import sp_dmx_convert
from spoteemix.helpers.command_helpers import pass_spotify


@click.command()
@click.argument("playlist", type=click.STRING)
@click.option(
    "--deemix",
    "-d",
    type=click.STRING,
    help="URL of the Deemix instance.",
    default="http://127.0.0.1:6595",
    show_default=True,
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["flac", "mp3_320", "mp3_128"], case_sensitive=False),
    help="Preferred audio format",
    default="mp3_320",
    show_default=True,
)
@pass_spotify
def std(spotify, playlist, deemix, format):
    """Download Spotify playlist using Deemix.

    PLAYLIST - the URL of the Spotify playlist to download.
    """
    if "http" not in deemix:
        raise click.UsageError(
            "Deemix URL doesn't start with http(s) or is otherwise malformed."
        )

    if "http" not in playlist:
        raise click.UsageError(
            "Playlist URL doesn't start with http(s) or is otherwise malformed."
        )

    sp_dmx_convert(
        client_id=spotify.id,
        client_secret=spotify.secret,
        deemix_url=deemix,
        pref_file=format,
        playlist_link=playlist,
    )


@click.command
@click.argument(
    "path",
    default="./",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.argument("name", type=click.STRING)
@pass_spotify
def fts(spotify, path, name):
    """Create Spotify playlist from files in PATH.

    PATH - where to search for audio files
    NAME - name of the created playlist
    """

    file_sp_convert(
        path=path,
        playlist_name=name,
        client_id=spotify.id,
        client_secret=spotify.secret,
    )
