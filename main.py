"""Spotisub main module"""
import logging
import os
import random
import threading
import json
from time import strftime

from os.path import dirname
from os.path import join
from dotenv import load_dotenv
from flask import Flask
from flask import Response
from flask import request
from flask import render_template
from flask_restx import Api
from flask_restx import Resource
from flask_apscheduler import APScheduler
from spotisub.core.external.utils.constants import constants
from spotisub.core.external.utils import utils
from spotisub.core import subsonic_helper
from spotisub import generate_playlists
from spotisub.core.exceptions.exceptions import SubsonicOfflineException

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=int(
        os.environ.get(
            constants.LOG_LEVEL,
            constants.LOG_LEVEL_DEFAULT_VALUE)),
    datefmt='%Y-%m-%d %H:%M:%S')

log = logging.getLogger('werkzeug')
log.setLevel(int(os.environ.get(constants.LOG_LEVEL,
             constants.LOG_LEVEL_DEFAULT_VALUE)))

app = Flask(__name__)

scheduler = APScheduler()


@app.after_request
def after_request(response):
    """Excluding healthcheck endpoint from logging"""
    if not request.path.startswith('/utils/healthcheck'):
        timestamp = strftime('[%Y-%b-%d %H:%M]')
        logging.info('%s %s %s %s %s %s',
                     timestamp,
                     request.remote_addr,
                     request.method,
                     request.scheme,
                     request.full_path,
                     response.status)
    return response


api = Api(app)

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


@app.route('/dashboard')
def dashboard():
    """Dashboard path"""
    return render_template('dashboard.html', data=[])


nsgenerate = api.namespace('generate', 'Generate APIs')


@nsgenerate.route('/artist_recommendations/')
@nsgenerate.route('/artist_recommendations/<string:artist_name>/')
class ArtistRecommendationsClass(Resource):
    """Artist reccomendations class"""
    def get(self, artist_name=None):
        """Artist reccomendations endpoint"""
        try:
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
                    target=lambda: generate_playlists
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
                    "Unable to communicate with Subsonic",
                    False),
                400)


@nsgenerate.route('/artist_recommendations/all/')
class ArtistRecommendationsAllClass(Resource):
    """All Artists reccomendations class"""
    def get(self):
        """All Artists reccomendations endpoint"""
        try:
            subsonic_helper.check_pysonic_connection()
            threading.Thread(
                target=lambda: generate_playlists
                    .all_artists_recommendations(subsonic_helper
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
                    "Unable to communicate with Subsonic",
                    False),
                400)


@nsgenerate.route('/artist_top_tracks/')
@nsgenerate.route('/artist_top_tracks/<string:artist_name>/')
class ArtistTopTracksClass(Resource):
    """Artist top tracks class"""
    def get(self, artist_name=None):
        """Artist top tracks endpoint"""
        try:
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
                    target=lambda: generate_playlists.artist_top_tracks(artist_name)).start()
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
                    "Unable to communicate with Subsonic",
                    False),
                400)


@nsgenerate.route('/artist_top_tracks/all/')
class ArtistTopTracksAllClass(Resource):
    """All Artists top tracks class"""
    def get(self):
        """All Artists top tracks endpoint"""
        try:
            subsonic_helper.check_pysonic_connection()
            threading.Thread(
                target=lambda: generate_playlists
                    .all_artists_top_tracks(subsonic_helper
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
                    "Unable to communicate with Subsonic",
                    False),
                400)

@nsgenerate.route('/recommendations')
class RecommendationsClass(Resource):
    """Recommendations class"""
    def get(self):
        """Recommendations endpoint"""
        try:
            subsonic_helper.check_pysonic_connection()
            threading.Thread(
                target=lambda: generate_playlists.my_recommendations(
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
                    "Unable to communicate with Subsonic",
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
            subsonic_helper.check_pysonic_connection()
            if playlist_name is None:
                count = generate_playlists.count_user_playlists(0)
                threading.Thread(
                    target=lambda: generate_playlists.get_user_playlists(
                        random.randrange(count),
                        single_execution=True)).start()
                return get_response_json(get_json_message(
                    "Importing a random playlist", True), 200)
            search_result_name = generate_playlists.get_user_playlist_by_name(
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
                threading.Thread(target=lambda: generate_playlists.get_user_playlists(
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
                    "Unable to communicate with Subsonic",
                    False),
                400)


@nsimport.route('/user_playlist/all/')
class UserPlaylistsAllClass(Resource):
    """All User playlists class"""
    def get(self):
        """All User playlists endpoint"""
        try:
            subsonic_helper.check_pysonic_connection()
            threading.Thread(
                target=lambda: generate_playlists.get_user_playlists(0)).start()
            return get_response_json(
                get_json_message(
                    "Importing all your spotify playlists",
                    True),
                200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic",
                    False),
                400)


@nsimport.route('/saved_tracks')
class SavedTracksClass(Resource):
    """Saved tracks class"""
    def get(self):
        """Saved tracks endpoint"""
        try:
            subsonic_helper.check_pysonic_connection()
            threading.Thread(
                target=lambda: generate_playlists
                    .get_user_saved_tracks(dict({'tracks': []}))).start()
            return get_response_json(get_json_message(
                "Importing your saved tracks", True), 200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic",
                    False),
                400)


nsdatabase = api.namespace('database', 'Database APIs')


@nsdatabase.route('/playlist/unmatched')
class PlaylistUnmatchedClass(Resource):
    """Unmatched playlist songs class"""
    def get(self):
        """Unmatched playlist songs endpoint"""
        try:
            subsonic_helper.check_pysonic_connection()
            missing_songs = subsonic_helper.get_playlist_songs(
                missing_only=True)
            return get_response_json(json.dumps(missing_songs), 200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic",
                    False),
                400)


