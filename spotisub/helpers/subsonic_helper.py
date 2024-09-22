"""Subsonic helper"""
import logging
import os
import random
import time
import libsonic
from libsonic.errors import DataNotFoundError
from spotisub import spotisub
from spotisub import database
from spotisub import constants
from spotisub import utils
from spotisub.exceptions import SubsonicOfflineException
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
        subsonic_search = check_pysonic_connection().search2(set_search)
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
            track = sp.track(uri)
            time.sleep(1)
        elif "uri" not in track:
            track["uri"] = uri
        return track
    return None


def write_playlist(sp, playlist_name, results):
    """write playlist to subsonic db"""
    try:
        playlist_name = os.environ.get(
            constants.PLAYLIST_PREFIX,
            constants.PLAYLIST_PREFIX_DEFAULT_VALUE).replace(
            "\"",
            "") + playlist_name
        playlist_id = get_playlist_id_by_name(playlist_name)
        song_ids = []
        old_song_ids = []
        if playlist_id is None:
            check_pysonic_connection().createPlaylist(name=playlist_name, songIds=[])
            logging.info('Creating playlist %s', playlist_name)
            playlist_id = get_playlist_id_by_name(playlist_name)
            database.delete_playlist_relation_by_id(playlist_id)
        else:
            old_song_ids = get_playlist_songs_ids_by_id(playlist_id)

        track_helper = []
        for track in results['tracks']:
            track = add_missing_values_to_track(sp, track)
            found = False
            for artist_spotify in track['artists']:
                if found is False:
                    excluded = False
                    if artist_spotify != '' and "name" in artist_spotify:
                        logging.info(
                            'Searching %s - %s in your music library',
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
                                playlist_id,
                                old_song_ids,
                                playlist_name)

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
                                        'Track %s - %s not found in your music ' +
                                        'library, using SPOTDL downloader',
                                        artist_spotify["name"],
                                        track['name'])
                                    logging.warning(
                                        'This track will be available after ' +
                                        'navidrome rescans your music dir')
                                    spotdl_helper.download_track(
                                        track["external_urls"]["spotify"])
                                else:
                                    logging.warning(
                                        'Track %s - %s not found in your music library',
                                        artist_spotify["name"],
                                        track['name'])
                                    logging.warning(
                                        'This track hasn'
                                        't been found in your Lidarr database, ' +
                                        'skipping download process')
                        elif found is False:
                            logging.warning(
                                'Track %s - %s not found in your music library',
                                artist_spotify["name"],
                                track['name'])
                            database.insert_song(
                                playlist_id, None, artist_spotify, track)
        if playlist_id is not None:

            if len(song_ids) > 0:
                check_pysonic_connection().createPlaylist(
                    playlistId=playlist_id, songIds=song_ids)
                logging.info('Success! Created playlist %s', playlist_name)
            elif len(song_ids) == 0:
                try:
                    check_pysonic_connection().deletePlaylist(playlist_id)
                    logging.info(
                        'Fail! No songs found for playlist %s',
                        playlist_name)
                except DataNotFoundError:
                    pass

    except SubsonicOfflineException:
        logging.error(
            'There was an error creating a Playlist, perhaps is your Subsonic server offline?')


def match_with_subsonic_track(
        comparison_helper, playlist_id, old_song_ids, playlist_name):
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
                'Track with id "%s" already in playlist "%s"',
                song["id"],
                playlist_name)
            comparison_helper.song_ids.append(song["id"])
            comparison_helper.found = True
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
                'Comparing song "%s - %s - %s" with Spotify track "%s - %s - %s"',
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
                        playlist_id, song, comparison_helper.artist_spotify, comparison_helper.track)
                    logging.info(
                        'Adding song "%s - %s - %s" to playlist "%s", matched by ISRC: "%s"',
                        song["artist"],
                        song["title"],
                        song["album"],
                        playlist_name,
                        comparison_helper.track["external_ids"]["isrc"])
                    check_pysonic_connection().createPlaylist(
                        playlistId=playlist_id, songIds=comparison_helper.song_ids)
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
                        playlist_id, song, comparison_helper.artist_spotify, comparison_helper.track)
                    logging.info(
                        'Adding song "%s - %s - %s" to playlist "%s", matched by text comparison',
                        song["artist"],
                        song["title"],
                        song["album"],
                        playlist_name)
                    check_pysonic_connection().createPlaylist(
                        playlistId=playlist_id, songIds=comparison_helper.song_ids)
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
                    playlist_id, skipped_song, comparison_helper.artist_spotify, comparison_helper.track)
                logging.warning(
                    'No matching album found for Subsonic search "%s", using a random one',
                    text_to_search)
                logging.info(
                    'Adding song "%s - %s - %s" to playlist "%s", random match',
                    skipped_song["artist"],
                    song["title"],
                    skipped_song["album"],
                    playlist_name)
                check_pysonic_connection().createPlaylist(
                    playlistId=playlist_id, songIds=comparison_helper.song_ids)
    return comparison_helper


