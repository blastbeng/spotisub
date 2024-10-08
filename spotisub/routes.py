"""Spotisub routes module"""
import logging
import os
import random
import threading
import json
import math
import string
import subprocess
from threading import Lock
from time import sleep
from time import strftime
from requests import ConnectionError
from requests import ReadTimeout
from urllib3.exceptions import MaxRetryError
from flask import Blueprint
from flask import Response
from flask import request
from flask import render_template
from flask import url_for
from flask import redirect
from flask import flash
from flask_restx import Api
from flask_restx import Resource
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from pygtail import Pygtail
from spotipy.exceptions import SpotifyException
from spotisub import spotisub
from spotisub import configuration_db
from spotisub.forms import LoginForm
from spotisub.forms import RegistrationForm
from spotisub import classes
from spotisub import database
from spotisub.classes import User
from spotisub import utils
from spotisub import constants
from spotisub import generator
from spotisub.generator import subsonic_helper
from spotisub.generator import spotipy_helper
from spotisub.exceptions import SubsonicOfflineException
from spotisub.exceptions import SpotifyApiException

reimport_all_poll_thread = None
playlist_poll_thread = None
log_poll_thread = None
tasks_poll_thread = None
thread_lock = Lock()

@spotisub.after_request
def after_request(response):
    """Excluding healthcheck endpoint from logging"""
    if not request.path.startswith('/api/v1/utils/healthcheck'):
        timestamp = strftime('[%Y-%b-%d %H:%M]')
        logging.info('%s %s %s %s %s %s',
                     timestamp,
                     request.remote_addr,
                     request.method,
                     request.scheme,
                     request.full_path,
                     response.status)
    return response


@spotisub.errorhandler(Exception)
def all_exception_handler(error):
    utils.write_exception()
    return render_template('errors/404.html',
                           title='Error!',
                           errors=[repr(error)])


blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(blueprint, doc='/docs/')
spotisub.register_blueprint(blueprint)

socketio = SocketIO(spotisub, async_mode=None)
thread = None
thread_lock = Lock()

def get_response_json(data, status):
    """Generates json response"""
    r = Response(response=data, status=status, mimetype="application/json")
    r.headers["Content-Type"] = "application/json; charset=utf-8"
    r.headers["Accept"] = "application/json"
    return r


def get_json_message(message, is_ok):
    """Generates json message"""
    data = {
        "status": "ko" if is_ok is False else "ok",
        "message": message,
    }
    return json.dumps(data)


@spotisub.route('/')
@spotisub.route('/overview/')
@spotisub.route('/overview/<int:page>/')
@spotisub.route('/overview/<int:page>/<int:limit>/')
@spotisub.route('/overview/<int:page>/<int:limit>/<string:order>/')
@spotisub.route('/overview/<int:page>/<int:limit>/<string:order>/<int:asc>/')
@login_required
def overview(
        page=1,
        limit=100,
        order='playlist_info.subsonic_playlist_name',
        asc=1):
    title = 'Overview'
    spotipy_helper.get_secrets()
    all_playlists, song_count = subsonic_helper.select_all_playlists(
        spotipy_helper, page=page - 1, limit=limit, order=order, asc=(asc == 1))
    total_pages = math.ceil(song_count / limit)
    pagination_array, prev_page, next_page = utils.get_pagination(
        page, total_pages)
    sorting_dict = {}
    sorting_dict["Playlist Name"] = "playlist_info.subsonic_playlist_name"
    sorting_dict["Type"] = "playlist_info.type"
    return render_template('overview.html',
                           title=title,
                           playlists=all_playlists,
                           pagination_array=pagination_array,
                           prev_page=prev_page,
                           next_page=next_page,
                           current_page=page,
                           total_pages=total_pages,
                           limit=limit,
                           result_size=song_count,
                           order=order,
                           asc=asc,
                           sorting_dict=sorting_dict)

@spotisub.route('/reimport_all/')
@login_required
def reimport_all(uuid=None):
    """Reimport all playlists"""
    if not generator.reimport_all():
        flash('This import process is already running, please wait for it to finish or restart Spotisub to stop it.')
    return redirect(url_for('overview'))

