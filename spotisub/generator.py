"""Subsonic generator"""
import logging
import os
import random
import time
import re
import string
import math
import threading
from datetime import datetime
from datetime import timedelta
from flask_apscheduler import APScheduler
from spotisub import spotisub
from spotisub import constants
from spotisub import database
from spotisub import utils
from spotisub.helpers import spotipy_helper
from spotisub.helpers import subsonic_helper
from spotisub.threading.spotisub_thread import thread_with_trace


scheduler = APScheduler()


def prechecks():
    spotipy_helper.get_secrets()
    subsonic_helper.check_pysonic_connection()


def scan_artists_top_tracks():
    artist_names = subsonic_helper.get_artists_array_names()
    if len(artist_names) > 0:
        for name in artist_names:
            artist = get_artist(name)
            if artist is not None and "uri" in artist and artist["uri"] is not None:
                playlist_name = name + " - Top Tracks"
                playlist_info = {}
                playlist_info["name"] = playlist_name
                playlist_info["import_arg"] = name
                playlist_info["spotify_uri"] = artist["uri"]
                playlist_info["type"] = constants.JOB_ATT_ID
                subsonic_helper.generate_playlist(playlist_info)


def scan_artists_recommendations():
    artist_names = subsonic_helper.get_artists_array_names()
    if len(artist_names) > 0:
        for name in artist_names:
            artist = get_artist(name)
            if artist is not None and "uri" in artist and artist["uri"] is not None:
                playlist_name = name + " - Recommendations"
                playlist_info = {}
                playlist_info["name"] = playlist_name
                playlist_info["spotify_uri"] = artist["uri"]
                playlist_info["type"] = constants.JOB_AR_ID
                playlist_info["import_arg"] = name
                subsonic_helper.generate_playlist(playlist_info)


def scan_my_recommendations():
    for playlist_num in range(int(os.environ.get(
            constants.NUM_USER_PLAYLISTS, constants.NUM_USER_PLAYLISTS_DEFAULT_VALUE))):
        playlist_name = "My Recommendations " + str(playlist_num + 1)
        playlist_info = {}
        playlist_info["name"] = playlist_name
        playlist_info["spotify_uri"] = None
        playlist_info["type"] = constants.JOB_MR_ID
        playlist_info["import_arg"] = playlist_num
        subsonic_helper.generate_playlist(playlist_info)


def scan_user_saved_tracks():
    playlist_info = {}
    playlist_info["name"] = "Saved Tracks"
    playlist_info["spotify_uri"] = None
    playlist_info["type"] = constants.JOB_ST_ID
    playlist_info["import_arg"] = ""
    subsonic_helper.generate_playlist(playlist_info)


def scan_user_playlists(offset=0):
    """get list of user playlists"""
    sp = spotipy_helper.get_spotipy_client()
    playlist_result = sp.current_user_playlists(limit=50, offset=offset)

    for item in playlist_result['items']:
        if item['name'] is not None and item['name'].strip() != '':
            playlist_info = {}
            playlist_info["name"] = item['name'].strip()
            playlist_info["spotify_uri"] = item["uri"]
            playlist_info["type"] = constants.JOB_UP_ID
            playlist_info["import_arg"] = item['name']
            subsonic_helper.generate_playlist(playlist_info)

    if len(playlist_result['items']) != 0:
        scan_user_playlists(offset=offset + 50)
    return


def init_artists_top_tracks():
    """all artists top tracks"""
    if os.environ.get(constants.ARTIST_TOP_GEN_SCHED,
                      constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE) != "0":
        playlist_infos = database.select_playlist_info_by_type(
            constants.JOB_ATT_ID)
        if len(playlist_infos) > 0:
            playlist_info = random.choice(playlist_infos)
            if playlist_info is not None and playlist_info.uuid is not None:
                old_job = scheduler.get_job(constants.JOB_ATT_ID)
                if old_job is None:
                    scheduler.add_job(
                        func=artist_top_tracks,
                        trigger="interval",
                        args=[
                            playlist_info.uuid],
                        hours=int(
                            os.environ.get(
                                constants.ARTIST_TOP_GEN_SCHED,
                                constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE)),
                        id=constants.JOB_ATT_ID,
                        replace_existing=True,
                        max_instances=1)


