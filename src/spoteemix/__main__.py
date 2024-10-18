import click

from spoteemix.commands import convert, utils
from spoteemix.config_helper import load_configs
from spoteemix.helpers.command_helpers import SpotifyClient

DEFAULT_CONFIG = dict(default_map=load_configs())
DEFAULT_CONFIG["help_option_names"] = ["-h", "--help"]


@click.group(context_settings=DEFAULT_CONFIG)
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
def cli(ctx, client_id, client_secret):
    ctx.ensure_object(dict)

    if len(client_id) != 32 or not client_id.isalnum():
        raise click.UsageError("Malformed client_id.")

    if len(client_secret) != 32 or not client_secret.isalnum():
        raise click.UsageError("Malformed client_secret.")

    ctx.obj = SpotifyClient(client_id, client_secret)

    pass


cli.add_command(convert)
cli.add_command(utils)
