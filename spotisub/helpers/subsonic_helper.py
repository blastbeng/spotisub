"""Subsonic helper"""
import logging
import os
import random
import time
import threading
import libsonic
from expiringdict import ExpiringDict
from libsonic.errors import DataNotFoundError
from spotisub import spotisub
from spotisub import database
from spotisub import constants
from spotisub import utils
from spotisub.exceptions import SubsonicOfflineException
from spotisub.exceptions import SpotifyApiException
from spotisub.exceptions import SpotifyDataException
from spotisub.classes import ComparisonHelper
from spotisub.helpers import musicbrainz_helper


if os.environ.get(constants.SPOTDL_ENABLED,
                  constants.SPOTDL_ENABLED_DEFAULT_VALUE) == "1":
    from spotisub.helpers import spotdl_helper
    logging.warning(
        "You have enabled SPOTDL integration, " +
        "make sure to configure the correct download " +
        "path and check that you have enough disk space " +
        "for music downloading.")

if os.environ.get(constants.LIDARR_ENABLED,
                  constants.LIDARR_ENABLED_DEFAULT_VALUE) == "1":
    from spotisub.helpers import lidarr_helper
    logging.warning(
        "You have enabled LIDARR integration, " +
        "if an artist won't be found inside the " +
        "lidarr database, the download process will be skipped.")

pysonic = libsonic.Connection(
    os.environ.get(
        constants.SUBSONIC_API_HOST),
    os.environ.get(
        constants.SUBSONIC_API_USER),
    os.environ.get(
        constants.SUBSONIC_API_PASS),
    appName="Spotisub",
    serverPath=os.environ.get(
        constants.SUBSONIC_API_BASE_URL,
        constants.SUBSONIC_API_BASE_URL_DEFAULT_VALUE) +
    "/rest",
    port=int(
        os.environ.get(
            constants.SUBSONIC_API_PORT)))


# caches
playlist_cache = ExpiringDict(max_len=500, max_age_seconds=300)
spotify_playlist_cache = ExpiringDict(max_len=1000, max_age_seconds=3600)
spotify_artist_cache = ExpiringDict(max_len=1000, max_age_seconds=3600)
spotify_album_cache = ExpiringDict(max_len=1000, max_age_seconds=3600)
spotify_song_cache = ExpiringDict(max_len=1000, max_age_seconds=3600)


def get_spotify_artist_from_cache(sp, spotify_uri):
    spotify_artist = None
    if spotify_uri not in spotify_artist_cache:
        spotify_artist = sp.artist(spotify_uri)
        spotify_artist_cache[spotify_uri] = spotify_artist
    else:
        spotify_artist = spotify_artist_cache[spotify_uri]
    return spotify_artist

def get_spotify_playlist_from_cache(sp, spotify_uri):
    spotify_playlist = None
    if spotify_uri not in spotify_playlist_cache:
        spotify_playlist = sp.playlist(spotify_uri)
        spotify_playlist_cache[spotify_uri] = spotify_playlist
    else:
        spotify_playlist = spotify_playlist_cache[spotify_uri]
    return spotify_playlist

def get_spotify_album_from_cache(sp, spotify_uri):
    spotify_album = None
    if spotify_uri not in spotify_album_cache:
        spotify_album = sp.album(spotify_uri)
        spotify_album_cache[spotify_uri] = spotify_album
    else:
        spotify_album = spotify_album_cache[spotify_uri]
    return spotify_album

def get_spotify_song_from_cache(sp, spotify_uri):
    spotify_song = None
    if spotify_uri not in spotify_song_cache:
        spotify_song = sp.track(spotify_uri)
        spotify_song_cache[spotify_uri] = spotify_song
    else:
        spotify_song = spotify_song_cache[spotify_uri]
    return spotify_song

def check_pysonic_connection():
    """Return SubsonicOfflineException if pysonic is offline"""
    if pysonic.ping():
        return pysonic
    raise SubsonicOfflineException()


def get_artists_array_names():
    """get artists array names"""
    check_pysonic_connection().getArtists()

    artist_names = []

    for index in check_pysonic_connection().getArtists()["artists"]["index"]:
        for artist in index["artist"]:
            if "name" in artist:
                artist_names.append(artist["name"])

    return artist_names