def init_artists_recommendations():
    """all artists recommendations"""
    if os.environ.get(constants.ARTIST_GEN_SCHED,
                      constants.ARTIST_GEN_SCHED_DEFAULT_VALUE) != "0":
        playlist_infos = database.select_playlist_info_by_type(
            constants.JOB_ATT_ID)
        if len(playlist_infos) > 0:
            playlist_info = random.choice(playlist_infos)
            if playlist_info is not None and playlist_info.uuid is not None:
                old_job = scheduler.get_job(constants.JOB_AR_ID)
                if old_job is None:
                    scheduler.add_job(
                        func=show_recommendations_for_artist,
                        trigger="interval",
                        args=[
                            playlist_info.uuid],
                        hours=int(
                            os.environ.get(
                                constants.ARTIST_GEN_SCHED,
                                constants.ARTIST_GEN_SCHED_DEFAULT_VALUE)),
                        id=constants.JOB_AR_ID,
                        replace_existing=True,
                        max_instances=1)


def init_my_recommendations():
    if os.environ.get(constants.RECOMEND_GEN_SCHED,
                      constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE) != "0":
        playlist_infos = database.select_playlist_info_by_type(
            constants.JOB_MR_ID)
        if len(playlist_infos) > 0:
            playlist_info = random.choice(playlist_infos)
            if playlist_info is not None and playlist_info.uuid is not None:
                old_job = scheduler.get_job(constants.JOB_MR_ID)
                if old_job is None:
                    scheduler.add_job(
                        func=my_recommendations,
                        trigger="interval",
                        args=[
                            playlist_info.uuid],
                        hours=int(
                            os.environ.get(
                                constants.RECOMEND_GEN_SCHED,
                                constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE)),
                        id=constants.JOB_MR_ID,
                        replace_existing=True,
                        max_instances=1)


def init_user_saved_tracks():
    """init user saved tracks"""
    name = "Saved Tracks"
    if os.environ.get(constants.SAVED_GEN_SCHED,
                      constants.SAVED_GEN_SCHED_DEFAULT_VALUE) != "0":
        playlist_infos = database.select_playlist_info_by_type(
            constants.JOB_ST_ID)
        if len(playlist_infos) > 0:
            playlist_info = playlist_infos[0]
            if playlist_info is not None and playlist_info.uuid is not None:
                old_job = scheduler.get_job(constants.JOB_ST_ID)
                if old_job is None:
                    scheduler.add_job(
                        func=get_user_saved_tracks,
                        trigger="interval",
                        args=[
                            playlist_info.uuid],
                        hours=int(
                            os.environ.get(
                                constants.SAVED_GEN_SCHED,
                                constants.SAVED_GEN_SCHED_DEFAULT_VALUE)),
                        id=constants.JOB_ST_ID,
                        replace_existing=True,
                        max_instances=1)


def init_user_playlists():
    if os.environ.get(constants.PLAYLIST_GEN_SCHED,
                      constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE) != "0":
        playlist_infos = database.select_playlist_info_by_type(
            constants.JOB_UP_ID)
        if len(playlist_infos) > 0:
            playlist_info = random.choice(playlist_infos)
            if playlist_info is not None and playlist_info.uuid is not None:
                old_job = scheduler.get_job(constants.JOB_UP_ID)
                if old_job is None:
                    scheduler.add_job(
                        func=get_user_playlists,
                        trigger="interval",
                        args=[
                            playlist_info.uuid],
                        hours=int(
                            os.environ.get(
                                constants.PLAYLIST_GEN_SCHED,
                                constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE)),
                        id=constants.JOB_UP_ID,
                        replace_existing=True,
                        max_instances=1)


