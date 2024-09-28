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
@spotisub.route('/overview/')
@spotisub.route('/overview/<int:page>/')
@spotisub.route('/overview/<int:page>/<int:limit>/')
@spotisub.route('/overview/<int:page>/<int:limit>/<string:order>/')
@spotisub.route('/overview/<int:page>/<int:limit>/<string:order>/<int:asc>/')
@login_required
def overview(page=1, limit=25, order='subsonic_spotify_relation.subsonic_playlist_name', asc=1):
    title = 'Overview'
    try:
        all_playlists, song_count = subsonic_helper.select_all_playlists(
            page=page - 1, limit=limit, order=order, asc=(asc == 1))
        total_pages = math.ceil(song_count / limit)
        pagination_array, prev_page, next_page = utils.get_pagination(
            page, total_pages)
        sorting_dict = {}
        sorting_dict["Playlist Name"] = "subsonic_spotify_relation.subsonic_playlist_name"
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
    except SubsonicOfflineException:
        return render_template('errors/404.html',
                               title=title,
                               errors=["Unable to communicate with Subsonic.", "Please check your configuration and make sure your instance is online."])
    except (SpotifyException, SpotifyApiException) as e:
        return render_template('errors/404.html',
                               title=title,
                               errors=["Unable to communicate with Spotify.", "Please check your configuration."])

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
    try:
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
        sorting_dict["Playlist Name"] = "subsonic_spotify_relation.subsonic_playlist_name"


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
    except SubsonicOfflineException:
        return render_template('errors/404.html',
                               title=title,
                               errors=["Unable to communicate with Subsonic.", "Please check your configuration and make sure your instance is online."])
    except (SpotifyException, SpotifyApiException) as e:
        return render_template('errors/404.html',
                               title=title,
                               errors=["Unable to communicate with Spotify.", "Please check your configuration."])

@spotisub.route('/song/<string:uuid>/')
@spotisub.route('/song/<string:uuid>/<int:page>/')
@spotisub.route('/song/<string:uuid>/<int:page>/<int:limit>/')
@spotisub.route('/song/<string:uuid>/<int:page>/<int:limit>/<string:order>/')
@spotisub.route('/song/<string:uuid>/<int:page>/<int:limit>/<string:order>/<int:asc>/')
@login_required
def song(uuid=None, page=1, limit=25, order='spotify_song.title', asc=1):
    title = 'Song'
    try:
        spotipy_helper.get_secrets()
        song1, songs, song_count = subsonic_helper.load_song(
            uuid, spotipy_helper, page=page-1, limit=limit, order=order, asc=(asc == 1))
        total_pages = math.ceil(song_count / limit)
        pagination_array, prev_page, next_page = utils.get_pagination(
            page, total_pages)

        
        sorting_dict = {}
        sorting_dict["Status"] = "subsonic_spotify_relation.subsonic_song_id"
        sorting_dict["Spotify Song Title"] = "spotify_song.title"
        sorting_dict["Spotify Artist"] = "spotify_artist.name"
        sorting_dict["Spotify Album"] = "spotify_album.name"
        sorting_dict["Playlist Name"] = "subsonic_spotify_relation.subsonic_playlist_name"

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
    except SubsonicOfflineException:
        return render_template('errors/404.html',
                               title=title,
                               errors=["Unable to communicate with Subsonic.", "Please check your configuration and make sure your instance is online."])
    except (SpotifyException, SpotifyApiException) as e:
        return render_template('errors/404.html',
                               title=title,
                               errors=["Unable to communicate with Spotify.", "Please check your configuration."])

@spotisub.route('/album/<string:uuid>/')
@spotisub.route('/album/<string:uuid>/<int:page>/')
@spotisub.route('/album/<string:uuid>/<int:page>/<int:limit>/')
@spotisub.route('/album/<string:uuid>/<int:page>/<int:limit>/<string:order>/')
@spotisub.route('/album/<string:uuid>/<int:page>/<int:limit>/<string:order>/<int:asc>/')
@login_required
def album(uuid=None, page=1, limit=25, order='spotify_song.title', asc=1):
    title = 'Album'
    try:
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
        sorting_dict["Playlist Name"] = "subsonic_spotify_relation.subsonic_playlist_name"
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
    except SubsonicOfflineException:
        return render_template('errors/404.html',
                               title=title,
                               errors=["Unable to communicate with Subsonic.", "Please check your configuration and make sure your instance is online."])
    except (SpotifyException, SpotifyApiException) as e:
        return render_template('errors/404.html',
                               title=title,
                               errors=["Unable to communicate with Spotify.", "Please check your configuration."])


@spotisub.route('/artist/<string:uuid>/')
@spotisub.route('/artist/<string:uuid>/<int:page>/')
@spotisub.route('/artist/<string:uuid>/<int:page>/<int:limit>/')
@spotisub.route('/artist/<string:uuid>/<int:page>/<int:limit>/<string:order>/')
@spotisub.route('/artist/<string:uuid>/<int:page>/<int:limit>/<string:order>/<int:asc>/')
@login_required
def artist(uuid=None, page=1, limit=25, order='spotify_song.title', asc=1):
    title = 'Artist'
    try:
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
        sorting_dict["Playlist Name"] = "subsonic_spotify_relation.subsonic_playlist_name"
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
    except SubsonicOfflineException:
        return render_template('errors/404.html',
                               title=title,
                               errors=["Unable to communicate with Subsonic.", "Please check your configuration and make sure your instance is online."])
    except (SpotifyException, SpotifyApiException) as e:
        return render_template('errors/404.html',
                               title=title,
                               errors=["Unable to communicate with Spotify.", "Please check your configuration."])

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
        try:
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
                    "Generating a random artiist recommendations playlist",
                    True),
                200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except (SpotifyException, SpotifyApiException) as e:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Spotify API Error. Please check your configuruation.",
                    False),
                400)


@nsgenerate.route('/artist_top_tracks')
class ArtistTopTracksClass(Resource):
    """Artist top tracks class"""

    def get(self):
        """Artist top tracks endpoint"""
        try:
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
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except (SpotifyException, SpotifyApiException) as e:
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
                target=lambda: scheduler
                    .run_job(constants.JOB_MR_ID)).start()
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
        except (SpotifyException, SpotifyApiException) as e:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Spotify API Error. Please check your configuruation.",
                    False),
                400)


nsimport = api.namespace('import', 'Generate APIs')


@nsimport.route('/user_playlist')
class UserPlaylistsClass(Resource):
    """User playlists class"""

    def get(self):
        """User playlists endpoint"""
        try:
            spotipy_helper.get_secrets()
            subsonic_helper.check_pysonic_connection()
            count = generator.count_user_playlists(0)
            threading.Thread(
                target=lambda: scheduler
                    .run_job(constants.JOB_UP_ID)).start()
            return get_response_json(get_json_message(
                "Importing a random playlist", True), 200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except (SpotifyException, SpotifyApiException) as e:
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
                target=lambda: scheduler
                    .run_job(constants.JOB_ST_ID)).start()
            return get_response_json(get_json_message(
                "Importing your saved tracks", True), 200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic.",
                    False),
                400)
        except (SpotifyException, SpotifyApiException) as e:
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