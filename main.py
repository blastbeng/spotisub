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

scheduler = APScheduler()
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

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

nsvoice = api.namespace('generate', 'Generate APIs')

@nsvoice.route('/artist_reccomendations/')
@nsvoice.route('/artist_reccomendations/<string:artist_name>/')
class ArtistReccomendationsClass(Resource):
  def post (self, artist_name = None):
    try:
        threading.Thread(target=lambda: generate_playlists.show_recommendations_for_artist(random.choice(get_artists_array_names()))).start()
        return get_response_str("Generating playlist for artist " + artist_name, 200)  
    except Exception as e:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
      g.request_error = str(e)

@nsvoice.route('/reccomendations')
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

@nsvoice.route('/user_playlists')
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

nsutils = api.namespace('utils', 'Utils APIs')

@nsutils.route('/healthcheck')
class Healthcheck(Resource):
  def get (self):
    return "Ok!"

@scheduler.task('interval', id='artist_reccomendations', hours=2)
def artist_reccomendations():
    if os.path.isdir(music_dir) and len(os.listdir(music_dir)) > 0:
        generate_playlists.show_recommendations_for_artist(random.choice(os.listdir(music_dir)))

@scheduler.task('interval', id='my_reccommendations', hours=6)
def my_reccommendations():
    if os.path.isdir(music_dir) and len(os.listdir(music_dir)) > 0:
        generate_playlists.my_reccommendations(count=random.randrange(int(os.environ.get("NUM_USER_PLAYLISTS"))))

@scheduler.task('interval', id='user_playlists', hours=6)
def user_playlists():
    if os.path.isdir(music_dir) and len(os.listdir(music_dir)) > 0:
        generate_playlists.get_user_playlists(random.randrange(100), single_execution = True)


scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
  app.run()