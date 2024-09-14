import asyncio
import re
import sys
import urllib
from time import sleep

import aiohttp
import click
import spotipy
from fuzzywuzzy import fuzz, process
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import TimeoutException, WebDriverWait
from spotipy.oauth2 import SpotifyClientCredentials
from tqdm.asyncio import tqdm_asyncio
from tqdm.auto import tqdm

pl_regex = re.compile(r".*\/playlist\/(\w*)(\?.*)?")
short_title_regex = re.compile(r"(\(.+\))")


def get_spotify_playlist_id(pl_link):
    if not (pl_match := re.search(pl_regex, pl_link)):
        sys.exit()

    pl_id = pl_match.group(1)
    return f"spotify:playlist:{pl_id}"


def get_spotify_playlist_info(sp, pl_id):
    playlist_info = sp.playlist(pl_id)
    click.secho(f"\nDownloading {playlist_info['name']}", fg="blue", nl=False)
    click.echo(" by ", nl=False)
    click.secho(f"{playlist_info['owner']['display_name']}.", fg="magenta")


def get_spotify_track_ids(sp, playlist_id):
    offset = 0

    track_ids = []

    while True:
        response = sp.playlist_items(
            playlist_id,
            offset=offset,
            fields="items.track.id,total",
            additional_types=["track"],
        )

        if len(response["items"]) == 0:
            break

        offset = offset + len(response["items"])

        for item in response["items"]:
            track_ids.append(item["track"]["id"])

    click.echo(f"Ids gathered for {len(track_ids)} songs.\n")
    return track_ids


def spotify_track_query(sp, track_id):
    response = sp.track(track_id)

    track = {"name": response["name"], "artists": []}

    for artist in response["artists"]:
        track["artists"].append(artist["name"])

    return track


async def get_spotify_track_info(sp, track_ids):
    tracks = []

    # Digits of total track count, for n_fmt padding
    total_digits = str(len(str(len(track_ids))))

    for track_id in tqdm(
        track_ids,
        desc="Track info from Spotify",
        bar_format="{desc}:  {percentage:3.0f}% {bar} {n:"
        + total_digits
        + ".0f}/{total_fmt}",
        ascii="⣿⣦⣀",
    ):
        tracks.append(spotify_track_query(sp, track_id))
    return tracks


def selenium_post(driver, deemix_url, path, params):
    driver.execute_script(
        """
    function post(url, path, params, method='post') {
        const form = document.createElement('form');
        form.method = method;
        form.action = url + path;
    
        for (const key in params) {
            if (params.hasOwnProperty(key)) {
            const hiddenField = document.createElement('input');
            hiddenField.type = 'hidden';
            hiddenField.name = key;
            hiddenField.value = params[key];
    
            form.appendChild(hiddenField);
        }
    }

    document.body.appendChild(form);
    form.submit();
    }
    
    post(arguments[0], arguments[1], arguments[2]);
    """,
        deemix_url,
        path,
        params,
    )
    # Sometimes when connecting with http, an alert dialog appears
    try:
        WebDriverWait(driver, 2).until(
            EC.alert_is_present(),
            "Timed out waiting for PA creation " + "confirmation popup to appear.",
        )

        alert = driver.switch_to.alert
        alert.accept()
    except TimeoutException:
        pass
    except NoAlertPresentException:
        pass


def initiate_selenium(deemix_url):
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)

    driver.get(deemix_url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '//span[text()="Logged in"]',
                )
            )
        )
    except TimeoutException:
        raise click.ClickException(
            f"Couldn't log in to Deemix, check if your ARL is up to date at {deemix_url}."
        )
    return driver


def sort_deemix_tracks(track, found_tracks):
    choices = []
    for i, found in enumerate(found_tracks):
        title = found["SNG_TITLE"]
        title_ratio = fuzz.ratio(title, track["name"])

        artist_matches = []

        for artist in found["ARTISTS"]:
            name = artist["ART_NAME"]
            artist_matches.append(process.extractOne(name, track["artists"]))

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


def find_best_match(pref_file, found_tracks, choices):
    best_matches = []

    for i, choice in enumerate(choices):
        if i + 2 > len(choices) or choices[i + 1]["confidence"] < choice["confidence"]:
            best_matches = choices[: i + 1]
            break

    for match in best_matches:
        matched_track = found_tracks[match["index"]]
        has_flac = matched_track["FILESIZE_FLAC"]
        has_320 = matched_track["FILESIZE_MP3_320"]
        has_128 = matched_track["FILESIZE_MP3_128"]

        if pref_file == "flac" and has_flac:
            return [matched_track, match["confidence"]]
        elif pref_file == "mp3_320" and has_320:
            return [matched_track, match["confidence"]]
        elif pref_file == "mp3_128" and has_128:
            return [matched_track, match["confidence"]]

    # Didn't find good match with preferred file type, return match with highest confidence
    return found_tracks[best_matches[0]["index"]], best_matches[0]["confidence"]


