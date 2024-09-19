"""Spotisub init script"""
import os

from os.path import dirname
from os.path import join
from dotenv import load_dotenv
import spotipy
from spotipy import SpotifyOAuth
from spotisub.core.external.utils.constants import constants

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

client_id = os.environ.get(constants.SPOTIPY_CLIENT_ID)
client_secret = os.environ.get(constants.SPOTIPY_CLIENT_SECRET)
redirect_uri = os.environ.get(constants.SPOTIPY_REDIRECT_URI)
SCOPE = "user-top-read,user-library-read,user-read-recently-played"

creds = SpotifyOAuth(
    scope=SCOPE,
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    open_browser=False,
    cache_path=os.path.dirname(
        os.path.abspath(__file__)) +
    "/cache/spotipy_cache")

sp = spotipy.Spotify(auth_manager=creds)

top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term')