nsdatabase = api.namespace('database', 'Database APIs')


@nsdatabase.route('/playlist/all')
class PlaylistAllClass(Resource):
    """All playlist songs class"""
    def get(self):
        """All playlist songs endpoint"""
        try:
            subsonic_helper.check_pysonic_connection()
            missing_songs = subsonic_helper.get_playlist_songs(
                missing_only=False)
            return get_response_json(json.dumps(missing_songs), 200)
        except SubsonicOfflineException:
            utils.write_exception()
            return get_response_json(
                get_json_message(
                    "Unable to communicate with Subsonic",
                    False),
                400)


nsutils = api.namespace('utils', 'Utils APIs')


@nsutils.route('/healthcheck')
class Healthcheck(Resource):
    """Healthcheck class"""
    def get(self):
        """Healthcheck endpoint"""
        return "Ok!"


if os.environ.get(constants.SCHEDULER_ENABLED,
                  constants.SCHEDULER_ENABLED_DEFAULT_VALUE) == "1":

    if os.environ.get(constants.ARTIST_GEN_SCHED,
                      constants.ARTIST_GEN_SCHED_DEFAULT_VALUE) != "0":
        @scheduler.task('interval',
                        id='artist_recommendations',
                        hours=int(os.environ.get(constants.ARTIST_GEN_SCHED,
                                                 constants.ARTIST_GEN_SCHED_DEFAULT_VALUE)))
        def artist_recommendations():
            """artist_recommendations task"""
            generate_playlists.show_recommendations_for_artist(
                random.choice(subsonic_helper.get_artists_array_names()))

    if os.environ.get(constants.ARTIST_TOP_GEN_SCHED,
                      constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE) != "0":
        @scheduler.task('interval',
                        id='artist_top_tracks',
                        hours=int(os.environ.get(constants.ARTIST_TOP_GEN_SCHED,
                                                 constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE)))
        def artist_top_tracks():
            """artist_top_tracks task"""
            generate_playlists.artist_top_tracks(
                random.choice(subsonic_helper.get_artists_array_names()))

    if os.environ.get(constants.RECOMEND_GEN_SCHED,
                      constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE) != "0":
        @scheduler.task('interval',
                        id='my_recommendations',
                        hours=int(os.environ.get(constants.RECOMEND_GEN_SCHED,
                                                 constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE)))
        def my_recommendations():
            """my_recommendations task"""
            generate_playlists.my_recommendations(count=random.randrange(int(os.environ.get(
                constants.NUM_USER_PLAYLISTS, constants.NUM_USER_PLAYLISTS_DEFAULT_VALUE))))

    if os.environ.get(constants.PLAYLIST_GEN_SCHED,
                      constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE) != "0":
        @scheduler.task('interval',
                        id='user_playlists',
                        hours=int(os.environ.get(constants.PLAYLIST_GEN_SCHED,
                                                 constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE)))
        def user_playlists():
            """user_playlists task"""
            generate_playlists.get_user_playlists(
                random.randrange(
                    generate_playlists.count_user_playlists(0)),
                single_execution=True)

    if os.environ.get(constants.SAVED_GEN_SCHED,
                      constants.SAVED_GEN_SCHED_DEFAULT_VALUE) != "0":
        @scheduler.task('interval',
                        id='saved_tracks',
                        hours=int(os.environ.get(constants.SAVED_GEN_SCHED,
                                                 constants.SAVED_GEN_SCHED_DEFAULT_VALUE)))
        def saved_tracks():
            """saved_tracks task"""
            generate_playlists.get_user_saved_tracks(dict({'tracks': []}))


@scheduler.task('interval', id='remove_subsonic_deleted_playlist', hours=12)
def remove_subsonic_deleted_playlist():
    """remove_subsonic_deleted_playlist task"""
    subsonic_helper.remove_subsonic_deleted_playlist()


scheduler.init_app(app)
scheduler.start()

utils.print_logo(constants.VERSION)

if __name__ == '__main__':
    app.run()
