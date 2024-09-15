import glob
import libsonic
import logging
import os
import random
import spotipy  
import sys
import time
import string
import constants

from dotenv import load_dotenv
from os.path import dirname
from os.path import join
from spotipy import SpotifyOAuth

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

os.environ["VERSION"] = "0.1.5"

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=int(os.environ.get("LOG_LEVEL", "40")),
        datefmt='%Y-%m-%d %H:%M:%S')

EXCLUDED_WORDS = constants.EXCLUDED_WORDS
if os.environ.get("EXCLUDED_WORDS") is not None and os.environ.get("EXCLUDED_WORDS").strip() != "":
    EXCLUDED_WORDS = os.environ.get("EXCLUDED_WORDS").split(",")

if os.environ.get("SPOTDL_ENABLED", "0") == "1":
    import spotdl_helper
    logging.warning("You have enabled SPOTDL integration, make sure to configure the correct download path and check that you have enough disk space for music downloading.")

    if os.environ.get("LIDARR_ENABLED", "0") == "1":
        import lidarr_helper
        logging.warning("You have enabled LIDARR integration, if an artist won't be found inside the lidarr database, the download process will be skipped.")

client_id=os.environ.get("SPOTIPY_CLIENT_ID")
client_secret=os.environ.get("SPOTIPY_CLIENT_SECRET")
redirect_uri=os.environ.get("SPOTIPY_REDIRECT_URI")
scope="user-top-read,user-library-read,user-read-recently-played"

creds = SpotifyOAuth(scope=scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, open_browser=False, cache_path=os.path.dirname(os.path.abspath(__file__)) + "/cache/spotipy_cache")

sp = spotipy.Spotify(auth_manager=creds)

serverPath = os.environ.get("SUBSONIC_API_BASE_URL", "") + "/rest"

pysonic = libsonic.Connection(os.environ.get("SUBSONIC_API_HOST"), os.environ.get("SUBSONIC_API_USER"),  os.environ.get("SUBSONIC_API_PASS"), appName="spotify-playlist-generator", serverPath=serverPath, port=int(os.environ.get("SUBSONIC_API_PORT")))

def get_artists_array_names():
    artists = pysonic.getArtists()
    
    artist_names = []

    for index in pysonic.getArtists()["artists"]["index"]:
        for artist in index["artist"]:
            artist_names.append(artist["name"])

    return artist_names


def my_reccommendations(count = None):
    try:
        top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term')
        logging.info('Loaded your custom top tracks')
        time.sleep(2)
        liked_tracks = sp.current_user_saved_tracks(limit=50)
        logging.info('Loaded your top liked tracks')
        time.sleep(2)
        history = sp.current_user_recently_played(limit=50)
        logging.info('Loaded your played tracks')
        time.sleep(2)
        for i in range(int(os.environ.get("NUM_USER_PLAYLISTS","5"))):
            if count is None or (count is not None and count == i):
                logging.info('Searching your reccommendations (playlist %s)', str(i+1))
                top_track_ids = [track['id'] for track in top_tracks['items']]
                liked_track_ids = [track['track']['id'] for track in liked_tracks['items']]
                history_track_ids = [track['track']['id'] for track in history['items']]
                seed_track_ids = top_track_ids + liked_track_ids + history_track_ids
                random.shuffle(seed_track_ids)
                results = sp.recommendations(seed_tracks=seed_track_ids[0:5], limit=int(os.environ.get("ITEMS_PER_PLAYLIST")))
                playlist_name = "My Reccommendations " + str(i+1)
                write_playlist(playlist_name, results)
                if count is not None:
                    break
            time.sleep(10)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)

def get_artist(name):
    results = sp.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        return items[0]
    else:
        return None

def get_navidrome_search_results(text_to_search):

    result = []
    searches = []
    searches.append(text_to_search)
    searches.append(text_to_search.split("(", 1)[0].strip())
    searches.append(text_to_search.split("(", 1)[0].translate(str.maketrans("", "", string.punctuation)).strip())
    searches.append(text_to_search.split("-", 1)[0].strip())
    searches.append(text_to_search.split("-", 1)[0].translate(str.maketrans("", "", string.punctuation)).strip())
    searches.append(text_to_search.split("feat", 1)[0].strip())
    searches.append(text_to_search.split("feat", 1)[0].translate(str.maketrans("", "", string.punctuation)).strip())
    set_searches = list(set(searches))
    count = 0
    for set_search in set_searches:
        navidrome_search = pysonic.search2(set_search)
        if "searchResult2" in navidrome_search and len(navidrome_search["searchResult2"]) > 0 and "song" in navidrome_search["searchResult2"]:
            result.append(navidrome_search)
        count = count + 1

    return result