def search_artist(artist_name):
    """search artist"""

    for index in check_pysonic_connection().getArtists()["artists"]["index"]:
        for artist in index["artist"]:
            if "name" in artist:
                if artist_name.strip().lower(
                ) == artist["name"].strip().lower():
                    return artist["name"]

    return None


def get_subsonic_search_results(text_to_search):
    """get subsonic search results"""
    result = {}
    set_searches = utils.generate_compare_array(text_to_search)
    for set_search in set_searches:
        subsonic_search = check_pysonic_connection().search2(set_search, songCount=500)
        if ("searchResult2" in subsonic_search
            and len(subsonic_search["searchResult2"]) > 0
                and "song" in subsonic_search["searchResult2"]):
            for song in subsonic_search["searchResult2"]["song"]:
                if "id" in song and song["id"] not in result:
                    result[song["id"]] = song
    return result


def get_playlist_id_by_name(playlist_name):
    """get playlist id by name"""
    playlist_id = None
    playlists_search = check_pysonic_connection().getPlaylists()
    if "playlists" in playlists_search and len(
            playlists_search["playlists"]) > 0:
        single_playlist_search = playlists_search["playlists"]
        if "playlist" in single_playlist_search and len(
                single_playlist_search["playlist"]) > 0:
            for playlist in single_playlist_search["playlist"]:
                if playlist["name"].strip() == playlist_name.strip():
                    playlist_id = playlist["id"]
                    break
    return playlist_id


def has_isrc(track):
    """check if spotify track has isrc"""
    if ("external_ids" not in track
        or track["external_ids"] is None
        or "isrc" not in track["external_ids"]
        or track["external_ids"]["isrc"] is None
            or track["external_ids"]["isrc"] == ""):
        return False
    return True


def add_missing_values_to_track(sp, track):
    """calls spotify if tracks has missing album or isrc or uri"""
    if "id" in track:
        uri = 'spotify:track:' + track['id']
        if "album" not in track or has_isrc(track) is False:
            track = get_spotify_song_from_cache(sp, uri)
            time.sleep(1)
        elif "uri" not in track:
            track["uri"] = uri
        return track
    return None


