import asyncio
import urllib

import click
import spotipy
from fuzzywuzzy import fuzz, process
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from tqdm.asyncio import tqdm_asyncio


def sort_spotify_tracks(track, found_tracks):
    choices = []
    for i, found in enumerate(found_tracks):
        title = found["name"]
        title_ratio = fuzz.ratio(title, track["title"])

        if track["artists"] == []:
            average_ratio = title_ratio
        else:
            artist_matches = []
            for artist in found["artists"]:
                name = artist["name"]
                matching_artist = process.extractOne(name, track["artists"])

                if matching_artist != None:
                    artist_matches.append(matching_artist)

            artist_matches = sorted(artist_matches, key=lambda x: -x[1])

            all_ratios = [title_ratio, *[match[1] for match in artist_matches]]
            average_ratio = sum(all_ratios) / len(all_ratios)

        choices.append(
            {
                "index": i,
                "confidence": average_ratio,
            }
        )

    return sorted(choices, key=lambda x: -x["confidence"])


def find_best_match(found_tracks, choices):
    best_matches = []

    for i, choice in enumerate(choices):
        if i + 2 > len(choices) or choices[i + 1]["confidence"] < choice["confidence"]:
            best_matches = choices[: i + 1]
            break

    return found_tracks[best_matches[0]["index"]], best_matches[0]["confidence"]


async def spotify_track_search(sp, track):
    try:
        search_terms = f"{track['title']} {' '.join(track['artists'])}"

        search_term = urllib.parse.quote_plus(search_terms)

        result = sp.search(q=search_term, limit=5, offset=0, type="track")

        found_tracks = result["tracks"]["items"]

        sorted_tracks = sort_spotify_tracks(track, found_tracks)
        return found_tracks, sorted_tracks

    except TypeError as e:
        print(e)
        return [], []
    except Exception as e:
        click.echo(
            "Unable to get url {} due to {}.".format(track["title"], e.__class__),
            err=True,
        )
        return [], []


async def find_track_on_spotify(sp, track):
    # Confidence threshold of 75 is an arbitrary magic number
    found_tracks, sorted_tracks = await spotify_track_search(sp, track)

    # Confidence threshold of 60 is an arbitrary magic number
    if len(found_tracks) == 0 or sorted_tracks[0]["confidence"] < 60:
        return track, 0

    return find_best_match(found_tracks, sorted_tracks)


async def tracks_to_spotify(sp, tracks):
    best_matches = []
    not_found = []

    # Digits of total track count, for n_fmt padding
    total_digits = str(len(str(len(tracks))))

    ret = await tqdm_asyncio.gather(
        *(find_track_on_spotify(sp, track) for track in tracks),
        desc="Finding songs on Spotify",
        bar_format="{desc}:  {percentage:3.0f}% {bar} {n:"
        + total_digits
        + ".0f}/{total_fmt}",
        ascii="⣿⣦⣀",
    )

    for best_match, confidence in ret:
        if confidence == 0:
            not_found.append(best_match)
        else:
            best_matches.append(best_match)

    return best_matches, not_found


def create_spotify_playlist(sp, name, matches):
    user_id = sp.current_user()["id"]

    ret = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=False,
        collaborative=False,
        description="Created by spoteemix",
    )
    playlist_id = ret["id"]
    playlist_link = ret["external_urls"]["spotify"]

    click.echo("Playlist ", nl=False)
    click.secho(name, fg="blue", nl=False)
    click.echo(" created with id ", nl=False)
    click.secho(playlist_id, fg="magenta", nl=False)
    click.echo(".")

    track_ids = []

    for match in matches:
        track_ids.append(match["uri"])

    sp.playlist_add_items(playlist_id, track_ids)

    click.secho("\nTracks successfuly added to playlist.\n", fg="green")
    click.echo(playlist_link)


def parse_files(path):
    mp3_files = path.glob("*.mp3")
    tracks = []

    for file in mp3_files:
        track_info = file.name.replace(".mp3", "")
        try:
            artist, title = track_info.split(" - ", 1)
            tracks.append({"artists": [artist], "title": title})
        except ValueError:
            tracks.append({"artists": "", "title": track_info})

    return tracks


def file_sp_convert(path, playlist_name, client_id, client_secret):
    scope = "playlist-modify-private"
    sp = spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
    )

    tracks = parse_files(path)

    matches, no_matches = asyncio.run(tracks_to_spotify(sp, tracks))

    click.secho(f"\n{len(matches)}/{len(tracks)}", fg="green", nl=False)
    click.echo(" tracks found.\n")

    if len(no_matches) > 0:
        click.secho("These songs couldn't be found:", fg="red")

        for track in no_matches:
            click.secho(f"{track['title']}", fg="blue", nl=False)

            click.echo(" - ", nl=False)
            click.secho(f"{', '.join(track['artists'])}", fg="magenta")

    if len(matches) == 0:
        click.secho("\n No matches, won't create playlist.", fg="red")
    else:
        click.echo("\nStart creating playlist, initiate OAUTH.")

        sp_oauth = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=scope,
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri="http://127.0.0.1:8888",
            )
        )
        create_spotify_playlist(sp_oauth, playlist_name, matches)
