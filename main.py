import generate_playlists
import logging
import os
import random
import sys
import threading

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

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

generate_playlists.print_logo()

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=int(os.environ.get("LOG_LEVEL", "40")),
        datefmt='%Y-%m-%d %H:%M:%S')

log = logging.getLogger('werkzeug')
log.setLevel(int(os.environ.get("LOG_LEVEL", "40")))

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

@nsgenerate.route('/artist_reccomendations/')
@nsgenerate.route('/artist_reccomendations/<string:artist_name>/')
class ArtistReccomendationsClass(Resource):
  def get (self, artist_name = None):
    try:
      if artist_name is None:
        artist_name = random.choice(generate_playlists.get_artists_array_names())
      threading.Thread(target=lambda: generate_playlists.show_recommendations_for_artist(artist_name)).start()
      return get_response_str("Generating reccomendations playlist for artist " + artist_name, 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)

@nsgenerate.route('/artist_reccomendations/all/')
class ArtistReccomendationsAllClass(Resource):
  def get (self, artist_name = None):
    try:
      threading.Thread(target=lambda: generate_playlists.all_artists_recommendations()).start()
      return get_response_str("Generating reccomendations playlist for all artists", 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)

@nsgenerate.route('/reccomendations')
class ReccomendationsClass(Resource):
  def get (self):
    try:
        threading.Thread(target=lambda: generate_playlists.my_reccommendations(count=random.randrange(int(os.environ.get("NUM_USER_PLAYLISTS", "5"))))).start()
        return get_response_str("Generating a reccomendation playlist", 200)  
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

nsutils = api.namespace('utils', 'Utils APIs')

@nsutils.route('/healthcheck')
class Healthcheck(Resource):
  def get (self):
    return "Ok!"

if os.environ.get("SCHEDULER_ENABLED", "1") == "1":

  from flask_apscheduler import APScheduler

  scheduler = APScheduler()

  if os.environ.get("ARTIST_GEN_SCHED", "1") != "0":
    @scheduler.task('interval', id='artist_reccomendations', hours=int(os.environ.get("ARTIST_GEN_SCHED", "1")))
    def artist_reccomendations():
      generate_playlists.show_recommendations_for_artist(random.choice(generate_playlists.get_artists_array_names()))

  if os.environ.get("RECCOMEND_GEN_SCHED", "1") != "0":
    @scheduler.task('interval', id='my_reccommendations', hours=int(os.environ.get("RECCOMEND_GEN_SCHED", "4")))
    def my_reccommendations():
      generate_playlists.my_reccommendations(count=random.randrange(int(os.environ.get("NUM_USER_PLAYLISTS","5"))))

  if os.environ.get("PLAYLIST_GEN_SCHED", "1") != "0":
    @scheduler.task('interval', id='user_playlists', hours=int(os.environ.get("PLAYLIST_GEN_SCHED","3")))
    def user_playlists():
      count = generate_playlists.count_user_playlists(0)
      generate_playlists.get_user_playlists(random.randrange(count), single_execution = True)

  if os.environ.get("SAVED_GEN_SCHED", "1") != "0":
    @scheduler.task('interval', id='saved_tracks', hours=int(os.environ.get("SAVED_GEN_SCHED","2")))
    def saved_tracks():
      generate_playlists.get_user_saved_tracks()


  scheduler.init_app(app)
  scheduler.start()

if __name__ == '__main__':
  app.run()