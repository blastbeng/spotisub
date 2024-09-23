"""Spotisub routes module"""
import logging
import os
import random
import threading
import json
import math
from time import strftime
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
from flask_apscheduler import APScheduler
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
from spotisub import database
from spotisub.generator import subsonic_helper
from spotisub.generator import spotipy_helper
from spotisub.exceptions import SubsonicOfflineException
from spotisub.exceptions import SpotifyApiException


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

blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(blueprint, doc='/docs/')
spotisub.register_blueprint(blueprint)

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
@spotisub.route('/playlists/')
@spotisub.route('/playlists/<int:missing_only>/')
@spotisub.route('/playlists/<int:missing_only>/<int:page>/')
@spotisub.route('/playlists/<int:missing_only>/<int:page>/<int:limit>/')
@spotisub.route('/playlists/<int:missing_only>/<int:page>/<int:limit>/<string:search>/')
@login_required
def playlists(missing_only = 0, page = 1, limit = 25, search = None):
    title = 'Missing' if missing_only == 1 else 'Manage'
    try:
        missing_bool = True if missing_only == 1 else False
        song_count = subsonic_helper.count_playlists(missing_only=missing_bool)
        total_pages = math.ceil(song_count/limit)
        playlists = subsonic_helper.get_playlist_songs(
                    missing_only=missing_bool, page=page-1, limit=limit)
        pagination_array, prev_page, next_page = utils.get_pagination(page, total_pages)
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
            result_size=song_count)
    except SubsonicOfflineException:
        return render_template('errors/404.html', 
            title=title,
            error="Unable to communicate with Subsonic.") 

@spotisub.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('playlists'))
    if not database.user_exists():
        return redirect(url_for('register'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome {user.username}')
        return redirect(url_for('playlists'))
    return render_template('login.html', title='Login', form=form)


@spotisub.route('/register',methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('playlists'))
    if database.user_exists():
        flash('Spotisub user already exists. Please log in to continue')
        return redirect(url_for('login'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        configuration_db.session.add(user)
        configuration_db.session.commit()
        flash('Spotisub user successfully. Please log in to continue')
        return redirect(url_for('login'))
    return render_template('register.html', title='Create Spotisub credentials', form=form)

@spotisub.route('/logout')
@login_required
def logout():
    """Used to log out a user"""
    logout_user()
    return redirect(url_for('login'))


nsgenerate = api.namespace('generate', 'Generate APIs')


@nsgenerate.route('/artist_recommendations/')
@nsgenerate.route('/artist_recommendations/<string:artist_name>/')
class ArtistRecommendationsClass(Resource):
    """Artist reccomendations class"""
    def get(self, artist_name=None):
        """Artist reccomendations endpoint"""
        try:
            spotipy_helper.get_secrets()
            subsonic_helper.check_pysonic_connection()
            if artist_name is None:
                artist_name = random.choice(
                    subsonic_helper.get_artists_array_names())
            else:
                search_result_name = subsonic_helper.search_artist(artist_name)
                if search_result_name is None:
                    return get_response_json(
                        get_json_message(
                            "Artist " +
                            artist_name +
                            " not found, maybe a misspelling error?",
                            True),
                        206)
                artist_name = search_result_name
            if artist_name is not None:
                threading.Thread(
                    target=lambda: generator
                    .show_recommendations_for_artist(artist_name)).start()
                return get_response_json(
                    get_json_message(
                        "Generating recommendations playlist for artist " +
                        artist_name,
                        True),
                    200)
            return get_response_json(
                get_json_message(
                    "Bad request",
                    False),
                400)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except SpotifyApiException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Spotify API Error. Please check your configuruation.",
                    False),
                400)


@nsgenerate.route('/artist_recommendations/all/')
class ArtistRecommendationsAllClass(Resource):
    """All Artists reccomendations class"""

    def get(self):
        """All Artists reccomendations endpoint"""
        try:
            spotipy_helper.get_secrets()
            subsonic_helper.check_pysonic_connection()
            threading.Thread(
                target=lambda: generator
                .all_artists_recommendations(get_subsonic_helper()
                                             .get_artists_array_names())).start()
            return get_response_json(
                get_json_message(
                    "Generating recommendations playlist for all artists",
                    True),
                200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except SpotifyApiException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Spotify API Error. Please check your configuruation.",
                    False),
                400)


@nsgenerate.route('/artist_top_tracks/')
@nsgenerate.route('/artist_top_tracks/<string:artist_name>/')
class ArtistTopTracksClass(Resource):
    """Artist top tracks class"""

    def get(self, artist_name=None):
        """Artist top tracks endpoint"""
        try:
            spotipy_helper.get_secrets()
            subsonic_helper.check_pysonic_connection()
            if artist_name is None:
                artist_name = random.choice(
                    subsonic_helper.get_artists_array_names())
            else:
                search_result_name = subsonic_helper.search_artist(artist_name)
                if search_result_name is None:
                    return get_response_json(
                        get_json_message(
                            "Artist " +
                            artist_name +
                            " not found, maybe a misspelling error?",
                            True),
                        206)
                artist_name = search_result_name
            if artist_name is not None:
                threading.Thread(
                    target=lambda: generator.artist_top_tracks(artist_name)).start()
                return get_response_json(
                    get_json_message(
                        "Generating top tracks playlist for artist " +
                        artist_name,
                        True),
                    200)
            return get_response_json(
                get_json_message(
                    "Bad request",
                    False),
                400)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except SpotifyApiException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Spotify API Error. Please check your configuruation.",
                    False),
                400)