def artist_top_tracks(uuid):
    """artist top tracks"""
    playlist_info_db = database.select_playlist_info_by_uuid(uuid)
    if playlist_info_db is not None and playlist_info_db.uuid is not None:
        artist = get_artist(playlist_info_db.import_arg)
        if artist is not None and "uri" in artist and artist["uri"] is not None:
            playlist_name = playlist_info_db.import_arg + " - Top Tracks"
            playlist_info = {}
            playlist_info["uuid"] = playlist_info_db.uuid
            playlist_info["name"] = playlist_name
            playlist_info["import_arg"] = playlist_info_db.import_arg
            playlist_info["spotify_uri"] = artist["uri"]
            playlist_info["type"] = constants.JOB_ATT_ID
            logging.info('(%s) Searching top tracks for: %s',
                         str(threading.current_thread().ident), playlist_info_db.import_arg)
            sp = spotipy_helper.get_spotipy_client()
            artist_top = sp.artist_top_tracks(artist["uri"])
            subsonic_helper.write_playlist(sp, playlist_info, artist_top)
        else:
            logging.warning('(%s) Artist: %s Not found!', str(
                threading.current_thread().ident), playlist_info_db.import_arg)

    if os.environ.get(constants.ARTIST_GEN_SCHED,
                      constants.ARTIST_GEN_SCHED_DEFAULT_VALUE) == "0":
        scheduler.remove_job(id=constants.JOB_ATT_ID)
    else:
        artist_names = subsonic_helper.get_artists_array_names()
        if len(artist_names) > 0 and os.environ.get(
                constants.ARTIST_TOP_GEN_SCHED,
                constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE) != "0":
            artist_name = random.choice(artist_names)
            playlist_infos = database.select_playlist_info_by_type(
                constants.JOB_ATT_ID)
            if len(playlist_infos) > 0:
                playlist_info_rnd = random.choice(playlist_infos)
                if playlist_info_rnd is not None and playlist_info_rnd.uuid is not None:
                    scheduler.modify_job(
                        args=[playlist_info_rnd.uuid],
                        id=constants.JOB_ATT_ID
                    )
        else:
            scheduler.remove_job(id=constants.JOB_ATT_ID)


def show_recommendations_for_artist(uuid):
    """get user saved tracks"""
    if not utils.check_thread_running_by_name("reimport_all"):
        thread = thread_with_trace(
            target=lambda: show_recommendations_for_artist_run(uuid),
            name=constants.JOB_AR_ID + "_" + uuid)
        thread.start()
        thread.join()
    else:
        logging.info("Skipping thread execution becase a full reimport process is running")


def show_recommendations_for_artist_run(uuid):
    """show recommendations for artist"""

    playlist_info_db = database.select_playlist_info_by_uuid(uuid)
    if playlist_info_db is not None and playlist_info_db.uuid is not None:
        artist = get_artist(playlist_info_db.import_arg)
        if artist is not None and "uri" in artist and artist["uri"] is not None:
            playlist_name = playlist_info_db.import_arg + " - Recommendations"
            playlist_info = {}
            playlist_info["uuid"] = playlist_info_db.uuid
            playlist_info["name"] = playlist_name
            playlist_info["spotify_uri"] = artist["uri"]
            playlist_info["type"] = constants.JOB_AR_ID
            playlist_info["import_arg"] = playlist_info_db.import_arg
            logging.info('(%s) Searching recommendations for: %s', str(
                threading.current_thread().ident), playlist_info_db.import_arg)
            sp = spotipy_helper.get_spotipy_client()
            results = sp.recommendations(
                seed_artists=[
                    artist['id']],
                limit=int(
                    os.environ.get(
                        constants.ITEMS_PER_PLAYLIST,
                        constants.ITEMS_PER_PLAYLIST_DEFAULT_VALUE)))
            subsonic_helper.write_playlist(sp, playlist_info, results)
        else:
            logging.warning('(%s) Artist: %s Not found!', str(
                threading.current_thread().ident), playlist_info_db.import_arg)

    if os.environ.get(constants.ARTIST_GEN_SCHED,
                      constants.ARTIST_GEN_SCHED_DEFAULT_VALUE) == "0":
        scheduler.remove_job(id=constants.JOB_AR_ID)
    else:
        artist_names = subsonic_helper.get_artists_array_names()
        if len(artist_names) > 0:
            artist_name = random.choice(artist_names)
            playlist_infos = database.select_playlist_info_by_type(
                constants.JOB_ATT_ID)
            if len(playlist_infos) > 0:
                playlist_info_rnd = random.choice(playlist_infos)
                if playlist_info_rnd is not None and playlist_info_rnd.uuid is not None:
                    scheduler.modify_job(
                        args=[playlist_info_rnd.uuid],
                        id=constants.JOB_AR_ID
                    )
        else:
            scheduler.remove_job(id=constants.JOB_AR_ID)


def my_recommendations(uuid):
    """get user saved tracks"""
    if not utils.check_thread_running_by_name("reimport_all"):
        thread = thread_with_trace(
            target=lambda: my_recommendations_run(uuid),
            name=constants.JOB_MR_ID + "_" + uuid)
        thread.start()
        thread.join()
    else:
        logging.info("Skipping thread execution becase a full reimport process is running")