def write_playlist(sp, playlist_info, results):
    """write playlist to subsonic db"""
    try:
        playlist_info["name"] = (os.environ.get(
            constants.PLAYLIST_PREFIX,
            constants.PLAYLIST_PREFIX_DEFAULT_VALUE).replace(
            "\"",
            "") + playlist_info["name"])
        playlist_id = get_playlist_id_by_name(playlist_info["name"])
        song_ids = []
        old_song_ids = []
        if playlist_id is None:
            check_pysonic_connection().createPlaylist(name=playlist_info["name"], songIds=[])
            logging.info('(%s) Creating playlist %s', 
                str(threading.current_thread().ident), playlist_info["name"])
            playlist_id = get_playlist_id_by_name(playlist_info["name"])
            database.delete_playlist_relation_by_id(playlist_id)
        else:
            old_song_ids = get_playlist_songs_ids_by_id(playlist_id)

        if playlist_id is not None:

            playlist_info["subsonic_playlist_id"] = playlist_id
            track_helper = []
            for track in results['tracks']:
                track = add_missing_values_to_track(sp, track)
                found = False
                for artist_spotify in track['artists']:
                    if found is False:
                        excluded = False
                        if artist_spotify != '' and "name" in artist_spotify:
                            logging.info(
                                '(%s) Searching %s - %s in your music library', 
                                str(threading.current_thread().ident),
                                artist_spotify["name"],
                                track['name'])
                            if "name" in track:
                                comparison_helper = ComparisonHelper(track,
                                                                    artist_spotify,
                                                                    found,
                                                                    excluded,
                                                                    song_ids,
                                                                    track_helper)
                                comparison_helper = match_with_subsonic_track(
                                    comparison_helper,
                                    playlist_info,
                                    old_song_ids)

                                track = comparison_helper.track
                                artist_spotify = comparison_helper.artist_spotify
                                found = comparison_helper.found
                                excluded = comparison_helper.excluded
                                song_ids = comparison_helper.song_ids
                                track_helper = comparison_helper.track_helper
                        if not excluded:
                            if (os.environ.get(constants.SPOTDL_ENABLED,
                                            constants.SPOTDL_ENABLED_DEFAULT_VALUE) == "1"
                                    and found is False):
                                if "external_urls" in track and "spotify" in track["external_urls"]:
                                    is_monitored = True
                                    if (os.environ.get(constants.LIDARR_ENABLED,
                                                    constants.LIDARR_ENABLED_DEFAULT_VALUE) == "1"):
                                        is_monitored = lidarr_helper.is_artist_monitored(
                                            artist_spotify["name"])
                                    if is_monitored:
                                        logging.warning(
                                            '(%s) Track %s - %s not found in your music ' +
                                            'library, using SPOTDL downloader', 
                                            str(threading.current_thread().ident),
                                            artist_spotify["name"],
                                            track['name'])
                                        logging.warning(
                                            '(%s) This track will be available after ' +
                                            'navidrome rescans your music dir', 
                                            str(threading.current_thread().ident))
                                        spotdl_helper.download_track(
                                            track["external_urls"]["spotify"])
                                    else:
                                        logging.warning(
                                            '(%s) Track %s - %s not found in your music library', 
                                            str(threading.current_thread().ident),
                                            artist_spotify["name"],
                                            track['name'])
                                        logging.warning(
                                            '(%s) This track hasn'
                                            't been found in your Lidarr database, ' +
                                            'skipping download process', 
                                            str(threading.current_thread().ident))
                            elif found is False:
                                logging.warning(
                                    '(%s) Track %s - %s not found in your music library', 
                                    str(threading.current_thread().ident),
                                    artist_spotify["name"],
                                    track['name'])
                                database.insert_song(
                                    playlist_info, None, artist_spotify, track)

            if len(song_ids) > 0:
                check_pysonic_connection().createPlaylist(
                    playlistId=playlist_info["subsonic_playlist_id"], songIds=song_ids)
                logging.info('(%s) Success! Created playlist %s', 
                    str(threading.current_thread().ident), playlist_info["name"])
            elif len(song_ids) == 0:
                try:
                    check_pysonic_connection().deletePlaylist(playlist_info["subsonic_playlist_id"])
                    logging.info(
                        '(%s) Fail! No songs found for playlist %s',
                        str(threading.current_thread().ident), playlist_info["name"])
                except DataNotFoundError:
                    pass

    except SubsonicOfflineException:
        logging.error(
            '(%s) There was an error creating a Playlist, perhaps is your Subsonic server offline?',
            str(threading.current_thread().ident))