@spotisub.route('/reimport/<string:uuid>/')
@login_required
def reimport(uuid=None):
    """Reimport a playlist"""
    playlist_info_running = generator.reimport(uuid)
    if playlist_info_running is not None:
        type = string.capwords(playlist_info_running.type.replace("_", " "))
        flash('A ' + type + ' import process is already running, please wait for it to finish or restart Spotisub to stop it. You can check the status going to System > Tasks.')
    return redirect(url_for('playlist', uuid=uuid))

@spotisub.route('/')
@spotisub.route('/overview_content/')
@spotisub.route('/overview_content/<int:page>/')
@spotisub.route('/overview_content/<int:page>/<int:limit>/')
@spotisub.route('/overview_content/<int:page>/<int:limit>/<string:order>/')
@spotisub.route('/overview_content/<int:page>/<int:limit>/<string:order>/<int:asc>/')
@login_required
def overview_content(
        page=1,
        limit=100,
        order='playlist_info.subsonic_playlist_name',
        asc=1):
    spotipy_helper.get_secrets()
    all_playlists, song_count = subsonic_helper.select_all_playlists(
        spotipy_helper, page=page - 1, limit=limit, order=order, asc=(asc == 1))
    sorting_dict = {}
    sorting_dict["Playlist Name"] = "playlist_info.subsonic_playlist_name"
    sorting_dict["Type"] = "playlist_info.type"
    return render_template('overview_content.html',
                           playlists=all_playlists,
                           limit=limit,
                           result_size=song_count,
                           order=order,
                           asc=asc)


@spotisub.route('/playlist/')
@spotisub.route('/playlist/<string:uuid>/')
@spotisub.route('/playlist/<string:uuid>/<int:page>/')
@spotisub.route('/playlist/<string:uuid>/<int:page>/<int:limit>/')
@spotisub.route('/playlist/<string:uuid>/<int:page>/<int:limit>/<string:order>/')
@spotisub.route('/playlist/<string:uuid>/<int:page>/<int:limit>/<string:order>/<int:asc>/')
@login_required
def playlist(uuid=None, page=1, limit=25,
             order='spotify_song.title', asc=1):
    title = 'Playlist'
    playlists, song_count = subsonic_helper.select_all_songs(
        page=page - 1, limit=limit, order=order, asc=(asc == 1), playlist_uuid=uuid)
    total_pages = math.ceil(song_count / limit)
    pagination_array, prev_page, next_page = utils.get_pagination(
        page, total_pages)

    playlist_info = subsonic_helper.select_playlist_info_by_uuid(
        spotipy_helper, uuid)

    sorting_dict = {}
    sorting_dict["Status"] = "subsonic_spotify_relation.subsonic_song_id"
    sorting_dict["Spotify Song Title"] = "spotify_song.title"
    sorting_dict["Spotify Artist"] = "spotify_artist.name"
    sorting_dict["Spotify Album"] = "spotify_album.name"
    sorting_dict["Playlist Name"] = "playlist_info.subsonic_playlist_name"

    return render_template('playlist.html',
                           title=title,
                           playlists=playlists,
                           uuid=uuid,
                           pagination_array=pagination_array,
                           prev_page=prev_page,
                           next_page=next_page,
                           current_page=page,
                           total_pages=total_pages,
                           limit=limit,
                           result_size=song_count,
                           order=order,
                           asc=asc,
                           playlist_info=playlist_info,
                           sorting_dict=sorting_dict)