def get_playlist_songs(missing_only=False):
    """get list of playlists and songs"""
    playlist_songs_db = database.select_all_playlists(missing_only)
    playlist_songs = {}
    for key in playlist_songs_db:
        playlist_search = None
        try:
            playlist_search = check_pysonic_connection().getPlaylist(key)
        except SubsonicOfflineException as ex:
            raise ex
        except DataNotFoundError:
            pass
        if playlist_search is None:
            logging.warning(
                'Playlist id "%s" not found, may be you deleted this playlist from Subsonic?',
                key)
            logging.warning(
                'Deleting Playlist with id "%s" from spotisub database.', key)
            database.delete_playlist_relation_by_id(key)
        elif playlist_search is not None:
            missings = playlist_songs_db[key]
            for missing in missings:
                if ("subsonic_playlist_id" in missing
                        and missing["subsonic_playlist_id"] is not None):
                    if "playlist" in playlist_search:
                        single_playlist_search = playlist_search["playlist"]

                        found_error = False

                        try:
                            if ("subsonic_artist_id" in missing
                                    and missing["subsonic_artist_id"] is not None):
                                artist_search = check_pysonic_connection().getArtist(
                                    missing["subsonic_artist_id"])
                                if "artist" in artist_search:
                                    single_artist_search = artist_search["artist"]
                                    missing["subsonic_artist_name"] = single_artist_search["name"]
                            if ("subsonic_song_id" in missing
                                    and missing["subsonic_song_id"] is not None):
                                song_search = check_pysonic_connection().getSong(
                                    missing["subsonic_song_id"])
                                if "song" in song_search:
                                    single_song_search = song_search["song"]
                                    missing["subsonic_song_name"] = single_song_search["title"]
                            if single_playlist_search["name"] not in playlist_songs:
                                playlist_songs[single_playlist_search["name"]] = [
                                ]
                            playlist_songs[single_playlist_search["name"]].append(
                                missing)
                        except DataNotFoundError:
                            found_error = True
                            pass

                        if found_error:
                            logging.warning(
                                'Found a song inside Spotisub playlist %s ' +
                                'with an unmatched Subsonic entry. ' +
                                'Deleting this playlist.',
                                single_playlist_search["name"])
                            database.delete_playlist_relation_by_id(key)
                            if single_playlist_search["name"] in playlist_songs:
                                playlist_songs.pop(
                                    single_playlist_search["name"])

                            try:
                                check_pysonic_connection().deletePlaylist(key)
                            except DataNotFoundError:
                                pass
                            break

    return playlist_songs


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
            'Playlist id "%s" not found, may be you ' +
            'deleted this playlist from Subsonic?',
            key)
        logging.warning(
            'Deleting Playlist with id "%s" from spotisub database.', key)
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

    spotisub_playlists = database.select_all_playlists(False)
    for key in spotisub_playlists:
        playlist_search = None
        try:
            playlist_search = check_pysonic_connection().getPlaylist(key)
        except SubsonicOfflineException as ex:
            raise ex
        except DataNotFoundError:
            pass
        if playlist_search is None:
            logging.warning(
                'Playlist id "%s" not found, may be you ' +
                'deleted this playlist from Subsonic?',
                key)
            logging.warning(
                'Deleting Playlist with id "%s" from spotisub database.', key)
            database.delete_playlist_relation_by_id(key)

    # DO we really need to remove spotify songs even if they are not related to any playlist?
    # This can cause errors when an import process is running
    # I will just leave spotify songs saved in Spotisub database for now
