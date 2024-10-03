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


def artist_top_tracks(name):
    """artist top tracks"""
    sp = spotipy_helper.get_spotipy_client()
    artist = get_artist(name)
    if artist is not None:
        playlist_name = name + " - Top Tracks"
        playlist_info = {}
        playlist_info["name"] = playlist_name
        playlist_info["spotify_uri"] = artist["uri"]
        playlist_info["type"] = constants.JOB_ATT_ID
        logging.info('(%s) Searching top tracks for for: %s',
                str(threading.current_thread().ident), artist_name)
        artist_top = sp.artist_top_tracks(artists_uri[artist_name])
        subsonic_helper.write_playlist(sp, playlist_info, artist_top)

        if os.environ.get(constants.ARTIST_GEN_SCHED, constants.ARTIST_GEN_SCHED_DEFAULT_VALUE) == "0":
            scheduler.remove_job(id=constants.JOB_ATT_ID)
        else:
            artist_names = subsonic_helper.get_artists_array_names()
            if len(artist_names) > 0 and os.environ.get(constants.ARTIST_TOP_GEN_SCHED, constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE) != "0":
                artist_name = random.choice(artist_names)
                scheduler.modify_job(
                        args=[artist_name],
                        hours=int(os.environ.get(constants.ARTIST_TOP_GEN_SCHED, constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE)),
                        id=constants.JOB_ATT_ID
                )
            else:
                scheduler.remove_job(id=constants.JOB_ATT_ID)