def write_playlist(playlist_name, results):
    try:
        playlist_name = os.environ.get("PLAYLIST_PREFIX", constants.PLAYLIST_PREFIX) + playlist_name
        song_ids = []
        for track in results['tracks']:
            for artist_spotify in track['artists']:
                artist_name_spotify = artist_spotify["name"]
                logging.info('Searching %s - %s in your music library', artist_name_spotify, track['name'])
                navidrome_search_result = None
                text_to_search = artist_name_spotify + " " + track['name']
                navidrome_search_results = get_navidrome_search_results(text_to_search)
                found = False
                excluded = False
                for navidrome_search in navidrome_search_results:
                    for song in navidrome_search["searchResult2"]["song"]:
                        excluded = False
                        song_title  = song["title"].strip().lower()
                        song_album  = song["album"].strip().lower()

                        if EXCLUDED_WORDS is not None and len(EXCLUDED_WORDS) > 0:
                            song_title_no_punt = song_title.translate(str.maketrans("", "", string.punctuation))
                            song_title_splitted = song_title_no_punt.split()
                            song_album_no_punt = song_album.translate(str.maketrans("", "", string.punctuation))
                            song_album_splitted = song_album_no_punt.split()
                            countw = 0
                            while excluded is not True and countw < len(EXCLUDED_WORDS):
                                excluded_word = EXCLUDED_WORDS[countw]
                                for song_title_sentence in song_title_splitted:
                                    if excluded_word == song_title_sentence.strip().lower():
                                        excluded = True
                                        logging.warning('Excluding search result %s - %s - %s because it contains the excluded word: %s', song["artist"], song["title"].strip(), song["album"], excluded_word)
                                        break
                                for song_album_sentence in song_album_splitted:
                                    if excluded_word == song_album_sentence.strip().lower():
                                        excluded = True
                                        logging.warning('Excluding search result %s - %s - %s because it contains the excluded word: %s', song["artist"], song["title"].strip(), song["album"], excluded_word)
                                        break
                                countw = countw + 1

                        song_artist = song["artist"].strip().lower()

                        if ((song_artist != '' and (artist_name_spotify.lower() == song_artist or song_artist in artist_name_spotify.lower() or artist_name_spotify.lower() in song_artist))
                            and excluded is not True
                            and (song_title != '' and (track['name'].lower() == song_title or song_title in track['name'].lower() or track['name'].lower() in song_title))):
                                song_ids.append(song["id"])
                                found = True
                if os.environ.get("SPOTDL_ENABLED", "0") == "1" and found is False:
                    is_monitored = True
                    if os.environ.get("LIDARR_ENABLED", "0") == "1":
                        is_monitored = lidarr_helper.is_artist_monitored(artist_name_spotify)
                    if is_monitored:
                        logging.warning('Track %s - %s not found in your music library, using SPOTDL downloader', artist_name_spotify, track['name'])
                        logging.warning('This track will be available after navidrome rescan your music dir')
                        spotdl_helper.download_track(track["external_urls"]["spotify"])
                    else:
                        logging.warning('Track %s - %s not found in your music library', artist_name_spotify, track['name'])
                        logging.warning('This track hasn''t been found in your Lidarr database, skipping download process')
                elif found is False: 
                    logging.warning('Track %s - %s not found in your music library', artist_name_spotify, track['name'])
                elif found is True: 
                    logging.info('Track %s - %s found in your music library', artist_name_spotify, track['name'])
                
        if len(song_ids) > 0:
            playlist_id = None
            playlists_search = pysonic.getPlaylists()
            if "playlists" in playlists_search and len(playlists_search["playlists"]) > 0:
                single_playlist_search = playlists_search["playlists"]
                if "playlist" in single_playlist_search and len(single_playlist_search["playlist"]) > 0:
                    for playlist in single_playlist_search["playlist"]:
                        if playlist["name"].strip() == playlist_name.strip():
                            playlist_id = playlist["id"]
                            break
                random.shuffle(song_ids)
            if playlist_id is not None:
                pysonic.createPlaylist(playlistId = playlist_id, songIds = song_ids)
                logging.info('Success! Updating playlist %s', playlist_name)
            else:
                pysonic.createPlaylist(name = playlist_name, songIds = song_ids)
                logging.info('Success! Creating playlist %s', playlist_name)

                

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)