@spotisub.route('/playlists/')
@spotisub.route('/playlists/<int:missing_only>/')
@spotisub.route('/playlists/<int:missing_only>/<int:page>/')
@spotisub.route('/playlists/<int:missing_only>/<int:page>/<int:limit>/')
@spotisub.route('/playlists/<int:missing_only>/<int:page>/<int:limit>/<string:order>/')
@spotisub.route('/playlists/<int:missing_only>/<int:page>/<int:limit>/<string:order>/<int:asc>/')
@spotisub.route('/playlists/<int:missing_only>/<int:page>/<int:limit>/<string:order>/<int:asc>/<string:search>/')
@login_required
def playlists(missing_only=0, page=1, limit=25,
              order='spotify_song.title', asc=1, search=None):
    title = 'Missing' if missing_only == 1 else 'Manage'
    missing_bool = True if missing_only == 1 else False
    playlists, song_count = subsonic_helper.select_all_songs(
        missing_only=missing_bool, page=page - 1, limit=limit, order=order, asc=(asc == 1), search=search)
    total_pages = math.ceil(song_count / limit)
    pagination_array, prev_page, next_page = utils.get_pagination(
        page, total_pages)

    sorting_dict = {}
    sorting_dict["Status"] = "subsonic_spotify_relation.subsonic_song_id"
    sorting_dict["Spotify Song Title"] = "spotify_song.title"
    sorting_dict["Spotify Artist"] = "spotify_artist.name"
    sorting_dict["Spotify Album"] = "spotify_album.name"
    sorting_dict["Playlist Name"] = "playlist_info.subsonic_playlist_name"

    return render_template('playlists.html',
                           title=title,
                           playlists=playlists,
                           missing_only=missing_only,
                           pagination_array=pagination_array,
                           prev_page=prev_page,
                           next_page=next_page,
                           current_page=page,
                           total_pages=total_pages,
                           limit=limit,
                           result_size=song_count,
                           order=order,
                           asc=asc,
                           search=search,
                           sorting_dict=sorting_dict)


@spotisub.route('/song/<string:uuid>/')
@spotisub.route('/song/<string:uuid>/<int:page>/')
@spotisub.route('/song/<string:uuid>/<int:page>/<int:limit>/')
@spotisub.route('/song/<string:uuid>/<int:page>/<int:limit>/<string:order>/')
@spotisub.route('/song/<string:uuid>/<int:page>/<int:limit>/<string:order>/<int:asc>/')
@login_required
def song(uuid=None, page=1, limit=25, order='spotify_song.title', asc=1):
    title = 'Song'
    spotipy_helper.get_secrets()
    song1, songs, song_count = subsonic_helper.load_song(
        uuid, spotipy_helper, page=page - 1, limit=limit, order=order, asc=(asc == 1))
    total_pages = math.ceil(song_count / limit)
    pagination_array, prev_page, next_page = utils.get_pagination(
        page, total_pages)

    sorting_dict = {}
    sorting_dict["Status"] = "subsonic_spotify_relation.subsonic_song_id"
    sorting_dict["Spotify Song Title"] = "spotify_song.title"
    sorting_dict["Spotify Artist"] = "spotify_artist.name"
    sorting_dict["Spotify Album"] = "spotify_album.name"
    sorting_dict["Playlist Name"] = "playlist_info.subsonic_playlist_name"

    return render_template('song.html',
                           title=title,
                           song=song1,
                           uuid=uuid,
                           songs=songs,
                           pagination_array=pagination_array,
                           prev_page=prev_page,
                           next_page=next_page,
                           current_page=page,
                           total_pages=total_pages,
                           limit=limit,
                           result_size=song_count,
                           order=order,
                           asc=asc,
                           sorting_dict=sorting_dict)


@spotisub.route('/album/<string:uuid>/')
@spotisub.route('/album/<string:uuid>/<int:page>/')
@spotisub.route('/album/<string:uuid>/<int:page>/<int:limit>/')
@spotisub.route('/album/<string:uuid>/<int:page>/<int:limit>/<string:order>/')
@spotisub.route('/album/<string:uuid>/<int:page>/<int:limit>/<string:order>/<int:asc>/')
@login_required
def album(uuid=None, page=1, limit=25, order='spotify_song.title', asc=1):
    title = 'Album'
    spotipy_helper.get_secrets()
    album1, songs, song_count = subsonic_helper.load_album(
        uuid, spotipy_helper, page=page - 1, limit=limit, order=order, asc=(asc == 1))
    total_pages = math.ceil(song_count / limit)
    pagination_array, prev_page, next_page = utils.get_pagination(
        page, total_pages)
    sorting_dict = {}
    sorting_dict["Status"] = "subsonic_spotify_relation.subsonic_song_id"
    sorting_dict["Spotify Song Title"] = "spotify_song.title"
    sorting_dict["Spotify Artist"] = "spotify_artist.name"
    sorting_dict["Spotify Album"] = "spotify_album.name"
    sorting_dict["Playlist Name"] = "playlist_info.subsonic_playlist_name"
    return render_template('album.html',
                           title=title,
                           album=album1,
                           uuid=uuid,
                           songs=songs,
                           pagination_array=pagination_array,
                           prev_page=prev_page,
                           next_page=next_page,
                           current_page=page,
                           total_pages=total_pages,
                           limit=limit,
                           result_size=song_count,
                           order=order,
                           asc=asc,
                           sorting_dict=sorting_dict)


