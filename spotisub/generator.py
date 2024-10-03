"""Subsonic generator"""
import logging
import os
import random
import time
import re
import threading
from flask_apscheduler import APScheduler
from spotisub import spotisub
from spotisub import constants
from spotisub import database
from spotisub.helpers import spotipy_helper
from spotisub.helpers import subsonic_helper


scheduler = APScheduler()


def prechecks():
    spotipy_helper.get_secrets()
    subsonic_helper.check_pysonic_connection()


def artist_top_tracks(name, init=False):
    """artist top tracks"""
    sp = spotipy_helper.get_spotipy_client()
    artist = get_artist(name)
    if artist is not None:
        playlist_name = name + " - Top Tracks"
        playlist_info = {}
        playlist_info["name"] = playlist_name
        playlist_info["spotify_uri"] = artist["uri"]
        playlist_info["type"] = constants.JOB_ATT_ID
        if init:
            return subsonic_helper.generate_playlist(playlist_info)
        else:
            logging.info('(%s) Searching top tracks for for: %s',
                str(threading.current_thread().ident), artist_name)
            artist_top = sp.artist_top_tracks(artists_uri[artist_name])
            subsonic_helper.write_playlist(sp, playlist_info, artist_top)

def init_my_reccomendations():
    for i in range(int(os.environ.get(constants.NUM_USER_PLAYLISTS,
                   constants.NUM_USER_PLAYLISTS_DEFAULT_VALUE))):
        playlist_name = "My Recommendations " + str(i + 1)
        playlist_info = {}
        playlist_info["name"] = playlist_name
        playlist_info["spotify_uri"] = None
        playlist_info["type"] = constants.JOB_MR_ID
        playlist_info = subsonic_helper.generate_playlist(playlist_info)
        if playlist_info is not None and os.environ.get(constants.RECOMEND_GEN_SCHED, constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE) != "0":
            old_job = scheduler.get_job(playlist_info.uuid)
            if old_job == None:
                scheduler.add_job(
                    func=my_recommendations,
                    trigger="interval",
                    args=[i],
                    hours=int(os.environ.get(constants.RECOMEND_GEN_SCHED, constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE)),
                    id=playlist_info.uuid,
                    replace_existing=True,
                    max_instances=1
                )

def my_recommendations(playlist_num):
    """my recommendations"""
    sp = spotipy_helper.get_spotipy_client()
    top_tracks = None
    liked_tracks = None
    history = None
    top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term')
    logging.info('(%s) Loaded your custom top tracks',
            str(threading.current_thread().ident))
    time.sleep(2)
    liked_tracks = sp.current_user_saved_tracks(limit=50)
    logging.info('(%s) Loaded your top liked tracks',
                str(threading.current_thread().ident))
    time.sleep(2)
    history = sp.current_user_recently_played(limit=50)
    logging.info('(%s) Loaded your played tracks',
                str(threading.current_thread().ident))
    time.sleep(2)
    logging.info(
                '(%s) Searching your recommendations (playlist %s)',
                    str(threading.current_thread().ident), str(
                    playlist_num + 1))
    top_track_ids = [track['id'] for track in top_tracks['items']]
    liked_track_ids = [track['track']['id']
                            for track in liked_tracks['items']]
    history_track_ids = [track['track']['id']
                                for track in history['items']]
    seed_track_ids = top_track_ids + liked_track_ids + history_track_ids
    random.shuffle(seed_track_ids)
    results = sp.recommendations(seed_tracks=seed_track_ids[0:5], limit=int(
                os.environ.get(constants.ITEMS_PER_PLAYLIST, constants.ITEMS_PER_PLAYLIST_DEFAULT_VALUE)))
    playlist_name = "My Recommendations " + str(playlist_num + 1)
    playlist_info = {}
    playlist_info["name"] = playlist_name
    playlist_info["spotify_uri"] = None
    playlist_info["type"] = constants.JOB_MR_ID
    subsonic_helper.write_playlist(
                sp, playlist_info, results)


def get_artist(name):
    """get artist"""
    sp = spotipy_helper.get_spotipy_client()
    results = sp.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        return items[0]
    return None