@nsgenerate.route('/artist_top_tracks/all/')
class ArtistTopTracksAllClass(Resource):
    """All Artists top tracks class"""

    def get(self):
        """All Artists top tracks endpoint"""
        try:
            spotipy_helper.get_secrets()
            subsonic_helper.check_pysonic_connection()
            threading.Thread(
                target=lambda: generator
                .all_artists_top_tracks(get_subsonic_helper()
                                        .get_artists_array_names())).start()
            return get_response_json(
                get_json_message(
                    "Generating top tracks playlist for all artists",
                    True),
                200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except SpotifyApiException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Spotify API Error. Please check your configuruation.",
                    False),
                400)


@nsgenerate.route('/recommendations')
class RecommendationsClass(Resource):
    """Recommendations class"""

    def get(self):
        """Recommendations endpoint"""
        try:
            spotipy_helper.get_secrets()
            subsonic_helper.check_pysonic_connection()
            threading.Thread(
                target=lambda: generator.my_recommendations(
                    count=random.randrange(
                        int(
                            os.environ.get(
                                constants.NUM_USER_PLAYLISTS,
                                constants.NUM_USER_PLAYLISTS_DEFAULT_VALUE))))).start()
            return get_response_json(
                get_json_message(
                    "Generating a reccommendation playlist",
                    True),
                200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except SpotifyApiException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Spotify API Error. Please check your configuruation.",
                    False),
                400)


nsimport = api.namespace('import', 'Generate APIs')


@nsimport.route('/user_playlist/')
@nsimport.route('/user_playlist/<string:playlist_name>/')
class UserPlaylistsClass(Resource):
    """User playlists class"""

    def get(self, playlist_name=None):
        """User playlists endpoint"""
        try:
            spotipy_helper.get_secrets()
            subsonic_helper.check_pysonic_connection()
            if playlist_name is None:
                count = generator.count_user_playlists(0)
                threading.Thread(
                    target=lambda: generator.get_user_playlists(
                        random.randrange(count),
                        single_execution=True)).start()
                return get_response_json(get_json_message(
                    "Importing a random playlist", True), 200)
            search_result_name = generator.get_user_playlist_by_name(
                playlist_name)
            if search_result_name is None:
                return get_response_json(
                    get_json_message(
                        "Playlist " +
                        playlist_name +
                        " not found, maybe a misspelling error?",
                        True),
                    206)
            playlist_name = search_result_name
            if playlist_name is not None:
                threading.Thread(target=lambda: generator.get_user_playlists(
                    0, single_execution=False, playlist_name=playlist_name)).start()
                return get_response_json(
                    get_json_message(
                        "Searching and importing your spotify account for playlist " +
                        playlist_name,
                        True),
                    200)
            return get_response_json(
                get_json_message(
                    "Bad request",
                    False),
                400)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except SpotifyApiException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Spotify API Error. Please check your configuruation.",
                    False),
                400)


@nsimport.route('/user_playlist/all/')
class UserPlaylistsAllClass(Resource):
    """All User playlists class"""

    def get(self):
        """All User playlists endpoint"""
        try:
            spotipy_helper.get_secrets()
            subsonic_helper.check_pysonic_connection()
            threading.Thread(
                target=lambda: generator.get_user_playlists(0)).start()
            return get_response_json(
                get_json_message(
                    "Importing all your spotify playlists",
                    True),
                200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except SpotifyApiException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Spotify API Error. Please check your configuruation.",
                    False),
                400)


@nsimport.route('/saved_tracks')
class SavedTracksClass(Resource):
    """Saved tracks class"""

    def get(self):
        """Saved tracks endpoint"""
        try:
            spotipy_helper.get_secrets()
            subsonic_helper.check_pysonic_connection()
            threading.Thread(
                target=lambda: generator
                .get_user_saved_tracks(dict({'tracks': []}))).start()
            return get_response_json(get_json_message(
                "Importing your saved tracks", True), 200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except SpotifyApiException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Spotify API Error. Please check your configuruation.",
                    False),
                400)