def my_recommendations_run(uuid):
    """my recommendations"""
    playlist_info_db = database.select_playlist_info_by_uuid(uuid)
    if playlist_info_db is not None and playlist_info_db.uuid is not None:
        playlist_num = int(playlist_info_db.import_arg)
        sp = spotipy_helper.get_spotipy_client()
        top_tracks = None
        liked_tracks = None
        history = None
        top_tracks = sp.current_user_top_tracks(
            limit=50, time_range='long_term')
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
        results = sp.recommendations(seed_tracks=seed_track_ids[0:5], limit=int(os.environ.get(
            constants.ITEMS_PER_PLAYLIST, constants.ITEMS_PER_PLAYLIST_DEFAULT_VALUE)))

        playlist_name = "My Recommendations " + str((playlist_num) + 1)
        playlist_info = {}
        playlist_info["uuid"] = playlist_info_db.uuid
        playlist_info["name"] = playlist_name
        playlist_info["spotify_uri"] = None
        playlist_info["type"] = constants.JOB_MR_ID
        playlist_info["import_arg"] = playlist_info_db.import_arg
        subsonic_helper.write_playlist(
            sp, playlist_info, results)

    if os.environ.get(constants.RECOMEND_GEN_SCHED,
                      constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE) == "0":
        scheduler.remove_job(id=constants.JOB_MR_ID)
    else:
        artist_names = subsonic_helper.get_artists_array_names()
        if len(artist_names) > 0:
            artist_name = random.choice(artist_names)
            playlist_infos = database.select_playlist_info_by_type(
                constants.JOB_MR_ID)
            if len(playlist_infos) > 0:
                playlist_info_rnd = random.choice(playlist_infos)
                if playlist_info_rnd is not None and playlist_info_rnd.uuid is not None:
                    scheduler.modify_job(
                        args=[playlist_info_rnd.uuid],
                        id=constants.JOB_MR_ID
                    )
        else:
            scheduler.remove_job(id=constants.JOB_MR_ID)


def get_user_saved_tracks(uuid):
    """get user saved tracks"""
    if not utils.check_thread_running_by_name("reimport_all"):
        thread = thread_with_trace(
            target=lambda: get_user_saved_tracks_run(uuid),
            name=constants.JOB_ST_ID + "_" + uuid)
        thread.start()
        thread.join()
    else:
        logging.info("Skipping thread execution becase a full reimport process is running")


def get_user_saved_tracks_run(uuid):
    """get user saved tracks run"""
    playlist_info_db = database.select_playlist_info_by_uuid(uuid)
    if playlist_info_db is not None and playlist_info_db.uuid is not None:
        playlist_info = {}
        playlist_info["uuid"] = playlist_info_db.uuid
        playlist_info["name"] = playlist_info_db.subsonic_playlist_name
        playlist_info["spotify_uri"] = None
        playlist_info["type"] = constants.JOB_ST_ID
        playlist_info["import_arg"] = ""
        sp = spotipy_helper.get_spotipy_client()
        result = dict({'tracks': []})
        result = get_user_saved_tracks_playlist(result)
        subsonic_helper.write_playlist(sp, playlist_info, result)

    if os.environ.get(constants.SAVED_GEN_SCHED,
                      constants.SAVED_GEN_SCHED_DEFAULT_VALUE) == "0":
        scheduler.remove_job(id=constants.JOB_MR_ID)


def get_user_playlists(uuid):
    """get user saved tracks"""
    if not utils.check_thread_running_by_name("reimport_all"):
        thread = thread_with_trace(
            target=lambda: get_user_playlists_run(uuid),
            name=constants.JOB_UP_ID + "_" + uuid)
        thread.start()
        thread.join()
    else:
        logging.info("Skipping thread execution becase a full reimport process is running")


