import os
import sys
import logging
import random
import generate_playlists
import threading
from flask import Flask, request, Response, make_response, after_this_request, g
from os.path import join, dirname
from dotenv import load_dotenv
from time import strftime
from flask_restx import Api, Resource
from flask_apscheduler import APScheduler

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)



if os.environ.get("LOG_LEVEL") is None:
  os.environ["LOG_LEVEL"] = "40"
if os.environ.get("NUM_USER_PLAYLISTS") is None:
  os.environ["NUM_USER_PLAYLISTS"] = "5"
if os.environ.get("ARTIST_GEN_SCHED") is None:
  os.environ["ARTIST_GEN_SCHED"] = "1"
if os.environ.get("RECCOMEND_GEN_SCHED") is None:
  os.environ["RECCOMEND_GEN_SCHED"] = "4"
if os.environ.get("PLAYLIST_GEN_SCHED") is None:
  os.environ["PLAYLIST_GEN_SCHED"] = "2"


scheduler = APScheduler()
generate_playlists.print_logo()

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=int(os.environ.get("LOG_LEVEL")),
        datefmt='%Y-%m-%d %H:%M:%S')

log = logging.getLogger('werkzeug')
log.setLevel(int(os.environ.get("LOG_LEVEL")))

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

nsgenerate = api.namespace('generate', 'Generate APIs')

@nsgenerate.route('/artist_reccomendations/')
@nsgenerate.route('/artist_reccomendations/<string:artist_name>/')
class ArtistReccomendationsClass(Resource):
  def post (self, artist_name = None):
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



@nsgenerate.route('/all_artists_reccomendations')
class ArtistReccomendationsClass(Resource):
  def post (self, artist_name = None):
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
  def post (self):
    try:
        threading.Thread(target=lambda: generate_playlists.my_reccommendations(count=random.randrange(int(os.environ.get("NUM_USER_PLAYLISTS"))))).start()
        return get_response_str("Generating a reccomendation playlist", 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)

@nsgenerate.route('/user_playlist')
class UserPlaylistsClass(Resource):
  def post (self):
    try:
        threading.Thread(target=lambda: generate_playlists.get_user_playlists(random.randrange(100), single_execution = True)).start()
        return get_response_str("Importing a random playlist", 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)

@nsgenerate.route('/all_user_playlists')
class AllPlaylistsClass(Resource):
  def post (self):
    try:
        threading.Thread(target=lambda: generate_playlists.get_user_playlists(0)).start()
        return get_response_str("Importing a all your spotify playlists", 200)  
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

@scheduler.task('interval', id='artist_reccomendations', hours=int(os.environ.get("ARTIST_GEN_SCHED")))
def artist_reccomendations():
    generate_playlists.show_recommendations_for_artist(random.choice(generate_playlists.get_artists_array_names()))

@scheduler.task('interval', id='my_reccommendations', hours=int(os.environ.get("RECCOMEND_GEN_SCHED")))
def my_reccommendations():
    generate_playlists.my_reccommendations(count=random.randrange(int(os.environ.get("PLAYLIST_GEN_SCHED"))))

@scheduler.task('interval', id='user_playlists', hours=6)
def user_playlists():
    generate_playlists.get_user_playlists(random.randrange(100), single_execution = True)


scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
  app.run()