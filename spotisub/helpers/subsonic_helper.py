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
            if "name" in artist:
                artist_names.append(artist["name"])

    return artist_names

def search_artist(artist_name):
    artist_names = []

    for index in checkPysonicConnection().getArtists()["artists"]["index"]:
        for artist in index["artist"]:
            if "name" in artist:
                if artist_name.strip().lower() == artist["name"].strip().lower():
                    return artist["name"]

    return None
    
def get_subsonic_search_results(text_to_search):
    result = {}
    set_searches = utils.generate_compare_array(text_to_search)
    for set_search in set_searches:
        subsonic_search = checkPysonicConnection().search2(set_search)
        if "searchResult2" in subsonic_search and len(subsonic_search["searchResult2"]) > 0 and "song" in subsonic_search["searchResult2"]:
            for song in subsonic_search["searchResult2"]["song"]:
                if "id" in song and song["id"] not in result:
                    result[song["id"]] = song
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

        excluded_words = []
        excluded_words_string = os.environ.get(constants.EXCLUDED_WORDS, constants.EXCLUDED_WORDS_DEFAULT_VALUE).replace("\"","")
        if excluded_words_string is not None and excluded_words_string != "":
            excluded_words = excluded_words_string.split(",")

        song_ids = []
        track_helper = []
        for track in results['tracks']:
            found = False
            for artist_spotify in track['artists']:
                if found is False:
                    excluded = False
                    if artist_spotify != '' and "name" in artist_spotify:
                        artist_name_spotify = artist_spotify["name"]
                        logging.info('Searching %s - %s in your music library', artist_name_spotify, track['name'])
                        text_to_search = artist_name_spotify + " " + track['name']
                        if ("name" in track and utils.compare_string_to_exclusion(track['name'], excluded_words)
                            or ("album" in track and "name" in track["album"] and utils.compare_string_to_exclusion(track["album"]["name"], excluded_words))):
                            excluded = True
                        elif "name" in track:
                            subsonic_search_results = get_subsonic_search_results(text_to_search)
                            skipped_songs = []
                            for song_id in subsonic_search_results:
                                song = subsonic_search_results[song_id]
                                if song["artist"] != '' and track['name'] != '' and song["album"] != '' and song["title"] != '':
                                    logging.info('Found %s - %s - %s in your music library', song["artist"], song["title"], song["album"])
                                    placeholder = song["artist"] + " " + song["title"] + " " + song["album"]
                                    if song["id"] not in song_ids:
                                        if (utils.compare_string_to_exclusion(song["title"], excluded_words)
                                            or utils.compare_string_to_exclusion(song["album"], excluded_words)):
                                            excluded = True
                                        elif (utils.compare_strings(artist_name_spotify, song["artist"])
                                            and utils.compare_strings(track['name'], song["title"])
                                            and placeholder not in track_helper):
                                            if (("album" in track and "name" in track["album"] and utils.compare_strings(track['album']['name'], song["album"]))
                                                or ("album" not in track) 
                                                or ("album" in track and "name" not in track["album"])):
                                                    song_ids.append(song["id"])
                                                    track_helper.append(placeholder)
                                                    found = True
                                                    database.insert_song(dbms, playlist_id, song, artist_spotify, track)
                                                    logging.info('Adding song %s - %s from album %s to playlist %s', song["artist"], song["title"], song["album"], playlist_name)
                                                    checkPysonicConnection().createPlaylist(playlistId = playlist_id, songIds = song_ids)
                                                    break
                                            else:
                                                skipped_songs.append(song)
                            if found is False and excluded is False and len(skipped_songs) > 0:
                                random.shuffle(skipped_songs)
                                for skipped_song in skipped_songs:
                                    placeholder = skipped_song["artist"] + " " + skipped_song['title'] + " " + skipped_song["album"]
                                    if placeholder not in track_helper:
                                        track_helper.append(placeholder)
                                        song_ids.append(skipped_song["id"])
                                        found = True
                                        database.insert_song(dbms, playlist_id, skipped_song, artist_spotify, track)
                                        logging.warning('No matching album found for Subsonic search "%s", using a random one', text_to_search)
                                        logging.info('Adding song %s - %s from album %s to playlist %s', skipped_song["artist"], song["title"], skipped_song["album"], playlist_name)
                                        checkPysonicConnection().createPlaylist(playlistId = playlist_id, songIds = song_ids)
                                        break
                    if not excluded:
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