def show_recommendations_for_artist(name, init=False):
    """show recommendations for artist"""
    sp = spotipy_helper.get_spotipy_client()
    artist = get_artist(name)
    if artist is not None:
        playlist_name = name + " - Recommendations"
        playlist_info = {}
        playlist_info["name"] = playlist_name
        playlist_info["spotify_uri"] = artist["uri"]
        playlist_info["type"] = constants.JOB_AR_ID
        if init:
            return subsonic_helper.generate_playlist(playlist_info)
        else:
            logging.info('(%s) Searching recommendations for: %s',
                str(threading.current_thread().ident), name)
            results = sp.recommendations(
                seed_artists=[
                    artist['id']],
                limit=int(
                    os.environ.get(
                        constants.ITEMS_PER_PLAYLIST,
                        constants.ITEMS_PER_PLAYLIST_DEFAULT_VALUE)))
            subsonic_helper.write_playlist(sp, playlist_info, results)
    else:
        logging.warning('(%s) Artist: %s Not found!',
            str(threading.current_thread().ident), name)


def get_playlist_tracks(item, result, offset_tracks=0):
    """get playlist tracks"""
    sp = spotipy_helper.get_spotipy_client()
    response_tracks = sp.playlist_items(item['id'],
                                        offset=offset_tracks,
                                        fields='items.track.id,items.track.name,items.track.artists,total',
                                        limit=50,
                                        additional_types=['track'])
    for track_item in response_tracks['items']:
        track = track_item['track']
        logging.info(
            '(%s) Found %s - %s inside playlist %s',
            str(threading.current_thread().ident),
            track['artists'][0]['name'],
            track['name'],
            item['name'])
        if track is not None:
            result["tracks"].append(track)
    time.sleep(2)
    if len(response_tracks['items']) != 0:
        result = get_playlist_tracks(
            item, result, offset_tracks=offset_tracks + 50)
    return result


def get_user_playlist_by_name(playlist_name, offset=0):
    """get user playlist by name"""
    sp = spotipy_helper.get_spotipy_client()
    playlist_result = sp.current_user_playlists(limit=50, offset=offset)

    name_found = None

    for item in playlist_result['items']:
        if (item['name'] is not None and item['name'].strip() != ''
            and (playlist_name is None
            or (playlist_name is not None
                and item['name'].lower().strip() == playlist_name.lower().strip()))):
            name_found = item['name'].strip()
    if name_found is None and len(playlist_result['items']) != 0:
        name_found = get_user_playlist_by_name(
            playlist_name, offset=offset + 50)
    return name_found


def get_user_playlists(playlist_name, offset=0, single_execution=False, init=False):
    """get user playlists"""
    sp = spotipy_helper.get_spotipy_client()

    playlist_result = sp.current_user_playlists(
        limit=(50 if single_execution is False else 1), offset=offset)

    for item in playlist_result['items']:
        if item['name'] is not None and item['name'].strip() != '' and (playlist_name is None or (
                playlist_name is not None and item['name'].lower().strip() == playlist_name.lower().strip())):
            playlist_info = {}
            playlist_info["name"] = item['name'].strip()
            playlist_info["spotify_uri"] = item["uri"]
            playlist_info["type"] = constants.JOB_UP_ID
            if init:
                playlist_info = subsonic_helper.generate_playlist(playlist_info)
                if playlist_info is not None and os.environ.get(constants.PLAYLIST_GEN_SCHED, constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE) != "0":
                    old_job = scheduler.get_job(playlist_info.uuid)
                    if old_job == None:
                        scheduler.add_job(
                            func=get_user_playlists,
                            trigger="interval",
                            args=[playlist_name],
                            hours=int(os.environ.get(constants.PLAYLIST_GEN_SCHED, constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE)),
                            id=playlist_info.uuid,
                            replace_existing=True,
                            max_instances=1
                        )
            else:
                logging.info('(%s) Importing playlist: %s',
                    str(threading.current_thread().ident), item['name'])
                result = dict({'tracks': []})
                result = get_playlist_tracks(item, result)
                subsonic_helper.write_playlist(sp, playlist_info, result)
            if single_execution:
                break

    if not single_execution and len(playlist_result['items']) != 0:
        get_user_playlists(offset=offset + 50, playlist_name=None, init=init)


def count_user_playlists(count, offset=0):
    """count user playlists"""
    sp = spotipy_helper.get_spotipy_client()
    playlist_result = sp.current_user_playlists(limit=50, offset=offset)
    count = count + len(playlist_result['items'])

    if len(playlist_result['items']) != 0:
        count = count_user_playlists(count, offset=offset + 50)
    return count