def show_recommendations_for_artist(name):
    logging.info('Searching reccommendations for: %s', name)
    artist = get_artist(name)
    if artist is not None:
        results = sp.recommendations(seed_artists=[artist['id']], limit=int(os.environ.get("ITEMS_PER_PLAYLIST")))
        playlist_name = name + " - Reccommendations"
        write_playlist(playlist_name, results)
    else:
        logging.warning('Artist: %s Not found!', name)

def get_playlist_tracks(item, result, offset_tracks = 0):
    response_tracks = sp.playlist_items(item['id'],
        offset=offset_tracks,
        fields='items.track.id,items.track.name,items.track.artists,total',
        limit=50,
        additional_types=['track'])
    for track_item in response_tracks['items']:
        track = track_item['track']
        logging.info('Found %s - %s inside playlist %s', track['artists'][0]['name'], track['name'], item['name'])
        track_dict = dict({'name': track['name'], 'artists': [{"name": track['artists'][0]['name']}]})
        result["tracks"].append(track)
    time.sleep(2)
    if len(response_tracks['items']) != 0:
        result = get_playlist_tracks(item, result, offset_tracks = offset_tracks + 50)
    return result

def get_user_playlists(offset = 0, single_execution = False, playlist_name = None):

    playlist_result = sp.current_user_playlists(limit=(50 if single_execution is False else 1), offset = offset)

    for item in playlist_result['items']:
        if item['name'] is not None and item['name'].strip() != '' and (playlist_name is None or (playlist_name is not None and item['name'].lower().strip() == playlist_name.lower().strip())):
            logging.info('Importing playlist: %s', item['name'])
            result = dict({'tracks': []})     
            result = get_playlist_tracks(item, result)    
            write_playlist(item['name'].strip(), result)
            if single_execution:
                break    
    
        
    if not single_execution and len(playlist_result['items']) != 0:
        get_user_playlists(offset = offset + 50)

def count_user_playlists(count, offset = 0):
    playlist_result = sp.current_user_playlists(limit=50, offset = offset)
    count = count + len(playlist_result['items'])

    if len(playlist_result['items']) != 0:
        count = count_user_playlists(count, offset = offset + 50)
    return count

def all_artists_recommendations():
    artist_names = get_artists_array_names()
    if len(artist_names) > 0:
        random.shuffle(artist_names)
        for artist_name in artist_names:
            show_recommendations_for_artist(artist_name)

def get_user_saved_tracks():
    result = dict({'tracks': []})
    result = get_user_saved_tracks_playlist(result)
    write_playlist("Saved Tracks", result)

def get_user_saved_tracks_playlist(result, offset_tracks = 0):
    response_tracks = sp.current_user_saved_tracks(
        offset=offset_tracks,
        limit=50)
    for track_item in response_tracks['items']:
        track = track_item['track']
        logging.info('Found %s - %s inside your saved tracks', track['artists'][0]['name'], track['name'])
        track_dict = dict({'name': track['name'], 'artists': [{"name": track['artists'][0]['name']}]})
        result["tracks"].append(track)
    time.sleep(2)
    if len(response_tracks['items']) != 0:
        result = get_user_saved_tracks_playlist(result, offset_tracks = offset_tracks + 50)
    return result

def print_logo():
        version_len = len(os.environ.get("VERSION"))
        print(
            """
░██████╗██╗░░░██╗██████╗░████████╗██╗███████╗██╗░░░██╗
██╔════╝██║░░░██║██╔══██╗╚══██╔══╝██║██╔════╝╚██╗░██╔╝
╚█████╗░██║░░░██║██████╦╝░░░██║░░░██║█████╗░░░╚████╔╝░
░╚═══██╗██║░░░██║██╔══██╗░░░██║░░░██║██╔══╝░░░░╚██╔╝░░
██████╔╝╚██████╔╝██████╦╝░░░██║░░░██║██║░░░░░░░░██║░░░
╚═════╝░░╚═════╝░╚═════╝░░░░╚═╝░░░╚═╝╚═╝░░░░░░░░╚═╝░░░
"""
            + "                                     "[: -(version_len + 2)]
            + "v{} ".format(os.environ.get("VERSION")
            + "\n")
        )
