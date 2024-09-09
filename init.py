import spotipy  
import os
from spotipy import SpotifyOAuth
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

client_id=os.environ.get("SPOTIPY_CLIENT_ID")
client_secret=os.environ.get("SPOTIPY_CLIENT_SECRET")
redirect_uri=os.environ.get("SPOTIPY_REDIRECT_URI")
scope="user-top-read,user-library-read,user-read-recently-played"

creds = SpotifyOAuth(scope=scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, open_browser=False, cache_path="./cache/spotipy_cache")

sp = spotipy.Spotify(auth_manager=creds)

top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term')