def all_artists_recommendations(artist_names):
    """all artists recommendations"""
    if len(artist_names) > 0:
        random.shuffle(artist_names)
        for artist_name in artist_names:
            playlist_info = show_recommendations_for_artist(artist_name, init=True)
            if playlist_info is not None and os.environ.get(constants.ARTIST_GEN_SCHED, constants.ARTIST_GEN_SCHED_DEFAULT_VALUE) != "0":
                old_job = scheduler.get_job(playlist_info.uuid)
                if old_job == None:
                    scheduler.add_job(
                        func=show_recommendations_for_artist,
                        trigger="interval",
                        args=[artist_name],
                        hours=int(os.environ.get(constants.ARTIST_GEN_SCHED, constants.ARTIST_GEN_SCHED_DEFAULT_VALUE)),
                        id=playlist_info.uuid,
                        replace_existing=True,
                        max_instances=1
                    )


def all_artists_top_tracks(artist_names, schedler=None):
    """all artists top tracks"""
    if len(artist_names) > 0:
        random.shuffle(artist_names)
        for artist_name in artist_names:
            playlist_info = artist_top_tracks(artist_name, init=True)
            if os.environ.get(constants.ARTIST_TOP_GEN_SCHED, constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE) != "0":
                old_job = scheduler.get_job(playlist_info.uuid)
                if old_job == None:
                    scheduler.add_job(
                        func=show_recommendations_for_artist,
                        trigger="interval",
                        args=[artist_name],
                        hours=int(os.environ.get(constants.ARTIST_TOP_GEN_SCHED, constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE)),
                        id=playlist_info.uuid,
                        replace_existing=True,
                        max_instances=1
                    )


def get_user_saved_tracks(result, init=True):
    """get user saved tracks"""
    playlist_info = {}
    playlist_info["name"] = "Saved Tracks"
    playlist_info["spotify_uri"] = None
    playlist_info["type"] = constants.JOB_ST_ID
    if init:
        playlist_info = subsonic_helper.generate_playlist(playlist_info)
        if playlist_info is not None and os.environ.get(constants.SAVED_GEN_SCHED, constants.SAVED_GEN_SCHED_DEFAULT_VALUE) != "0":
            old_job = scheduler.get_job(playlist_info.uuid)
            if old_job == None:
                scheduler.add_job(
                    func=get_user_saved_tracks,
                    trigger="interval",
                    args=[dict({'tracks': []})],
                    hours=int(os.environ.get(constants.SAVED_GEN_SCHED, constants.SAVED_GEN_SCHED_DEFAULT_VALUE)),
                    id=playlist_info.uuid,
                    replace_existing=True,
                    max_instances=1
                )
    else:
        sp = spotipy_helper.get_spotipy_client()
        result = get_user_saved_tracks_playlist(result)
        subsonic_helper.write_playlist(sp, playlist_info, result)


def get_user_saved_tracks_playlist(result, offset_tracks=0):
    """get user saved tracks playlist"""
    sp = spotipy_helper.get_spotipy_client()
    response_tracks = sp.current_user_saved_tracks(
        offset=offset_tracks,
        limit=50)
    for track_item in response_tracks['items']:
        if "track" in track_item:
            track = track_item['track']
            if track is not None:
                logging.info(
                    '(%s) Found %s - %s inside your saved tracks',
                    str(threading.current_thread().ident),
                    track['artists'][0]['name'],
                    track['name'])
                if track is not None:
                    result["tracks"].append(track)
    time.sleep(2)
    if len(response_tracks['items']) != 0:
        result = get_user_saved_tracks_playlist(
            result, offset_tracks=offset_tracks + 50)
    return result

def scan_library(init):
    """Used to scan the spotify library"""
    old_job = scheduler.get_job(id="scan_library_task")
    if init:
        scheduler.modify_job(
            func=scan_library,
            trigger="interval",
            hours=24,
            args=[False],
            id="scan_library_task",
            max_instances=1
        )
    #get_user_saved_tracks(None, init=True)
    init_my_reccomendations()
    #artist_names = subsonic_helper.get_artists_array_names()
    #all_artists_recommendations(artist_names)
    #all_artists_top_tracks(artist_names)
    #get_user_playlists(None, init=True)


scheduler.add_job(
    func=subsonic_helper.remove_subsonic_deleted_playlist,
    trigger="interval",
    hours=12,
    id="remove_deleted_playlists",
    replace_existing=True,
    max_instances=1
)

scheduler.add_job(
    func=scan_library,
    trigger="interval",
    seconds=10,
    args=[True],
    id="scan_library_task",
    replace_existing=True,
    max_instances=1
)

scheduler.init_app(spotisub)
scheduler.start(paused=(os.environ.get(constants.SCHEDULER_ENABLED,
                                       constants.SCHEDULER_ENABLED_DEFAULT_VALUE) != "1"))

try:
    subsonic_helper.select_all_playlists(spotipy_helper, page=0, limit=100, order='playlist_info.subsonic_playlist_name', asc=True)
except:
    pass