def match_with_subsonic_track(
        comparison_helper, playlist_info, old_song_ids):
    """compare spotify track to subsonic one"""
    text_to_search = comparison_helper.artist_spotify["name"] + \
        " " + comparison_helper.track['name']
    subsonic_search_results = get_subsonic_search_results(text_to_search)
    skipped_songs = []
    for song_id in subsonic_search_results:
        song = subsonic_search_results[song_id]
        song["isrc-list"] = musicbrainz_helper.get_isrc_by_id(song)
        placeholder = song["artist"] + " " + \
            song["title"] + " " + song["album"]
        if song["id"] in old_song_ids:
            logging.info(
                '(%s) Track with id "%s" already in playlist "%s"',
                str(threading.current_thread().ident),
                song["id"],
                playlist_info["name"])
            comparison_helper.song_ids.append(song["id"])
            comparison_helper.found = True
            database.insert_song(
                playlist_info, song, comparison_helper.artist_spotify, comparison_helper.track)
        elif (song["id"] not in comparison_helper.song_ids
              and song["artist"] != ''
              and comparison_helper.track['name'] != ''
              and song["album"] != ''
              and song["title"] != ''):
            album_name = ""
            if ("album" in comparison_helper.track
                and "name" in comparison_helper.track["album"]
                    and comparison_helper.track["album"]["name"] is not None):
                album_name = comparison_helper.track["album"]["name"]
            logging.info(
                '(%s) Comparing song "%s - %s - %s" with Spotify track "%s - %s - %s"',
                str(threading.current_thread().ident),
                song["artist"],
                song["title"],
                song["album"],
                comparison_helper.artist_spotify["name"],
                comparison_helper.track['name'],
                album_name)
            if has_isrc(comparison_helper.track):
                found_isrc = False
                for isrc in song["isrc-list"]:
                    if isrc.strip(
                    ) == comparison_helper.track["external_ids"]["isrc"].strip():
                        found_isrc = True
                        break
                if found_isrc is True:
                    comparison_helper.song_ids.append(song["id"])
                    comparison_helper.track_helper.append(placeholder)
                    comparison_helper.found = True
                    database.insert_song(
                        playlist_info, song, comparison_helper.artist_spotify, comparison_helper.track)
                    logging.info(
                        '(%s) Adding song "%s - %s - %s" to playlist "%s", matched by ISRC: "%s"',
                        str(threading.current_thread().ident),
                        song["artist"],
                        song["title"],
                        song["album"],
                        playlist_info["name"],
                        comparison_helper.track["external_ids"]["isrc"])
                    check_pysonic_connection().createPlaylist(
                        playlistId=playlist_info["subsonic_playlist_id"], songIds=comparison_helper.song_ids)
                    break
            if (utils.compare_string_to_exclusion(song["title"],
                utils.get_excluded_words_array())
                or utils.compare_string_to_exclusion(song["album"],
                                                     utils.get_excluded_words_array())):
                comparison_helper.excluded = True
            elif (utils.compare_strings(comparison_helper.artist_spotify["name"], song["artist"])
                  and utils.compare_strings(comparison_helper.track['name'], song["title"])
                  and placeholder not in comparison_helper.track_helper):
                if (("album" in comparison_helper.track and "name" in comparison_helper.track["album"]
                    and utils.compare_strings(comparison_helper.track['album']['name'], song["album"]))
                    or ("album" not in comparison_helper.track)
                        or ("album" in comparison_helper.track and "name" not in comparison_helper.track["album"])):
                    comparison_helper.song_ids.append(song["id"])
                    comparison_helper.track_helper.append(placeholder)
                    comparison_helper.found = True
                    database.insert_song(
                        playlist_info, song, comparison_helper.artist_spotify, comparison_helper.track)
                    logging.info(
                        '(%s) Adding song "%s - %s - %s" to playlist "%s", matched by text comparison',
                        str(threading.current_thread().ident),
                        song["artist"],
                        song["title"],
                        song["album"],
                        playlist_info["name"])
                    check_pysonic_connection().createPlaylist(
                        playlistId=playlist_info["subsonic_playlist_id"], songIds=comparison_helper.song_ids)
                    break
                skipped_songs.append(song)
    if comparison_helper.found is False and comparison_helper.excluded is False and len(
            skipped_songs) > 0:
        random.shuffle(skipped_songs)
        for skipped_song in skipped_songs:
            placeholder = skipped_song["artist"] + " " + \
                skipped_song['title'] + " " + skipped_song["album"]
            if placeholder not in comparison_helper.track_helper:
                comparison_helper.track_helper.append(placeholder)
                comparison_helper.song_ids.append(skipped_song["id"])
                comparison_helper.found = True
                database.insert_song(
                    playlist_info, skipped_song, comparison_helper.artist_spotify, comparison_helper.track)
                logging.warning(
                    '(%s) No matching album found for Subsonic search "%s", using a random one',
                    str(threading.current_thread().ident),
                    text_to_search)
                logging.info(
                    '(%s) Adding song "%s - %s - %s" to playlist "%s", random match',
                    str(threading.current_thread().ident),
                    skipped_song["artist"],
                    song["title"],
                    skipped_song["album"],
                    playlist_info["name"])
                check_pysonic_connection().createPlaylist(
                    playlistId=playlist_info["subsonic_playlist_id"], songIds=comparison_helper.song_ids)
    return comparison_helper


def select_all_songs(missing_only=False, page=None,
                         limit=None, order=None, asc=None, search=None):
    """get list of playlists and songs"""
    try:
        playlist_songs, count = database.select_all_songs(
            missing_only=missing_only,
            page=page,
            limit=limit,
            order=order,
            asc=asc,
            search=search)


        has_been_deleted = False

        ids=[]
        for playlist in playlist_songs:
           if playlist.subsonic_playlist_id not in ids:
                ids.append(playlist.subsonic_playlist_id)

        for plid in ids:
            playlist_search, has_been_deleted = get_playlist_from_cache(plid)

        if has_been_deleted:
            return select_all_songs(
                missing_only=missing_only,
                page=page,
                limit=limit,
                order=order,
                asc=asc,
                search=search)
        return playlist_songs, count
    except SubsonicOfflineException as ex:
        raise ex


