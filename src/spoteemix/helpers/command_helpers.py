import click


class SpotifyClient:
    def __init__(self, id: str, secret: str) -> None:
        self.id = id
        self.secret = secret


pass_spotify = click.make_pass_decorator(SpotifyClient)