nsdatabase = api.namespace('database', 'Database APIs')


@nsdatabase.route('/playlist/unmatched')
class PlaylistUnmatchedClass(Resource):
    """Unmatched playlist songs class"""

    def get(self):
        """Unmatched playlist songs endpoint"""
        try:
            spotipy_helper.get_secrets()
            subsonic_helper.check_pysonic_connection()
            missing_songs = subsonic_helper.get_playlist_songs(
                missing_only=True)
            return get_response_json(json.dumps(missing_songs), 200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except SpotifyApiException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Spotify API Error. Please check your configuruation.",
                    False),
                400)


nsdatabase = api.namespace('database', 'Database APIs')


@nsdatabase.route('/playlist/all')
class PlaylistAllClass(Resource):
    """All playlist songs class"""

    def get(self):
        """All playlist songs endpoint"""
        try:
            spotipy_helper.get_secrets()
            subsonic_helper.check_pysonic_connection()
            missing_songs = subsonic_helper.get_playlist_songs(
                missing_only=False)
            return get_response_json(json.dumps(missing_songs), 200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except SpotifyApiException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Spotify API Error. Please check your configuruation.",
                    False),
                400)


nsutils = api.namespace('utils', 'Utils APIs')


@nsutils.route('/healthcheck')
class Healthcheck(Resource):
    """Healthcheck class"""

    def get(self):
        """Healthcheck endpoint"""
        return "Ok!"


scheduler = APScheduler()


if os.environ.get(constants.ARTIST_GEN_SCHED,
                  constants.ARTIST_GEN_SCHED_DEFAULT_VALUE) != "0":
    @scheduler.task('interval',
                    id=constants.JOB_AR_ID,
                    hours=int(os.environ.get(constants.ARTIST_GEN_SCHED,
                                             constants.ARTIST_GEN_SCHED_DEFAULT_VALUE)))
    def artist_recommendations():
        """artist_recommendations task"""
        generator.show_recommendations_for_artist(
            random.choice(subsonic_helper.get_artists_array_names()))
            
if os.environ.get(constants.ARTIST_TOP_GEN_SCHED,
                  constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE) != "0":
    @scheduler.task('interval',
                    id=constants.JOB_ATT_ID,
                    hours=int(os.environ.get(constants.ARTIST_TOP_GEN_SCHED,
                                             constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE)))
    def artist_top_tracks():
        """artist_top_tracks task"""
        generator.artist_top_tracks(
            random.choice(subsonic_helper.get_artists_array_names()))

if os.environ.get(constants.RECOMEND_GEN_SCHED,
                  constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE) != "0":
    @scheduler.task('interval',
                    id=constants.JOB_MR_ID,
                    hours=int(os.environ.get(constants.RECOMEND_GEN_SCHED,
                                             constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE)))

    def my_recommendations():
        """my_recommendations task"""
        generator.my_recommendations(count=random.randrange(int(os.environ.get(
            constants.NUM_USER_PLAYLISTS, constants.NUM_USER_PLAYLISTS_DEFAULT_VALUE))))

if os.environ.get(constants.PLAYLIST_GEN_SCHED,
                  constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE) != "0":
    @scheduler.task('interval',
                    id=constants.JOB_UP_ID,
                    hours=int(os.environ.get(constants.PLAYLIST_GEN_SCHED,
                                             constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE)))
    def user_playlists():
        """user_playlists task"""
        generator.get_user_playlists(
            random.randrange(
                generator.count_user_playlists(0)),
            single_execution=True)

if os.environ.get(constants.SAVED_GEN_SCHED,
                  constants.SAVED_GEN_SCHED_DEFAULT_VALUE) != "0":
    @scheduler.task('interval',
                    id=constants.JOB_ST_ID,
                    hours=int(os.environ.get(constants.SAVED_GEN_SCHED,
                                             constants.SAVED_GEN_SCHED_DEFAULT_VALUE)))
    def saved_tracks():
        """saved_tracks task"""
        generator.get_user_saved_tracks(dict({'tracks': []}))


@scheduler.task('interval', id='remove_subsonic_deleted_playlist', hours=12)
def remove_subsonic_deleted_playlist():
    """remove_subsonic_deleted_playlist task"""
    subsonic_helper.remove_subsonic_deleted_playlist()


scheduler.init_app(spotisub)
scheduler.start(paused=(os.environ.get(constants.SCHEDULER_ENABLED,
    constants.SCHEDULER_ENABLED_DEFAULT_VALUE) != "1"))
