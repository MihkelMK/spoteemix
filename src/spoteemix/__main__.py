import re

import click

from spoteemix.config_helper import load_configs
from spoteemix.main import main

DEFAULT_CONFIG = dict(default_map=load_configs())
DEFAULT_CONFIG["help_option_names"] = ["-h", "--help"]


@click.command(context_settings=DEFAULT_CONFIG)
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
@click.option(
    "--client-id",
    type=click.STRING,
    help="The client id of you Spotify API key",
    required=True,
    envvar="SPOTIPY_CLIENT_ID",
)
@click.option(
    "--client-secret",
    type=click.STRING,
    help="The client secret of you Spotify API key",
    required=True,
    envvar="SPOTIPY_CLIENT_SECRET",
)
@click.pass_context
def cli(ctx, playlist, deemix, format, client_id, client_secret):
    """Download Spotify playlist using Deemix.

    PLAYLIST - the URL of the Spotify playlist to download.
    """
    ctx.ensure_object(dict)

    if "http" not in deemix:
        raise click.UsageError(
            "Deemix URL doesn't start with http(s) or is otherwise malformed."
        )

    if "http" not in playlist:
        raise click.UsageError(
            "Playlist URL doesn't start with http(s) or is otherwise malformed."
        )

    if len(client_id) != 32 or not client_id.isalnum():
        raise click.UsageError("Malformed client_id.")

    if len(client_secret) != 32 or not client_secret.isalnum():
        raise click.UsageError("Malformed client_secret.")

    main(
        client_id=client_id,
        client_secret=client_secret,
        deemix_url=deemix,
        pref_file=format,
        playlist_link=playlist,
    )
