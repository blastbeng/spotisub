import generate_playlists
import logging
import os
import random
import sys
import threading
import utils

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
import constants

import subsonic_helper

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=int(os.environ.get(constants.LOG_LEVEL, constants.LOG_LEVEL_DEFAULT_VALUE)),
        datefmt='%Y-%m-%d %H:%M:%S')

log = logging.getLogger('werkzeug')
log.setLevel(int(os.environ.get(constants.LOG_LEVEL, constants.LOG_LEVEL_DEFAULT_VALUE)))

app = Flask(__name__)

@app.after_request
def after_request(response):
  if not request.path.startswith('/utils/healthcheck'):
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    logging.info('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status)
  return response

api = Api(app)

def get_response_str(text: str, status):
  r = Response(response=text, status=status, mimetype="text/xml")
  r.headers["Content-Type"] = "text/xml; charset=utf-8"
  return r



@app.route('/dashboard')
def dashboard():
  return render_template('dashboard.html', data=[])

nsgenerate = api.namespace('generate', 'Generate APIs')

@nsgenerate.route('/artist_recommendations/')
@nsgenerate.route('/artist_recommendations/<string:artist_name>/')
class ArtistRecommendationsClass(Resource):
  def get (self, artist_name = None):
    try:
      if artist_name is None:
        artist_name = random.choice(subsonic_helper.get_artists_array_names())
      threading.Thread(target=lambda: generate_playlists.show_recommendations_for_artist(artist_name)).start()
      return get_response_str("Generating recommendations playlist for artist " + artist_name, 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)

@nsgenerate.route('/artist_recommendations/all/')
class ArtistRecommendationsAllClass(Resource):
  def get (self, artist_name = None):
    try:
      threading.Thread(target=lambda: generate_playlists.all_artists_recommendations()).start()
      return get_response_str("Generating recommendations playlist for all artists", 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)

@nsgenerate.route('/artist_top_tracks/')
@nsgenerate.route('/artist_top_tracks/<string:artist_name>/')
class ArtistTopTracksClass(Resource):
  def get (self, artist_name = None):
    try:
      if artist_name is None:
        artist_name = random.choice(subsonic_helper.get_artists_array_names())
      threading.Thread(target=lambda: generate_playlists.artist_top_tracks(artist_name)).start()
      return get_response_str("Generating top tracks playlist for artist " + artist_name, 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)

@nsgenerate.route('/artist_top_tracks/all/')
class ArtistTopTracksAllClass(Resource):
  def get (self, artist_name = None):
    try:
      threading.Thread(target=lambda: generate_playlists.all_artists_top_tracks()).start()
      return get_response_str("Generating top tracks playlist for all artists", 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)

@nsgenerate.route('/recommendations')
class RecommendationsClass(Resource):
  def get (self):
    try:
        threading.Thread(target=lambda: generate_playlists.my_recommendations(count=random.randrange(int(os.environ.get(constants.NUM_USER_PLAYLISTS, constants.NUM_USER_PLAYLISTS_DEFAULT_VALUE))))).start()
        return get_response_str("Generating a reccommendation playlist", 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)


nsimport = api.namespace('import', 'Generate APIs')

@nsimport.route('/user_playlist/')
@nsimport.route('/user_playlist/<string:playlist_name>/')
class UserPlaylistsClass(Resource):
  def get (self, playlist_name = None):
    try:
        if playlist_name is None:
          count = generate_playlists.count_user_playlists(0)
          threading.Thread(target=lambda: generate_playlists.get_user_playlists(random.randrange(count), single_execution = True)).start()
          return get_response_str("Importing a random playlist", 200)  
        else:
          threading.Thread(target=lambda: generate_playlists.get_user_playlists(0, single_execution = False, playlist_name = playlist_name)).start()
          return get_response_str("Searching and importing your spotify account for playlist " + playlist_name, 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)

@nsimport.route('/user_playlist/all/')
class UserPlaylistsAllClass(Resource):
  def get (self, playlist_name = None):
    try:
      threading.Thread(target=lambda: generate_playlists.get_user_playlists(0)).start()
      return get_response_str("Importing all your spotify playlists", 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)

@nsimport.route('/saved_tracks')
class SavedTracksClass(Resource):
  def get (self):
    try:
        threading.Thread(target=lambda: generate_playlists.get_user_saved_tracks()).start()
        return get_response_str("Importing your saved tracks", 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)

nsdatabase = api.namespace('database', 'Database APIs')
@nsdatabase.route('/unmatched_songs')
class UnmatchedSongsClass(Resource):
  def get (self):
    try:
      data = {
        "status": "TODO",
      }
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)


nsutils = api.namespace('utils', 'Utils APIs')

@nsutils.route('/healthcheck')
class Healthcheck(Resource):
  def get (self):
    return "Ok!"

if os.environ.get(constants.SCHEDULER_ENABLED, constants.SCHEDULER_ENABLED_DEFAULT_VALUE) == "1":

  from flask_apscheduler import APScheduler

  scheduler = APScheduler()

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
      count = generate_playlists.count_user_playlists(0)
      generate_playlists.get_user_playlists(random.randrange(count), single_execution = True)

  if os.environ.get(constants.SAVED_GEN_SCHED, constants.SAVED_GEN_SCHED_DEFAULT_VALUE) != "0":
    @scheduler.task('interval', id='saved_tracks', hours=int(os.environ.get(constants.SAVED_GEN_SCHED, constants.SAVED_GEN_SCHED_DEFAULT_VALUE)))
    def saved_tracks():
      generate_playlists.get_user_saved_tracks()


  scheduler.init_app(app)
  scheduler.start()


utils.print_logo(constants.VERSION)

if __name__ == '__main__':
  app.run()