def select_all_playlists(spotipy_helper, page=None,
                         limit=None, order=None, asc=None):
    """get list of playlists"""
    try:
        all_playlists, count = database.select_all_playlists(
            page=page,
            limit=limit,
            order=order,
            asc=asc)

        has_been_deleted = False

        songs = []

        ids = []
        for playlist in all_playlists:
            if playlist["subsonic_playlist_id"] not in ids:
                ids.append(playlist["subsonic_playlist_id"])
            if playlist["type"] == constants.JOB_ATT_ID or playlist["type"] == constants.JOB_AR_ID:
                spotify_artist = get_spotify_artist_from_cache(spotipy_helper.get_spotipy_client(), playlist["spotify_playlist_uri"])
                if "images" in spotify_artist and len(spotify_artist["images"]) > 0:
                    playlist["image"] = spotify_artist["images"][0]["url"]
            elif playlist["type"] == constants.JOB_UP_ID:
                spotify_playlist = get_spotify_playlist_from_cache(spotipy_helper.get_spotipy_client(), playlist["spotify_playlist_uri"])
                if "images" in spotify_playlist and len(spotify_playlist["images"]) > 0:
                    playlist["image"] = spotify_playlist["images"][0]["url"]
            else:
                playlist["image"] = ""
            prefix = os.environ.get(
                        constants.PLAYLIST_PREFIX,
                        constants.PLAYLIST_PREFIX_DEFAULT_VALUE).replace(
                        "\"",
                        "")
            playlist["subsonic_playlist_name"] = playlist["subsonic_playlist_name"].replace(prefix,"")

        for plid in ids:
            playlist_search, has_been_deleted = get_playlist_from_cache(
                plid)

        if has_been_deleted:
            return select_all_playlists(spotipy_helper, page=None,
                limit=None, order=None, asc=None)
        return all_playlists, count
    except SubsonicOfflineException as ex:
        raise ex


def get_playlist_from_cache(key):
    has_been_deleted = False
    if key not in playlist_cache:
        try:
            playlist_search = check_pysonic_connection().getPlaylist(key)
            playlist_cache[key] = playlist_search["playlist"]["name"]
        except DataNotFoundError:
            pass

    if key not in playlist_cache:
        logging.warning(
            '(%s) Playlist id "%s" not found, may be you deleted this playlist from Subsonic?',
            str(threading.current_thread().ident), key)
        logging.warning(
            '(%s) Deleting Playlist with id "%s" from spotisub database.',
            str(threading.current_thread().ident), key)
        database.delete_playlist_relation_by_id(key)
        has_been_deleted = True
        return None, has_been_deleted
    return playlist_cache[key], has_been_deleted

    


def get_playlist_songs_ids_by_id(key):
    """get playlist songs ids by id"""
    songs = []
    playlist_search = None
    try:
        playlist_search = check_pysonic_connection().getPlaylist(key)
    except SubsonicOfflineException as ex:
        raise ex
    except DataNotFoundError:
        pass
    if playlist_search is None:
        logging.warning(
            '(%s) Playlist id "%s" not found, may be you ' +
            'deleted this playlist from Subsonic?',
            str(threading.current_thread().ident), key)
        logging.warning(
            '(%s) Deleting Playlist with id "%s" from spotisub database.',
            str(threading.current_thread().ident), key)
        database.delete_playlist_relation_by_id(key)
    elif (playlist_search is not None
            and "playlist" in playlist_search
            and "entry" in playlist_search["playlist"]
            and len(playlist_search["playlist"]["entry"]) > 0):
        songs = playlist_search["playlist"]["entry"]
        for entry in playlist_search["playlist"]["entry"]:
            if "id" in entry and entry["id"] is not None and entry["id"].strip(
            ) != "":
                songs.append(entry["id"])

    return songs


