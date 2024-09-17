import libsonic
import logging
import os
import random
from ..constants import constants
from ..utils import utils
from ..exceptions.exceptions import SubsonicOfflineException
import sys
from ..database import database
import re
from libsonic.errors import DataNotFoundError

from dotenv import load_dotenv
from os.path import dirname
from os.path import join

if os.environ.get(constants.SPOTDL_ENABLED, constants.SPOTDL_ENABLED_DEFAULT_VALUE) == "1":
    from . import spotdl_helper
    logging.warning("You have enabled SPOTDL integration, make sure to configure the correct download path and check that you have enough disk space for music downloading.")

if os.environ.get(constants.LIDARR_ENABLED, constants.LIDARR_ENABLED_DEFAULT_VALUE) == "1":
    from . import lidarr_helper
    logging.warning("You have enabled LIDARR integration, if an artist won't be found inside the lidarr database, the download process will be skipped.")

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=int(os.environ.get(constants.LOG_LEVEL, constants.LOG_LEVEL_DEFAULT_VALUE)),
        datefmt='%Y-%m-%d %H:%M:%S')

dbms = database.Database(database.SQLITE, dbname='spotisub.sqlite3')
database.create_db_tables(dbms)

pysonic = libsonic.Connection(os.environ.get(constants.SUBSONIC_API_HOST), os.environ.get(constants.SUBSONIC_API_USER), os.environ.get(constants.SUBSONIC_API_PASS), appName="Spotisub", serverPath=os.environ.get(constants.SUBSONIC_API_BASE_URL, constants.SUBSONIC_API_BASE_URL_DEFAULT_VALUE) + "/rest", port=int(os.environ.get(constants.SUBSONIC_API_PORT)))

def checkPysonicConnection():
    global pysonic
    if pysonic.ping():
        return pysonic
    else:
        raise SubsonicOfflineException()

def get_artists_array_names():
    checkPysonicConnection().getArtists()
    
    artist_names = []

    for index in checkPysonicConnection().getArtists()["artists"]["index"]:
        for artist in index["artist"]:
            artist_names.append(artist["name"])

    return artist_names

    
def get_subsonic_search_results(text_to_search):

    result = []
    searches = []
    searches.append(text_to_search)
    searches.append(text_to_search.split("(", 1)[0].strip())
    searches.append(re.sub(r'[^\w\s]','',text_to_search.split("(", 1)[0]))
    searches.append(text_to_search.split("-", 1)[0].strip())
    searches.append(re.sub(r'[^\w\s]','',text_to_search.split("-", 1)[0]).strip())
    searches.append(text_to_search.split("feat", 1)[0].strip())
    searches.append(re.sub(r'[^\w\s]','',text_to_search.split("feat", 1)[0]).strip())
    set_searches = list(set(searches))
    count = 0
    for set_search in set_searches:
        subsonic_search = checkPysonicConnection().search2(set_search)
        if "searchResult2" in subsonic_search and len(subsonic_search["searchResult2"]) > 0 and "song" in subsonic_search["searchResult2"]:
            result.append(subsonic_search)
        count = count + 1

    return result

