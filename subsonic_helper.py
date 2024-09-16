import libsonic
import logging
import os
import random
import constants
import sys
import string
import database

from dotenv import load_dotenv
from os.path import dirname
from os.path import join

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=int(os.environ.get(constants.LOG_LEVEL, constants.LOG_LEVEL_DEFAULT_VALUE)),
        datefmt='%Y-%m-%d %H:%M:%S')

dbms = database.Database(database.SQLITE, dbname='subtify.sqlite3')
database.create_db_tables(dbms)

pysonic = libsonic.Connection(os.environ.get(constants.SUBSONIC_API_HOST), os.environ.get(constants.SUBSONIC_API_USER), os.environ.get(constants.SUBSONIC_API_PASS), appName="Subtify", serverPath=os.environ.get(constants.SUBSONIC_API_BASE_URL, constants.SUBSONIC_API_BASE_URL_DEFAULT_VALUE) + "/rest", port=int(os.environ.get(constants.SUBSONIC_API_PORT)))

def get_artists_array_names():
    pysonic.getArtists()
    
    artist_names = []

    for index in pysonic.getArtists()["artists"]["index"]:
        for artist in index["artist"]:
            artist_names.append(artist["name"])

    return artist_names

    
def get_subsonic_search_results(text_to_search):

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
        subsonic_search = pysonic.search2(set_search)
        if "searchResult2" in subsonic_search and len(subsonic_search["searchResult2"]) > 0 and "song" in subsonic_search["searchResult2"]:
            result.append(subsonic_search)
        count = count + 1

    return result

def get_playlist_id_by_name(playlist_name):  
    playlist_id = None  
    playlists_search = pysonic.getPlaylists()
    if "playlists" in playlists_search and len(playlists_search["playlists"]) > 0:
        single_playlist_search = playlists_search["playlists"]
        if "playlist" in single_playlist_search and len(single_playlist_search["playlist"]) > 0:
            for playlist in single_playlist_search["playlist"]:
                if playlist["name"].strip() == playlist_name.strip():
                    playlist_id = playlist["id"]
                    break
    return playlist_id

def write_playlist(playlist_name, results):
    try:
        playlist_name = os.environ.get(constants.PLAYLIST_PREFIX, constants.PLAYLIST_PREFIX_DEFAULT_VALUE) + playlist_name
        playlist_id = get_playlist_id_by_name(playlist_name)
        if playlist_id is None:
            pysonic.createPlaylist(name = playlist_name, songIds = [])
            logging.info('Creating playlist %s', playlist_name)
            playlist_id = get_playlist_id_by_name(playlist_name)
            

        song_ids = []
        for track in results['tracks']:
            for artist_spotify in track['artists']:
                artist_name_spotify = artist_spotify["name"]
                logging.info('Searching %s - %s in your music library', artist_name_spotify, track['name'])
                text_to_search = artist_name_spotify + " " + track['name']
                subsonic_search_results = get_subsonic_search_results(text_to_search)
                found = False
                excluded = False
                for subsonic_search in subsonic_search_results:
                    for song in subsonic_search["searchResult2"]["song"]:
                        excluded = False
                        song_title  = song["title"].strip().lower()
                        song_album  = song["album"].strip().lower()

                        excluded_words = []
                        excluded_words_string = os.environ.get(constants.EXCLUDED_WORDS, constants.EXCLUDED_WORDS_DEFAULT_VALUE)
                        if excluded_words_string is not None and excluded_words_string != "":
                            excluded_words = excluded_words_string.split(",")

                        if excluded_words is not None and len(excluded_words) > 0:
                            song_title_no_punt = song_title.translate(str.maketrans("", "", string.punctuation))
                            song_title_splitted = song_title_no_punt.split()
                            song_album_no_punt = song_album.translate(str.maketrans("", "", string.punctuation))
                            song_album_splitted = song_album_no_punt.split()
                            countw = 0
                            while excluded is not True and countw < len(excluded_words):
                                excluded_word = excluded_words[countw]
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
                                database.insert_song(dbms, playlist_name, song, artist_spotify, track, 0, playlist_id)
                if os.environ.get(constants.SPOTDL_ENABLED, constants.SPOTDL_ENABLED_DEFAULT_VALUE) == "1" and found is False:
                    is_monitored = True
                    if os.environ.get(constants.LIDARR_ENABLED, constants.LIDARR_ENABLED_DEFAULT_VALUE) == "1":
                        is_monitored = lidarr_helper.is_artist_monitored(artist_name_spotify)
                    if is_monitored:
                        logging.warning('Track %s - %s not found in your music library, using SPOTDL downloader', artist_name_spotify, track['name'])
                        logging.warning('This track will be available after navidrome rescans your music dir')
                        spotdl_helper.download_track(track["external_urls"]["spotify"])
                    else:
                        logging.warning('Track %s - %s not found in your music library', artist_name_spotify, track['name'])
                        logging.warning('This track hasn''t been found in your Lidarr database, skipping download process')
                elif found is False: 
                    logging.warning('Track %s - %s not found in your music library', artist_name_spotify, track['name'])
                    database.insert_song(dbms, playlist_name, None, artist_spotify, track, 1, playlist_id)
                elif found is True: 
                    logging.info('Track %s - %s found in your music library', artist_name_spotify, track['name'])
                
        if len(song_ids) > 0:
            random.shuffle(song_ids)
            if playlist_id is not None:
                pysonic.createPlaylist(playlistId = playlist_id, songIds = song_ids)
                logging.info('Success! Adding songs to playlist %s', playlist_name)

                

    except Exception:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)