def init_my_reccomendations():
    i = random.randrange(int(os.environ.get(constants.NUM_USER_PLAYLISTS,
                   constants.NUM_USER_PLAYLISTS_DEFAULT_VALUE)))
    if os.environ.get(constants.RECOMEND_GEN_SCHED, constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE) != "0":
        old_job = scheduler.get_job(constants.JOB_MR_ID)
        if old_job is None:
            scheduler.add_job(
                func=my_recommendations,
                trigger="interval",
                args=[i],
                hours=int(os.environ.get(constants.RECOMEND_GEN_SCHED, constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE)),
                id=constants.JOB_MR_ID,
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
    
    i = random.randrange(int(os.environ.get(constants.NUM_USER_PLAYLISTS,
                   constants.NUM_USER_PLAYLISTS_DEFAULT_VALUE)))
    scheduler.modify_job(
                args=[i],
                hours=int(os.environ.get(constants.RECOMEND_GEN_SCHED, constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE)),
                id=constants.JOB_MR_ID
            )


def get_artist(name):
    """get artist"""
    sp = spotipy_helper.get_spotipy_client()
    results = sp.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        return items[0]
    return None


def show_recommendations_for_artist(name):
    """show recommendations for artist"""
    sp = spotipy_helper.get_spotipy_client()
    artist = get_artist(name)
    if artist is not None:
        playlist_name = name + " - Recommendations"
        playlist_info = {}
        playlist_info["name"] = playlist_name
        playlist_info["spotify_uri"] = artist["uri"]
        playlist_info["type"] = constants.JOB_AR_ID
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

        if os.environ.get(constants.ARTIST_GEN_SCHED, constants.ARTIST_GEN_SCHED_DEFAULT_VALUE) == "0":
            scheduler.remove_job(id=constants.JOB_AR_ID)
        else:
            artist_names = subsonic_helper.get_artists_array_names()
            if len(artist_names) > 0:
                artist_name = random.choice(artist_names)
                scheduler.modify_job(
                                args=[artist_name],
                                hours=int(os.environ.get(constants.ARTIST_GEN_SCHED, constants.ARTIST_GEN_SCHED_DEFAULT_VALUE)),
                                id=constants.JOB_AR_ID
                            )
            else:
                scheduler.remove_job(id=constants.JOB_AR_ID)
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


def get_user_playlists(playlist_name, offset=0):
    """get user playlists"""
    sp = spotipy_helper.get_spotipy_client()

    playlist_result = sp.current_user_playlists(
        limit=50, offset=offset)

    for item in playlist_result['items']:
        if item['name'] is not None and item['name'].strip() != '' and (playlist_name is None or (
                playlist_name is not None and item['name'].lower().strip() == playlist_name.lower().strip())):
            playlist_info = {}
            playlist_info["name"] = item['name'].strip()
            playlist_info["spotify_uri"] = item["uri"]
            playlist_info["type"] = constants.JOB_UP_ID
            logging.info('(%s) Importing playlist: %s',
                str(threading.current_thread().ident), item['name'])
            result = dict({'tracks': []})
            result = get_playlist_tracks(item, result)
            subsonic_helper.write_playlist(sp, playlist_info, result)

            if os.environ.get(constants.PLAYLIST_GEN_SCHED, constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE) == "0":
                scheduler.remove_job(id=constants.JOB_UP_ID)
            else:
                playlists = get_user_playlists_array([])
                if len(playlists) > 0 and os.environ.get(constants.PLAYLIST_GEN_SCHED, constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE) != "0":
                    item = random.choice(playlists)
                    scheduler.modify_job(
                                    args=["name"],
                                    hours=int(os.environ.get(constants.PLAYLIST_GEN_SCHED, constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE)),
                                    id=constants.JOB_UP_ID
                                )
                else:
                    scheduler.remove_job(id=constants.JOB_UP_ID)
            

    if len(playlist_result['items']) != 0:
        get_user_playlists(playlist_name, offset=offset + 50)


def count_user_playlists(count, offset=0):
    """count user playlists"""
    sp = spotipy_helper.get_spotipy_client()
    playlist_result = sp.current_user_playlists(limit=50, offset=offset)
    count = count + len(playlist_result['items'])

    if len(playlist_result['items']) != 0:
        count = count_user_playlists(count, offset=offset + 50)
    return count

def get_user_playlists_array(array, offset=0):
    """get list of user playlists"""
    sp = spotipy_helper.get_spotipy_client()
    playlist_result = sp.current_user_playlists(limit=50, offset=offset)

    for item in playlist_result['items']:
        if item['name'] is not None and item['name'].strip() != '':
            array.append(item)

    if len(playlist_result['items']) != 0:
        array = get_user_playlists_array(array, offset=offset + 50)
    return array


def init_artists_recommendations():
    """all artists recommendations"""
    artist_names = subsonic_helper.get_artists_array_names()
    if len(artist_names) > 0:
        artist_name = random.choice(artist_names)
        if os.environ.get(constants.ARTIST_GEN_SCHED, constants.ARTIST_GEN_SCHED_DEFAULT_VALUE) != "0":
            old_job = scheduler.get_job(constants.JOB_AR_ID)
            if old_job is None:
                scheduler.add_job(
                        func=show_recommendations_for_artist,
                        trigger="interval",
                        args=[artist_name],
                        hours=int(os.environ.get(constants.ARTIST_GEN_SCHED, constants.ARTIST_GEN_SCHED_DEFAULT_VALUE)),
                        id=constants.JOB_AR_ID,
                        replace_existing=True,
                        max_instances=1
                )


def init_artists_top_tracks():
    """all artists top tracks"""
    artist_names = subsonic_helper.get_artists_array_names()
    if len(artist_names) > 0:
        artist_name = random.choice(artist_names)
        if os.environ.get(constants.ARTIST_TOP_GEN_SCHED, constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE) != "0":
            old_job = scheduler.get_job(constants.JOB_ATT_ID)
            if old_job is None:
                scheduler.add_job(
                        func=artist_top_tracks,
                        trigger="interval",
                        args=[artist_name],
                        hours=int(os.environ.get(constants.ARTIST_TOP_GEN_SCHED, constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE)),
                        id=constants.JOB_ATT_ID,
                        replace_existing=True,
                        max_instances=1
                    )


def get_user_saved_tracks(result):
    """get user saved tracks"""
    playlist_info = {}
    playlist_info["name"] = "Saved Tracks"
    playlist_info["spotify_uri"] = None
    playlist_info["type"] = constants.JOB_ST_ID
    sp = spotipy_helper.get_spotipy_client()
    result = get_user_saved_tracks_playlist(result)
    subsonic_helper.write_playlist(sp, playlist_info, result)
    if os.environ.get(constants.SAVED_GEN_SCHED, constants.SAVED_GEN_SCHED_DEFAULT_VALUE) != "0":
        scheduler.modify_job(
                hours=int(os.environ.get(constants.SAVED_GEN_SCHED, constants.SAVED_GEN_SCHED_DEFAULT_VALUE)),
                id=constants.JOB_ST_ID
        )
    else:
        scheduler.remove_job(id=constants.JOB_ST_ID)

def init_user_saved_tracks():
    """init user saved tracks"""
    if os.environ.get(constants.SAVED_GEN_SCHED, constants.SAVED_GEN_SCHED_DEFAULT_VALUE) != "0":
        old_job = scheduler.get_job(constants.JOB_ST_ID)
        if old_job is None:
            scheduler.add_job(
                    func=get_user_saved_tracks,
                    trigger="interval",
                    args=[dict({'tracks': []})],
                    hours=int(os.environ.get(constants.SAVED_GEN_SCHED, constants.SAVED_GEN_SCHED_DEFAULT_VALUE)),
                    id=constants.JOB_ST_ID,
                    replace_existing=True,
                    max_instances=1
            )
    
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

def init_user_playlists():
    playlists = get_user_playlists_array([])
    if len(playlists) > 0:
        item = random.choice(playlists)
        if os.environ.get(constants.PLAYLIST_GEN_SCHED, constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE) != "0":
            old_job = scheduler.get_job(constants.JOB_UP_ID)
            if old_job is None:
                scheduler.add_job(
                func=get_user_playlists,
                trigger="interval",
                args=[item['name'].strip()],
                hours=int(os.environ.get(constants.PLAYLIST_GEN_SCHED, constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE)),
                id=constants.JOB_UP_ID,
                replace_existing=True,
                max_instances=1
                )

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
    init_user_saved_tracks()
    init_my_reccomendations()
    init_artists_recommendations()
    init_artists_top_tracks()
    init_user_playlists()


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