def get_playlist_id_by_name(playlist_name):  
    playlist_id = None  
    playlists_search = checkPysonicConnection().getPlaylists()
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
        playlist_name = os.environ.get(constants.PLAYLIST_PREFIX, constants.PLAYLIST_PREFIX_DEFAULT_VALUE).replace("\"", "") + playlist_name
        playlist_id = get_playlist_id_by_name(playlist_name)
        if playlist_id is None:
            checkPysonicConnection().createPlaylist(name = playlist_name, songIds = [])
            logging.info('Creating playlist %s', playlist_name)
            playlist_id = get_playlist_id_by_name(playlist_name)
            database.delete_playlist_relation_by_id(dbms, playlist_id)


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

                        song_title_no_punt = re.sub(r'[^\w\s]','',song_title)
                        song_title_splitted = song_title_no_punt.split()

                        if excluded_words is not None and len(excluded_words) > 0:
                            song_album_no_punt = re.sub(r'[^\w\s]','',song_album)
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

                        song_artist = song["artist"].strip()
                        song_artist_no_punct = re.sub(r'[^\w\s]','',song_artist)
                        artist_name_spotify_no_punct = re.sub(r'[^\w\s]','',artist_name_spotify)                  

                        song_titles = []
                        song_titles.append(song_title.strip())
                        song_titles.append(song_title_no_punt.strip())
                        song_titles.append(song_title.split("(", 1)[0].strip())
                        song_titles.append(re.sub(r'[^\w\s]','',song_title.split("(", 1)[0]))
                        song_titles.append(song_title.split("-", 1)[0].strip())
                        song_titles.append(re.sub(r'[^\w\s]','',song_title.split("-", 1)[0]).strip())
                        song_titles.append(song_title.split("feat", 1)[0].strip())
                        song_titles.append(re.sub(r'[^\w\s]','',song_title.split("feat", 1)[0]).strip()) 

                        song_titles = list(set(song_titles))

                        track_names = []
                        track_names.append(track['name'].strip())
                        track_names.append(re.sub(r'[^\w\s]','',track['name']).strip())
                        track_names.append(track['name'].split("(", 1)[0].strip())
                        track_names.append(re.sub(r'[^\w\s]','',track['name'].split("(", 1)[0]))
                        track_names.append(track['name'].split("-", 1)[0].strip())
                        track_names.append(re.sub(r'[^\w\s]','',track['name'].split("-", 1)[0]).strip())
                        track_names.append(track['name'].split("feat", 1)[0].strip())
                        track_names.append(re.sub(r'[^\w\s]','',track['name'].split("feat", 1)[0]).strip())

                        track_names = list(set(track_names))

                        if (song["id"] not in song_ids
                            and song_artist != '' 
                            and ((artist_name_spotify.lower() == song_artist.lower() or song_artist.lower() in artist_name_spotify.lower() or artist_name_spotify.lower() in song_artist.lower())
                            or  (artist_name_spotify_no_punct.lower() == song_artist_no_punct.lower() or song_artist_no_punct.lower() in artist_name_spotify_no_punct.lower() or artist_name_spotify_no_punct.lower() in song_artist_no_punct.lower()))
                            and excluded is not True
                            and song_title != '' 
                            and compare_title(track_names, song_titles)):
                                song_ids.append(song["id"])
                                found = True
                                database.insert_song(dbms, playlist_id, song, artist_spotify, track)
                                logging.info('Success! Adding song %s - %s from album %s to playlist %s', song_artist, track['name'], song_album, playlist_name)
                                checkPysonicConnection().createPlaylist(playlistId = playlist_id, songIds = song_ids)
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
                    database.insert_song(dbms, playlist_id, None, artist_spotify, track)
                elif found is True: 
                    logging.info('Track %s - %s found in your music library', artist_name_spotify, track['name'])
                
        if len(song_ids) > 0:
            logging.info('Success! Created playlist %s', playlist_name)
        elif len(song_ids) == 0:
            if playlist_id is not None:
                try:
                    checkPysonicConnection().deletePlaylist(playlist_id)
                except DataNotFoundError:
                    pass
                

    except SubsonicOfflineException:
        logging.error('There was an error creating a Playlist, perhaps is your Subsonic server offline?')
    except Exception:
        utils.write_exception()

def compare_title(track_names, song_titles):
    for song_title in song_titles:
        for track_name in track_names:
            if track_name.lower() == song_title.lower() or song_title.lower() in track_name.lower() or track_name.lower() in song_title.lower():
                return True
    return False


def get_playlist_songs(missing=False):
    unmatched_songs_db = database.select_all_playlists(dbms, missing)
    unmatched_songs = {}
    for key in unmatched_songs_db:
        playlist_search = None
        try:
            playlist_search = checkPysonicConnection().getPlaylist(key)
        except SubsonicOfflineException as ex:
            raise ex
        except DataNotFoundError:
            pass
        if playlist_search is None:
            logging.warning('Playlist id "%s" not found, may be you deleted this playlist from Subsonic?', key)
            logging.warning('Deleting Playlist with id "%s" from spotisub database.', key)
            database.delete_playlist_relation_by_id(dbms, key)
        elif playlist_search is not None:
            missings = unmatched_songs_db[key]
            for missing in missings:
                if "subsonic_playlist_id" in missing and missing["subsonic_playlist_id"] is not None:
                    if "playlist" in playlist_search :
                        single_playlist_search = playlist_search["playlist"]

                        if "subsonic_artist_id" in missing and missing["subsonic_artist_id"] is not None:
                            artist_search = checkPysonicConnection().getArtist(missing["subsonic_artist_id"])
                            if "artist" in artist_search:
                                single_artist_search = artist_search["playlist"]
                                missing["subsonic_playlist_name"] = single_artist_search["name"]
                        if "subsonic_song_id" in missing and missing["subsonic_song_id"] is not None:
                            artist_search = checkPysonicConnection().getArtist(missing["subsonic_song_id"])
                            if "song" in song_search:
                                single_song_search = song_search["playlist"]
                                missing["subsonic_song_title"] = single_song_search["title"]
                                if "subsonic_artist_id" not in missing:
                                    missing["subsonic_playlist_name"] = single_artist_search["artist"]

                        if single_playlist_search["name"] not in unmatched_songs:
                            unmatched_songs[single_playlist_search["name"]] = []
                            
                        unmatched_songs[single_playlist_search["name"]].append(missing)

    return unmatched_songs

def remove_subsonic_deleted_playlist():

    spotisub_playlists = database.select_all_playlists(dbms, False)
    for key in spotisub_playlists:
        playlist_search = None
        try:
            playlist_search = checkPysonicConnection().getPlaylist(key)
        except SubsonicOfflineException as ex:
            raise ex
        except DataNotFoundError:
            pass
        if playlist_search is None:
            logging.warning('Playlist id "%s" not found, may be you deleted this playlist from Subsonic?', key)
            logging.warning('Deleting Playlist with id "%s" from spotisub database.', key)
            database.delete_playlist_relation_by_id(dbms, key)

    database.clean_spotify_songs(dbms)