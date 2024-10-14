import click


class SpotifyClient(object):
    def __init__(self, id=None, secret=None):
        self.id = id
        self.secret = secret


pass_spotify = click.make_pass_decorator(SpotifyClient)