@spotisub.route('/artist/<string:uuid>/')
@spotisub.route('/artist/<string:uuid>/<int:page>/')
@spotisub.route('/artist/<string:uuid>/<int:page>/<int:limit>/')
@spotisub.route('/artist/<string:uuid>/<int:page>/<int:limit>/<string:order>/')
@spotisub.route('/artist/<string:uuid>/<int:page>/<int:limit>/<string:order>/<int:asc>/')
@login_required
def artist(uuid=None, page=1, limit=25, order='spotify_song.title', asc=1):
    title = 'Artist'
    spotipy_helper.get_secrets()
    artist1, songs, song_count = subsonic_helper.load_artist(
        uuid, spotipy_helper, page=page - 1, limit=limit, order=order, asc=(asc == 1))
    total_pages = math.ceil(song_count / limit)
    pagination_array, prev_page, next_page = utils.get_pagination(
        page, total_pages)
    sorting_dict = {}
    sorting_dict["Status"] = "subsonic_spotify_relation.subsonic_song_id"
    sorting_dict["Spotify Song Title"] = "spotify_song.title"
    sorting_dict["Spotify Artist"] = "spotify_artist.name"
    sorting_dict["Spotify Album"] = "spotify_album.name"
    sorting_dict["Playlist Name"] = "playlist_info.subsonic_playlist_name"
    return render_template('artist.html',
                           title=title,
                           artist=artist1,
                           uuid=uuid,
                           songs=songs,
                           pagination_array=pagination_array,
                           prev_page=prev_page,
                           next_page=next_page,
                           current_page=page,
                           total_pages=total_pages,
                           limit=limit,
                           result_size=song_count,
                           order=order,
                           asc=asc,
                           sorting_dict=sorting_dict)


@spotisub.route('/tasks')
@login_required
def tasks():
    title = 'Tasks'
    return render_template('tasks.html',
                           title=title,
                           tasks=generator.get_tasks())


@spotisub.route('/logs')
@login_required
def logs():
    title = 'Logs'
    return render_template('logs.html',
                           title=title)


@socketio.event
def connect():
    global reimport_all_poll_thread
    global playlist_poll_thread
    global log_poll_thread
    global tasks_poll_thread
    with thread_lock:
        if reimport_all_poll_thread is None:
            reimport_all_poll_thread = socketio.start_background_task(poll_overview)
        if playlist_poll_thread is None:
            playlist_poll_thread = socketio.start_background_task(poll_playlist)
        if log_poll_thread is None:
            log_poll_thread = socketio.start_background_task(poll_log)
        if tasks_poll_thread is None:
            tasks_poll_thread = socketio.start_background_task(poll_tasks)
    emit('my_response', {'data': 'Connected', 'count': 0})

def poll_overview():
    with spotisub.test_request_context('/'):
        while True:
            if utils.check_thread_running_by_name("reimport_all"):
                emit('reimport_all_response', {'data': 'Reimport All job is running', 'status': 1}, namespace='/', broadcast=True)
            else:
                emit('reimport_all_response', {'data': 'Reimport All job is not running', 'status': 0}, namespace='/', broadcast=True)
            socketio.sleep(5)


def poll_playlist():
    with spotisub.test_request_context('/'):
        while True:
            uuids = generator.poll_playlist()
            if len(uuids) > 0:
                emit('playlist_response', {'data': 'Playlist import is running', 'uuids': uuids, 'status': 1}, namespace='/', broadcast=True)
            else:
                emit('playlist_response', {'data': 'Playlist import is not running', 'uuids': uuids, 'status': 0}, namespace='/', broadcast=True)
            socketio.sleep(5)


def poll_tasks():
    with spotisub.test_request_context('/'):
        while True:
            emit('tasks_response', generator.get_tasks(), namespace='/', broadcast=True)
            socketio.sleep(5)

def poll_log():
    return "work in progress"