def get_user_playlists_run(uuid, offset=0):
    """get user playlists"""
    playlist_info_db = database.select_playlist_info_by_uuid(uuid)
    if playlist_info_db is not None and playlist_info_db.uuid is not None:

        sp = spotipy_helper.get_spotipy_client()

        playlist_result = sp.current_user_playlists(
            limit=50, offset=offset)

        for item in playlist_result['items']:
            if item['name'] is not None and item['name'].strip() != '' and (playlist_info_db.import_arg is None or (
                    playlist_info_db.import_arg is not None and item['name'].lower().strip() == playlist_info_db.import_arg.lower().strip())):
                playlist_info = {}
                playlist_info["uuid"] = playlist_info_db.uuid
                playlist_info["name"] = item['name'].strip()
                playlist_info["spotify_uri"] = item["uri"]
                playlist_info["type"] = constants.JOB_UP_ID
                playlist_info["import_arg"] = item['name']
                logging.info(
                    '(%s) Importing playlist: %s', str(
                        threading.current_thread().ident), item['name'])
                result = dict({'tracks': []})
                result = get_playlist_tracks(item, result)
                subsonic_helper.write_playlist(sp, playlist_info, result)

        if len(playlist_result['items']) != 0:
            get_user_playlists_run(uuid, offset=offset + 50)

    if os.environ.get(constants.PLAYLIST_GEN_SCHED,
                      constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE) == "0":
        scheduler.remove_job(id=constants.JOB_UP_ID)
    else:
        playlist_infos = database.select_playlist_info_by_type(
            constants.JOB_UP_ID)
        if len(playlist_infos) > 0 and os.environ.get(
                constants.PLAYLIST_GEN_SCHED,
                constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE) != "0":
            playlist_info = random.choice(playlist_infos)
            scheduler.modify_job(
                args=[playlist_info.uuid],
                id=constants.JOB_UP_ID
            )
        else:
            scheduler.remove_job(id=constants.JOB_UP_ID)


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


def get_artist(name):
    """get artist"""
    sp = spotipy_helper.get_spotipy_client()
    results = sp.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        return items[0]
    return None


