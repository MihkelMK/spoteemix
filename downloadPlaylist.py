dev_tracks = [
    {"artists": ["Rome in Silver"], "name": "Waiting..."},
    {"artists": ["wes mills"], "name": "nintendo 64"},
    {"artists": ["Disco Lines", "demotapes"], "name": "RWEOK?"},
    {"artists": ["Andruss"], "name": "Frikitona"},
    {
        "artists": [
            "Kerri Chandler",
            "Dennis Quin",
            "Troy Denari",
            "Faster Horses",
        ],
        "name": "You Are In My System - Faster Horses Sport Mix",
    },
    {"artists": ["Josh Dorey"], "name": "Feed Your Soul"},
    {"artists": ["Starjunk 95"], "name": "Grimestar"},
    {"artists": ["Duskus"], "name": "Cut"},
    {
        "artists": ["Paul Woolford", "LF SYSTEM", "Shayan"],
        "name": "In My Head (feat. Shayan)",
    },
    {"artists": ["LF SYSTEM"], "name": "Hungry (For Love)"},
    {
        "artists": ["LF SYSTEM", "Tommy Villiers"],
        "name": "Afraid To Feel - Tommy Villiers Remix",
    },
    {"artists": ["heynat"], "name": "poyo!"},
    {"artists": ["TWAN"], "name": "Carry On"},
    {"artists": ["Niko The Kid", "Benson"], "name": "Hella Good"},
    {"artists": ["Dylan & Harry", "Party Favor", "Baauer"], "name": "Smoke"},
    {"artists": ["Oppidan"], "name": "You & I"},
    {"artists": ["Conducta"], "name": "3FALL"},
    {"artists": ["Square Perception"], "name": "Alone"},
    {"artists": ["SVDKO"], "name": "DAYJOB"},
    {"artists": ["Vintage Culture", "Maverick Sabre", "Tom Breu"], "name": "Weak"},
    {"artists": ["Mézigue"], "name": "Du son pour les gars sûrs"},
    {"artists": ["Diffrent"], "name": "A Little Closer"},
    {"artists": ["ZPKF", "Darzak"], "name": "Cloods - Darzack Remix"},
    {"artists": ["Diffrent"], "name": "Happiness"},
    {"artists": ["JEV"], "name": "AINT EASIER"},
    {"artists": ["JEV"], "name": "DREAMER"},
    {"artists": ["JEV"], "name": "be free"},
    {"artists": ["JEV"], "name": "4U"},
    {"artists": ["JEV"], "name": "COMPLICATED"},
    {"artists": ["ESCE"], "name": "Come A Little Closer - VIP Mix"},
    {
        "artists": ["LOSTBOYJAY", "Billy Raffoul"],
        "name": "Say Goodbye (feat. Billy Raffoul)",
    },
    {"artists": ["Class Fools"], "name": "Some Nights"},
    {"artists": ["MANT", "HAYLA"], "name": "Lonely Days"},
    {
        "artists": ["Riton", "Kah-Lo", "GEE LEE"],
        "name": "Fake ID (Coke & Rum Remix)",
    },
    {
        "artists": ["Flex (UK)", "Nate Dogg"],
        "name": "6 In the Morning (feat. Nate Dogg)",
    },
    {"artists": ["Malugi"], "name": "Reach Out"},
    {"artists": ["t e s t p r e s s"], "name": "U"},
    {"artists": ["Belters Only", "Sonny Fodera", "Jazzy"], "name": "Life Lesson"},
    {"artists": ["Higgo", "mustbejohn"], "name": "Pretty Little Raver"},
    {
        "artists": ["John Summit", "Sub Focus", "Julia Church"],
        "name": "Go Back (feat. Julia Church)",
    },
    {"artists": ["Lemtom"], "name": "Bancroft"},
    {"artists": ["Sosa UK"], "name": "Your Love"},
    {"artists": ["DJ HEARTSTRING", "Narciss"], "name": "While U Sleep"},
    {"artists": ["Torren Foot", "Azealia Banks"], "name": "New Bottega"},
    {"artists": ["EFESIAN"], "name": "Can't Be Stopped"},
    {"artists": ["Oden & Fatzo", "Camden Cox"], "name": "Lady Love"},
    {
        "artists": ["Reel Mood", "Taiki Nulight", "Jack Beats"],
        "name": "Every Night",
    },
    {"artists": ["Palace"], "name": "Vision"},
    {"artists": ["Murphy's Law (UK)"], "name": "Need To Know"},
    {"artists": ["it's murph"], "name": "123 Round Again"},
    {"artists": ["Bonkers"], "name": "Pilsplaat"},
    {"artists": ["Nikita, the Wicked"], "name": "The Auction"},
    {"artists": ["Quarterhead", "SESA"], "name": "You Will See"},
    {"artists": ["Skeptic", "Sophia Violet"], "name": "Want Me"},
    {
        "artists": ["Artemas", "southstar"],
        "name": "i like the way you kiss me - southstar remix",
    },
    {"artists": ["Dusky", "Denham Audio"], "name": "Everything I Do"},
    {"artists": ["Club Angel"], "name": "Control Dem"},
    {"artists": ["Justin Jay"], "name": "Monster"},
    {"artists": ["Skin On Skin"], "name": "Magic"},
    {"artists": ["Skeptic"], "name": "Bring Me Home"},
    {"artists": ["Disclosure"], "name": "She’s Gone, Dance On"},
]


