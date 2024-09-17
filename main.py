import logging
import os
import random
import sys
import threading
import json

from dotenv import load_dotenv
from flask import Flask
from flask import Response
from flask import after_this_request
from flask import g
from flask import make_response
from flask import request
from flask import render_template
from flask_restx import Api
from flask_restx import Resource
from os.path import dirname
from os.path import join
from time import strftime
from subtify.constants import constants
from subtify.utils import utils
from subtify.helpers import subsonic_helper
from subtify.helpers import generate_playlists
from flask_apscheduler import APScheduler
from subtify.exceptions.exceptions import SubsonicOfflineException

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=int(os.environ.get(constants.LOG_LEVEL, constants.LOG_LEVEL_DEFAULT_VALUE)),
        datefmt='%Y-%m-%d %H:%M:%S')

log = logging.getLogger('werkzeug')
log.setLevel(int(os.environ.get(constants.LOG_LEVEL, constants.LOG_LEVEL_DEFAULT_VALUE)))

app = Flask(__name__)

scheduler = APScheduler()

@app.after_request
def after_request(response):
  if not request.path.startswith('/utils/healthcheck'):
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    logging.info('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status)
  return response

api = Api(app)

def get_response_json(data, status):
  r = Response(response=data, status=status, mimetype="application/json")
  r.headers["Content-Type"] = "application/json; charset=utf-8"
  r.headers["Accept"] = "application/json"
  return r

def get_json_message(message, is_ok):
  data = {
    "status": "ko" if is_ok is False else "ok",
    "message": message,
  }
  return json.dumps(data)

@app.route('/dashboard')
def dashboard():
  return render_template('dashboard.html', data=[])

nsgenerate = api.namespace('generate', 'Generate APIs')

@nsgenerate.route('/artist_recommendations/')
@nsgenerate.route('/artist_recommendations/<string:artist_name>/')
class ArtistRecommendationsClass(Resource):
  def get (self, artist_name = None):
    try:
      subsonic_helper.checkPysonicConnection()
      if artist_name is None:
        artist_name = random.choice(subsonic_helper.get_artists_array_names())
      threading.Thread(target=lambda: generate_playlists.show_recommendations_for_artist(artist_name)).start()
      return get_response_json(get_json_message("Generating recommendations playlist for artist " + artist_name, True), 200)  
    except SubsonicOfflineException:
      utils.write_exception()
      return get_response_json(get_json_message("Your Subsonic instance is Offline", False), 400) 
    except Exception as e:
      utils.write_exception()
      g.request_error = str(e)

@nsgenerate.route('/artist_recommendations/all/')
class ArtistRecommendationsAllClass(Resource):
  def get (self, artist_name = None):
    try:
      subsonic_helper.checkPysonicConnection()
      threading.Thread(target=lambda: generate_playlists.all_artists_recommendations()).start()
      return get_response_json(get_json_message("Generating recommendations playlist for all artists", True), 200)
    except SubsonicOfflineException:
      utils.write_exception()
      return get_response_json(get_json_message("Your Subsonic instance is Offline", False), 400) 
    except Exception as e:
      utils.write_exception()
      g.request_error = str(e)

@nsgenerate.route('/artist_top_tracks/')
@nsgenerate.route('/artist_top_tracks/<string:artist_name>/')
class ArtistTopTracksClass(Resource):
  def get (self, artist_name = None):
    try:
      subsonic_helper.checkPysonicConnection()
      if artist_name is None:
        artist_name = random.choice(subsonic_helper.get_artists_array_names())
      threading.Thread(target=lambda: generate_playlists.artist_top_tracks(artist_name)).start()
      return get_response_json(get_json_message("Generating top tracks playlist for artist " + artist_name, True), 200)  
    except SubsonicOfflineException:
      utils.write_exception()
      return get_response_json(get_json_message("Your Subsonic instance is Offline", False), 400) 
    except Exception as e:
      utils.write_exception()
      g.request_error = str(e)

@nsgenerate.route('/artist_top_tracks/all/')
class ArtistTopTracksAllClass(Resource):
  def get (self, artist_name = None):
    try:
      subsonic_helper.checkPysonicConnection()
      threading.Thread(target=lambda: generate_playlists.all_artists_top_tracks()).start()
      return get_response_json(get_json_message("Generating top tracks playlist for all artists", True), 200)  
    except SubsonicOfflineException:
      utils.write_exception()
      return get_response_json(get_json_message("Your Subsonic instance is Offline", False), 400) 
    except Exception as e:
      utils.write_exception()
      g.request_error = str(e)

@nsgenerate.route('/recommendations')
class RecommendationsClass(Resource):
  def get (self):
    try:
      subsonic_helper.checkPysonicConnection()
      threading.Thread(target=lambda: generate_playlists.my_recommendations(count=random.randrange(int(os.environ.get(constants.NUM_USER_PLAYLISTS, constants.NUM_USER_PLAYLISTS_DEFAULT_VALUE))))).start()
      return get_response_json(get_json_message("Generating a reccommendation playlist", True), 200)  
    except SubsonicOfflineException:
      utils.write_exception()
      return get_response_json(get_json_message("Your Subsonic instance is Offline", False), 400) 
    except Exception as e:
      utils.write_exception()
      g.request_error = str(e)


nsimport = api.namespace('import', 'Generate APIs')

@nsimport.route('/user_playlist/')
@nsimport.route('/user_playlist/<string:playlist_name>/')
class UserPlaylistsClass(Resource):
  def get (self, playlist_name = None):
    try:
      subsonic_helper.checkPysonicConnection()
      if playlist_name is None:
        count = generate_playlists.count_user_playlists(0)
        threading.Thread(target=lambda: generate_playlists.get_user_playlists(random.randrange(count), single_execution = True)).start()
        return get_response_json(get_json_message("Importing a random playlist", True), 200)  
      else:
        threading.Thread(target=lambda: generate_playlists.get_user_playlists(0, single_execution = False, playlist_name = playlist_name)).start()
        return get_response_json(get_json_message("Searching and importing your spotify account for playlist " + playlist_name, True), 200)  
    except SubsonicOfflineException:
      utils.write_exception()
      return get_response_json(get_json_message("Your Subsonic instance is Offline", False), 400) 
    except Exception as e:
      utils.write_exception()
      g.request_error = str(e)
@nsimport.route('/user_playlist/all/')
class UserPlaylistsAllClass(Resource):
  def get (self, playlist_name = None):
    try:
      subsonic_helper.checkPysonicConnection()
      threading.Thread(target=lambda: generate_playlists.get_user_playlists(0)).start()
      return get_response_json(get_json_message("Importing all your spotify playlists", True), 200)  
    except SubsonicOfflineException:
      utils.write_exception()
      return get_response_json(get_json_message("Your Subsonic instance is Offline", False), 400) 
    except Exception as e:
      utils.write_exception()
      g.request_error = str(e)

@nsimport.route('/saved_tracks')
class SavedTracksClass(Resource):
  def get (self):
    try:
      subsonic_helper.checkPysonicConnection()
      threading.Thread(target=lambda: generate_playlists.get_user_saved_tracks()).start()
      return get_response_json(get_json_message("Importing your saved tracks", True), 200)  
    except SubsonicOfflineException:
      utils.write_exception()
      return get_response_json(get_json_message("Your Subsonic instance is Offline", False), 400) 
    except Exception as e:
      utils.write_exception()
      g.request_error = str(e)

nsdatabase = api.namespace('database', 'Database APIs')
@nsdatabase.route('/unmatched_songs')
class UnmatchedSongsClass(Resource):
  def get (self):
    try:
      subsonic_helper.checkPysonicConnection()
      missing_songs = subsonic_helper.get_playlist_songs(missing=True)
      return get_response_json(json.dumps(missing_songs), 200)   
    except SubsonicOfflineException:
      utils.write_exception()
      return get_response_json(get_json_message("Your Subsonic instance is Offline", False), 400) 
    except Exception as e:
      utils.write_exception()
      g.request_error = str(e)


nsutils = api.namespace('utils', 'Utils APIs')

@nsutils.route('/healthcheck')
class Healthcheck(Resource):
  def get (self):
    return "Ok!"

if os.environ.get(constants.SCHEDULER_ENABLED, constants.SCHEDULER_ENABLED_DEFAULT_VALUE) == "1":

  if os.environ.get(constants.ARTIST_GEN_SCHED, constants.ARTIST_GEN_SCHED_DEFAULT_VALUE) != "0":
    @scheduler.task('interval', id='artist_recommendations', hours=int(os.environ.get(constants.ARTIST_GEN_SCHED, constants.ARTIST_GEN_SCHED_DEFAULT_VALUE)))
    def artist_recommendations():
      generate_playlists.show_recommendations_for_artist(random.choice(subsonic_helper.get_artists_array_names()))

  if os.environ.get(constants.ARTIST_TOP_GEN_SCHED, constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE) != "0":
    @scheduler.task('interval', id='artist_top_tracks', hours=int(os.environ.get(constants.ARTIST_TOP_GEN_SCHED, constants.ARTIST_TOP_GEN_SCHED_DEFAULT_VALUE)))
    def artist_top_tracks():
      generate_playlists.artist_top_tracks(random.choice(subsonic_helper.get_artists_array_names()))

  if os.environ.get(constants.RECOMEND_GEN_SCHED, constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE) != "0":
    @scheduler.task('interval', id='my_recommendations', hours=int(os.environ.get(constants.RECOMEND_GEN_SCHED, constants.RECOMEND_GEN_SCHED_DEFAULT_VALUE)))
    def my_recommendations():
      generate_playlists.my_recommendations(count=random.randrange(int(os.environ.get(constants.NUM_USER_PLAYLISTS, constants.NUM_USER_PLAYLISTS_DEFAULT_VALUE))))

  if os.environ.get(constants.PLAYLIST_GEN_SCHED, constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE) != "0":
    @scheduler.task('interval', id='user_playlists', hours=int(os.environ.get(constants.PLAYLIST_GEN_SCHED, constants.PLAYLIST_GEN_SCHED_DEFAULT_VALUE)))
    def user_playlists():
      generate_playlists.get_user_playlists(random.randrange(generate_playlists.count_user_playlists(0)), single_execution = True)

  if os.environ.get(constants.SAVED_GEN_SCHED, constants.SAVED_GEN_SCHED_DEFAULT_VALUE) != "0":
    @scheduler.task('interval', id='saved_tracks', hours=int(os.environ.get(constants.SAVED_GEN_SCHED, constants.SAVED_GEN_SCHED_DEFAULT_VALUE)))
    def saved_tracks():
      generate_playlists.get_user_saved_tracks()

@scheduler.task('interval', id='remove_subsonic_deleted_playlist', hours=1)
def remove_subsonic_deleted_playlist():
  subsonic_helper.remove_subsonic_deleted_playlist()

scheduler.init_app(app)
scheduler.start()


utils.print_logo(constants.VERSION)

if __name__ == '__main__':
  app.run()