def remove_subsonic_deleted_playlist():
    """fix user manually deleted playlists"""

    spotisub_playlists, count = database.select_all_playlists()
    spotisub_songs, count = database.select_all_songs()

    ids = []
    
    for row1 in spotisub_playlists:
        if row1["subsonic_playlist_id"] not in ids:
            ids.append(row1["subsonic_playlist_id"])

    for row2 in spotisub_songs:
        if row2.subsonic_playlist_id not in ids:
            ids.append(row2.subsonic_playlist_id)

    for key in ids:
        playlist_search = None
        try:
            playlist_search = check_pysonic_connection().getPlaylist(key)
        except SubsonicOfflineException as ex:
            raise ex
        except DataNotFoundError:
            pass
        if playlist_search is None:
            logging.warning(
                '(%s) Playlist id "%s" not found, may be you ' +
                'deleted this playlist from Subsonic?',
                str(threading.current_thread().ident), key)
            logging.warning(
                '(%s) Deleting Playlist with id "%s" from spotisub database.', 
                str(threading.current_thread().ident), key)
            database.delete_playlist_relation_by_id(key)

    # DO we really need to remove spotify songs even if they are not related to any playlist?
    # This can cause errors when an import process is running
    # I will just leave spotify songs saved in Spotisub database for now

def load_artist(uuid, spotipy_helper, page=None,
                limit=None, order=None, asc=None):
    artist_db, songs, count = database.get_artist_and_songs(
        uuid, page=page, limit=limit, order=order, asc=asc)
    sp = None

    spotify_artist = get_spotify_artist_from_cache(spotipy_helper.get_spotipy_client(), artist_db.spotify_uri)

    if spotify_artist is None:
        raise SpotifyDataException
    artist = {}
    artist["name"] = artist_db.name
    artist["genres"] = ""
    artist["url"] = ""
    artist["image"] = ""
    artist["popularity"] = ""
    if "genres" in spotify_artist:
        artist["genres"] = ", ".join(spotify_artist["genres"])
    if "popularity" in spotify_artist:
        artist["popularity"] = str(spotify_artist["popularity"]) + "%"
    if "external_urls" in spotify_artist and "spotify" in spotify_artist["external_urls"]:
        artist["url"] = spotify_artist["external_urls"]["spotify"]
    if "images" in spotify_artist and len(spotify_artist["images"]) > 0:
        artist["image"] = spotify_artist["images"][0]["url"]
    return artist, songs, count


def load_album(uuid, spotipy_helper, page=None,
               limit=None, order=None, asc=None):
    album_db, songs, count = database.get_album_and_songs(
        uuid, page=page, limit=limit, order=order, asc=asc)
    sp = None

    spotify_album = get_spotify_album_from_cache(spotipy_helper.get_spotipy_client(), album_db.spotify_uri)

    if spotify_album is None:
        raise SpotifyDataException
    album = {}
    album["name"] = album_db.name
    album["url"] = ""
    album["image"] = ""
    album["release_date"] = ""
    if "release_date" in spotify_album:
        album["release_date"] = spotify_album["release_date"]
    if "external_urls" in spotify_album and "spotify" in spotify_album["external_urls"]:
        album["url"] = spotify_album["external_urls"]["spotify"]
    if "images" in spotify_album and len(spotify_album["images"]) > 0:
        album["image"] = spotify_album["images"][0]["url"]

    return album, songs, count


def load_song(uuid, spotipy_helper, page=None,
               limit=None, order=None, asc=None):
    song_db, songs, count = database.get_song_and_playlists(
        uuid, page=page, limit=limit, order=order, asc=asc)
    sp = None

    spotify_song = get_spotify_song_from_cache(spotipy_helper.get_spotipy_client(), song_db.spotify_uri)

    if spotify_song is None:
        raise SpotifyDataException

    song = {}
    song["name"] = song_db.title
    song["url"] = ""
    song["image"] = ""
    song["popularity"] = ""
    song["preview"] = ""
    
    if "preview_url" in spotify_song:
        song["preview_url"] = spotify_song["preview_url"]
    if "popularity" in spotify_song:
        song["popularity"] = str(spotify_song["popularity"]) + "%"
    if "external_urls" in spotify_song and "spotify" in spotify_song["external_urls"]:
        song["url"] = spotify_song["external_urls"]["spotify"]

    if len(songs) > 0:
        spotify_album = None
        if songs[0].spotify_album_uri not in spotify_album_cache:
            spotify_album = get_spotify_album_from_cache(spotipy_helper.get_spotipy_client(), songs[0].spotify_album_uri)

            if spotify_album is None:
                raise SpotifyDataException
        
        if "images" in spotify_album and len(spotify_album["images"]) > 0:
            song["image"] = spotify_album["images"][0]["url"]

    return song, songs, count