async def deemix_track_search(session, deemix_url, track, expanded, short_title=False):
    try:
        if short_title:
            title = re.sub(short_title_regex, "", track["name"])
        else:
            title = track["name"]

        if expanded:
            search_terms = " ".join([title, *track["artists"]])
        else:
            search_terms = title

        search_term = urllib.parse.quote_plus(search_terms)

        async with session.get(
            f"{deemix_url}/api/mainSearch?term={search_term}"
        ) as resp:
            json_data = await resp.json()
            found_tracks = json_data["TRACK"]["data"]

            sorted_tracks = sort_deemix_tracks(track, found_tracks)
            return found_tracks, sorted_tracks
    except Exception as e:
        click.echo(
            "Unable to get url {} due to {}.".format(track["name"], e.__class__),
            err=True,
        )
        return [], []


async def find_track_on_deemix(session, deemix_url, pref_file, track):
    # Sometimes artist names confuse the Deemix search, in these cases try to search only by title
    # Confidence threshold of 75 is an arbitrary magic number
    found_tracks, sorted_tracks = await deemix_track_search(
        session, deemix_url, track, expanded=True
    )
    if len(found_tracks) == 0 or sorted_tracks[0]["confidence"] < 75:
        found_tracks, sorted_tracks = await deemix_track_search(
            session, deemix_url, track, expanded=False
        )

    # Confidence threshold of 60 is an arbitrary magic number
    if len(found_tracks) == 0 or sorted_tracks[0]["confidence"] < 60:
        found_tracks, sorted_tracks = await deemix_track_search(
            session, deemix_url, track, expanded=True, short_title=True
        )

    # Confidence threshold of 60 is an arbitrary magic number
    if len(found_tracks) == 0 or sorted_tracks[0]["confidence"] < 60:
        return track, 0

    return find_best_match(pref_file, found_tracks, sorted_tracks)


def add_to_deemix_cue(deemix, deemix_url, track):
    data = {"bitrate": "null", "url": f"https://www.deezer.com/track/{track['SNG_ID']}"}
    selenium_post(deemix, deemix_url, "/api/addToQueue", params=data)


async def convert_tracks_to_deezer(deemix_url, pref_file, tracks):
    best_matches = []
    not_found = []

    # Digits of total track count, for n_fmt padding
    total_digits = str(len(str(len(tracks))))

    async with aiohttp.ClientSession() as session:
        ret = await tqdm_asyncio.gather(
            *(
                find_track_on_deemix(session, deemix_url, pref_file, track)
                for track in tracks
            ),
            desc="Finding songs on Deemix",
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


def deemix_tracks_to_cue(deemix_url, deezer_matches):
    driver = initiate_selenium(deemix_url)

    # Digits of total track count, for n_fmt padding
    total_digits = str(len(str(len(deezer_matches))))

    for match in tqdm(
        deezer_matches,
        desc="Adding to download queue",
        bar_format="{desc}: {percentage:3.0f}% {bar} {n:"
        + total_digits
        + ".0f}/{total_fmt}",
        ascii="⣿⣦⣀",
    ):
        add_to_deemix_cue(driver, deemix_url, match)
        sleep(0.5)

    driver.quit()


async def parse_playlist(sp, playlist_id):
    track_ids = get_spotify_track_ids(sp, playlist_id)
    tracks = await get_spotify_track_info(sp, track_ids)
    return tracks


def main(client_id, client_secret, deemix_url, pref_file, playlist_link):
    sp = spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
    )

    playlist_id = get_spotify_playlist_id(playlist_link)
    get_spotify_playlist_info(sp, playlist_id)

    tracks = asyncio.run(parse_playlist(sp, playlist_id))

    deezer_matches, no_matches = asyncio.run(
        convert_tracks_to_deezer(deemix_url, pref_file, tracks)
    )
    deemix_tracks_to_cue(deemix_url, deezer_matches)

    click.secho(f"\n{len(deezer_matches)}/{len(tracks)}", fg="green", nl=False)
    click.echo(" tracks downloaded.\n")

    if len(no_matches) > 0:
        click.secho("These songs couldn't be found:", fg="red")

        for track in no_matches:
            click.secho(f"{track['name']}", fg="blue", nl=False)

            click.echo(" - ", nl=False)
            click.secho(f"{', '.join(track['artists'])}", fg="magenta")