import asyncio
import re
import sys
import urllib

import aiohttp
import spotipy
from dotenv import load_dotenv
from fuzzywuzzy import fuzz, process
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from spotipy.oauth2 import SpotifyClientCredentials
from tqdm.asyncio import tqdm, tqdm_asyncio

load_dotenv()

pl_regex = re.compile(r".*\/playlist\/(\w*)(\?.*)?")


def get_spotify_playlist_id():
    pl_link = input("Enter the playlist link: ")
    if not (pl_match := re.search(pl_regex, pl_link)):
        sys.exit()

    pl_id = pl_match.group(1)
    return f"spotify:playlist:{pl_id}"


def get_spotify_track_ids(sp, playlist_id):
    print("Requesting track ids.")
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

        print(f"Request - [{offset}]")
        offset = offset + len(response["items"])

        for item in response["items"]:
            track_ids.append(item["track"]["id"])

    print(f"Ids gathered for {len(track_ids)} songs.\n")
    return track_ids


async def get_spotify_track_info(sp, track_ids):
    print("Requesting track info.")

    tracks = []

    for i, id in enumerate(track_ids):
        print(f"Gathering info for track nr {i}", end="\r")
        response = sp.track(id)

        track = {"name": response["name"], "artists": []}

        for artist in response["artists"]:
            track["artists"].append(artist["name"])

        tracks.append(track)

    print("\nTracks gathered.\n")
    return tracks


def selenium_post(driver, path, params):
    driver.execute_script(
        """
    function post(path, params, method='post') {
        const form = document.createElement('form');
        form.method = method;
        form.action = path;
    
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
    
    post(arguments[1], arguments[0]);
    """,
        params,
        path,
    )


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
    finally:
        print("Initiated Deemix session.\n")
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


async def deemix_track_search(session, deemix_url, track, expanded):
    try:
        if expanded:
            search_terms = " ".join([track["name"], *track["artists"]])
        else:
            search_terms = track["name"]

        search_term = urllib.parse.quote_plus(search_terms)

        async with session.get(
            f"{deemix_url}/api/mainSearch?term={search_term}"
        ) as resp:
            json_data = await resp.json()
            found_tracks = json_data["TRACK"]["data"]

            sorted_tracks = sort_deemix_tracks(track, found_tracks)
            return found_tracks, sorted_tracks
    except Exception as e:
        print("Unable to get url {} due to {}.".format(track["name"], e.__class__))
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
        return {"SNG_TITLE": track["name"]}, 0

    return find_best_match(pref_file, found_tracks, sorted_tracks)


def add_to_deemix_cue(deemix, deemix_url, track):
    print("Strarting download.")
    data = {"bitrate": "null", "url": f"https://www.deezer.com/track/{track['SNG_ID']}"}
    selenium_post(deemix, f"{deemix_url}/api/addToQueue", params=data)


async def convert_tracks_to_deezer(deemix_url, pref_file, tracks):
    best_matches = []

    print("Looking for songs in Deemix:")

    async with aiohttp.ClientSession() as session:
        ret = await tqdm_asyncio.gather(
            *(
                find_track_on_deemix(session, deemix_url, pref_file, track)
                for track in tracks
            )
        )
    for best_match, confidence in ret:
        if confidence == 0:
            print(f"Couldn't find {best_match['SNG_TITLE']}.")
        else:
            print(
                f"Found {best_match['SNG_TITLE']} with {round(confidence)}% confidence."
            )
            best_matches.append(best_match)

    return best_matches


def download_tracks(deezer_matches):
    driver = initiate_selenium(deemix_url)

    for match in deezer_matches:
        print(f"Adding {match['SNG_TITLE']} to download queue.")
        add_to_deemix_cue(driver, deemix_url, match)

    driver.quit()


async def main(sp, deemix_url, pref_file):
    # playlist_id = get_spotify_playlist_id()
    # playlist_id = "spotify:playlist:6LSNeL6venXT0Cqx0JO5c0"

    # track_ids = get_spotify_track_ids(sp, playlist_id)
    # tracks = get_spotify_track_info(sp, track_ids)
    tracks = dev_tracks
    deezer_matches = await convert_tracks_to_deezer(deemix_url, pref_file, tracks)
    # download_tracks(deezer_matches)


if __name__ == "__main__":
    deemix_url = "http://127.0.0.1:6595"
    pref_file = "mp3_320"

    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    asyncio.run(main(sp, deemix_url, pref_file))