@spotisub.route('/ignore/<string:type>/<string:uuid>/<int:value>/')
@login_required
def ignore(type=None, uuid=None, value=None):
    """Set ignored value to an object"""
    subsonic_helper.set_ignore(type, uuid, value)
    return get_response_json(
        get_json_message(
            "Setting ignored to " +
            str(value) +
            " to object with uuid " +
            uuid +
            ", type: " +
            type,
            True),
        200)


@spotisub.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('overview'))
    if not database.user_exists():
        return redirect(url_for('register'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('overview'))
    return render_template('login.html', title='Login', form=form)


@spotisub.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('overview'))
    if database.user_exists():
        flash('Spotisub user already exists. Please log in to continue')
        return redirect(url_for('login'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        configuration_db.session.add(user)
        configuration_db.session.commit()
        flash('Spotisub user successfully created. Please log in to continue')
        return redirect(url_for('login'))
    return render_template(
        'register.html', title='Create Spotisub credentials', form=form)


@spotisub.route('/logout')
@login_required
def logout():
    """Used to log out a user"""
    logout_user()
    return redirect(url_for('login'))


nsgenerate = api.namespace('generate', 'Generate APIs')


@nsgenerate.route('/artist_recommendations')
class ArtistRecommendationsClass(Resource):
    """Artist reccomendations class"""

    def get(self):
        """Artist reccomendations endpoint"""
        spotipy_helper.get_secrets()
        subsonic_helper.check_pysonic_connection()
        artist_names = subsonic_helper.get_artists_array_names()
        if len(artist_names) is None:
            return get_response_json(
                get_json_message(
                    "No artists found in your library",
                    True),
                206)
        threading.Thread(
            target=lambda: scheduler
            .run_job(constants.JOB_AR_ID)).start()
        return get_response_json(
            get_json_message(
                "Generating a random artist recommendations playlist",
                True),
            200)


@nsgenerate.route('/artist_top_tracks')
class ArtistTopTracksClass(Resource):
    """Artist top tracks class"""

    def get(self):
        """Artist top tracks endpoint"""
        spotipy_helper.get_secrets()
        subsonic_helper.check_pysonic_connection()
        artist_names = subsonic_helper.get_artists_array_names()
        if len(artist_names) is None:
            return get_response_json(
                get_json_message(
                    "No artists found in your library",
                    True),
                206)

        threading.Thread(
            target=lambda: scheduler
            .run_job(constants.JOB_ATT_ID)).start()
        return get_response_json(
            get_json_message(
                "Generating a random artist top tracks playlist",
                True),
            200)


@nsgenerate.route('/recommendations')
class RecommendationsClass(Resource):
    """Recommendations class"""

    def get(self):
        """Recommendations endpoint"""
        spotipy_helper.get_secrets()
        subsonic_helper.check_pysonic_connection()
        threading.Thread(
            target=lambda: scheduler
            .run_job(constants.JOB_MR_ID)).start()
        return get_response_json(
            get_json_message(
                "Generating a reccommendation playlist",
                True),
            200)


nsimport = api.namespace('import', 'Generate APIs')


@nsimport.route('/user_playlist')
class UserPlaylistsClass(Resource):
    """User playlists class"""

    def get(self):
        """User playlists endpoint"""
        spotipy_helper.get_secrets()
        subsonic_helper.check_pysonic_connection()
        count = generator.count_user_playlists(0)
        threading.Thread(
            target=lambda: scheduler
            .run_job(constants.JOB_UP_ID)).start()
        return get_response_json(get_json_message(
            "Importing a random playlist", True), 200)


@nsimport.route('/saved_tracks')
class SavedTracksClass(Resource):
    """Saved tracks class"""

    def get(self):
        """Saved tracks endpoint"""
        spotipy_helper.get_secrets()
        subsonic_helper.check_pysonic_connection()
        threading.Thread(
            target=lambda: scheduler
            .run_job(constants.JOB_ST_ID)).start()
        return get_response_json(get_json_message(
            "Importing your saved tracks", True), 200)


nsutils = api.namespace('utils', 'Utils APIs')


@nsutils.route('/healthcheck')
class Healthcheck(Resource):
    """Healthcheck class"""

    def get(self):
        """Healthcheck endpoint"""
        return "Ok!"