def get_playlist_tracks(item, result, offset_tracks=0):
    """get playlist tracks"""
    sp = spotipy_helper.get_spotipy_client()
    response_tracks = sp.playlist_items(
        item['id'],
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


def reimport(uuid):
    playlist_info = database.select_playlist_info_by_uuid(uuid)
    timedelta_sec = timedelta(seconds=5)
    for thread in threading.enumerate():
        if (thread.name == playlist_info.type or thread.name.startswith(
                playlist_info.type)) and thread.is_alive():
            #thread.kill()
            timedelta_sec = timedelta(seconds=30)
            return playlist_info
    if playlist_info is not None:
        if playlist_info.type == constants.JOB_AR_ID:
            run_job_now(
                timedelta_sec,
                show_recommendations_for_artist,
                constants.JOB_AR_ID,
                [uuid],
                constants.ARTIST_GEN_SCHED,
                constants.ARTIST_GEN_SCHED_DEFAULT_VALUE)
        elif playlist_info.type == constants.JOB_ATT_ID:
            run_job_now(
                timedelta_sec,
                artist_top_tracks,
                constants.JOB_ATT_ID,
                [uuid],
                constants.ARTIST_TOP_GEN_SCHED,
                constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE)
        elif playlist_info.type == constants.JOB_MR_ID:
            run_job_now(
                timedelta_sec,
                my_recommendations,
                constants.JOB_MR_ID,
                [uuid],
                constants.RECOMEND_GEN_SCHED,
                constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE)
        elif playlist_info.type == constants.JOB_UP_ID:
            run_job_now(
                timedelta_sec,
                get_user_playlists,
                constants.JOB_UP_ID,
                [uuid],
                constants.PLAYLIST_GEN_SCHED,
                constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE)
        elif playlist_info.type == constants.JOB_ST_ID:
            run_job_now(
                timedelta_sec,
                get_user_saved_tracks,
                constants.JOB_ST_ID,
                [uuid],
                constants.SAVED_GEN_SCHED,
                constants.SAVED_GEN_SCHED_DEFAULT_VALUE)
    return None

def get_tasks():
    tasks = []
    types = database.select_distinct_type_name()
    for type in types:
        job = scheduler.get_job(type)
        if job is not None:
            task = {}
            thread_name = job.id
            task["type"] = type
            task["type_desc"] = "Import " + string.capwords(type.replace("_", " "))
            task["next_execution"] = job.next_run_time.strftime("%d/%m %H:%M:%S")
            task["interval"] = str( math.trunc(job.trigger.interval_length / 60 / 60) ) + " hour(s)"
            if len(job.args) > 0:
                pl_info = database.select_playlist_info_by_uuid(str( job.args[0] ))
                if pl_info is not None:
                    task["args"] = pl_info.subsonic_playlist_name
                task["uuid"] = job.args[0]
                    
            else:
                task["args"] = ""
            task["running"] = "1" if utils.check_thread_running_by_init_name(thread_name) else "0"
            task["id"] = thread_name
            tasks.append(task)

    thread_name = "reimport_all"
    task = {}
    task["type"] = "reimport_all"
    task["type_desc"] = "(Re)Import All"
    task["args"] = ""
    task["uuid"] = ""
    task["next_execution"] = "Manual"
    task["interval"] = ""
    task["running"] = "1" if utils.check_thread_running_by_name(thread_name) else "0"
    task["id"] = thread_name
    tasks.append(task)
    
    return tasks

def poll_playlist():
    uuids = []
    types = database.select_distinct_type_name()
    for thread in threading.enumerate():
        for type in types:
            if (thread.name.startswith(type)) and thread.is_alive():
                uuids.append(thread.name.split("_")[-1])
    return uuids


def run_job_now(
        timedelta_sec,
        function,
        job_id,
        args,
        schedule,
        default_value):
    scheduler.add_job(
        func=function,
        trigger="interval",
        args=args,
        hours=int(os.environ.get(schedule, default_value)),
        id=job_id,
        replace_existing=True,
        max_instances=1
    )
    next_run_time = datetime.now() + timedelta_sec
    scheduler.modify_job(id=job_id, next_run_time=next_run_time)


def init_jobs():
    """Used to initialize Spotisub Jobs"""
    init_user_saved_tracks()
    init_my_recommendations()
    init_artists_recommendations()
    init_artists_top_tracks()
    init_user_playlists()


def scan_library():
    """Used to initialize Spotisub Jobs"""
    scan_user_saved_tracks()
    scan_my_recommendations()
    scan_artists_recommendations()
    scan_artists_top_tracks()
    scan_user_playlists()

def reimport_all():
    """Used to reimport everything"""
    if not utils.check_thread_running_by_name("reimport_all"):
        thread = thread_with_trace(
            target=lambda: reimport_all_thread(),
            name="reimport_all").start()
        return True
    return False

def reimport_all_thread():
    """Used to reimport everything"""
    import_all_user_saved_tracks()
    import_all_my_recommendations()
    import_all_user_playlists()
    import_all_artists_recommendations()
    import_all_artists_top_tracks()

def import_all_user_saved_tracks():
    playlist_infos = database.select_playlist_info_by_type(
            constants.JOB_ST_ID)
    if len(playlist_infos) > 0:
        get_user_saved_tracks_run(playlist_infos[0].uuid)

def import_all_my_recommendations():
    playlist_infos = database.select_playlist_info_by_type(
            constants.JOB_MR_ID)
    if len(playlist_infos) > 0:
        for playlist_info in playlist_infos:
            my_recommendations_run(playlist_info.uuid)

def import_all_artists_recommendations():
    playlist_infos = database.select_playlist_info_by_type(
            constants.JOB_AR_ID)
    if len(playlist_infos) > 0:
        for playlist_info in playlist_infos:
            show_recommendations_for_artist_run(playlist_info.uuid)

def import_all_artists_top_tracks():
    playlist_infos = database.select_playlist_info_by_type(
            constants.JOB_ATT_ID)
    if len(playlist_infos) > 0:
        for playlist_info in playlist_infos:
            artist_top_tracks_run(playlist_info.uuid)

def import_all_user_playlists():
    playlist_infos = database.select_playlist_info_by_type(
            constants.JOB_UP_ID)
    if len(playlist_infos) > 0:
        for playlist_info in playlist_infos:
            get_user_playlists_run(playlist_info.uuid)


scheduler.add_job(
    func=subsonic_helper.remove_subsonic_deleted_playlist,
    trigger="interval",
    hours=8,
    id="remove_deleted_playlists",
    replace_existing=True,
    max_instances=1
)

scheduler.add_job(
    func=init_jobs,
    trigger="interval",
    hours=1,
    id="init_jobs",
    replace_existing=True,
    max_instances=1
)
scheduler.add_job(
    func=scan_library,
    trigger="interval",
    hours=24,
    id="scan_library",
    replace_existing=True,
    max_instances=1
)

scheduler.init_app(spotisub)
scheduler.start(
    paused=(
        os.environ.get(
            constants.SCHEDULER_ENABLED,
            constants.SCHEDULER_ENABLED_DEFAULT_VALUE) != "1"))

try:
    subsonic_helper.select_all_playlists(
        spotipy_helper,
        page=0,
        limit=100,
        order='playlist_info.subsonic_playlist_name',
        asc=True)
except BaseException:
    utils.write_exception()
    pass

scheduler.modify_job(id="init_jobs", next_run_time=datetime.now())
scheduler.modify_job(id="scan_library", next_run_time=datetime.now())
