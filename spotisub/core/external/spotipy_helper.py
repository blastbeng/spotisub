import spotipy
import os
from os.path import dirname
from os.path import join
from dotenv import load_dotenv
from spotipy import SpotifyOAuth
from .utils import utils
from .utils.constants import constants
from .exceptions.exceptions import SpotifyApiException


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

sp = None

def get_secrets():
    client_id = os.environ.get(
        constants.SPOTIPY_CLIENT_ID,
        constants.SPOTIPY_CLIENT_ID_DEFAULT_VALUE)
    client_secret = os.environ.get(
        constants.SPOTIPY_CLIENT_SECRET,
        constants.SPOTIPY_CLIENT_SECRET_DEFAULT_VALUE)
    redirect_uri = os.environ.get(
        constants.SPOTIPY_REDIRECT_URI,
        constants.SPOTIPY_REDIRECT_URI_DEFAULT_VALUE)

    if (client_id != ""
        and client_secret != ""
            and redirect_uri != ""):
        secrets = {}
        secrets["client_id"] = client_id
        secrets["client_secret"] = client_secret
        secrets["redirect_uri"] = redirect_uri
        return secrets
    raise SpotifyApiException()

def create_sp_client():
    secrets = get_secrets()
    SCOPE = "user-top-read,user-library-read,user-read-recently-played"
    creds = spotipy.SpotifyOAuth(
        scope=SCOPE,
        client_id=secrets["client_id"],
        client_secret=secrets["client_secret"],
        redirect_uri=secrets["redirect_uri"],
        open_browser=False,
        cache_path=os.path.dirname(
            os.path.abspath(__file__)) +
        "/../../../cache/spotipy_cache")

    return spotipy.Spotify(auth_manager=creds)
    
def get_spotipy_client():
    global sp
    if sp is None:
        sp = create_sp_client()
    return sp

