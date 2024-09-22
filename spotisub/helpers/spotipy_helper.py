"""Spotipy helper"""
import os
import spotipy
from spotipy import SpotifyOAuth
from spotisub import constants
from spotisub.exceptions import SpotifyApiException


SP = None


def get_secrets():
    """Get Spotify api keys from env vars"""
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
    """Creates the spotipy client"""
    secrets = get_secrets()
    scope = "user-top-read,user-library-read,user-read-recently-played"
    creds = SpotifyOAuth(
        scope=scope,
        client_id=secrets["client_id"],
        client_secret=secrets["client_secret"],
        redirect_uri=secrets["redirect_uri"],
        open_browser=False,
        cache_path=os.path.dirname(
            os.path.abspath(__file__)) +
        "/../../cache/spotipy_cache")

    return spotipy.Spotify(auth_manager=creds)


def get_spotipy_client():
    """Get the previously created spotipy client"""
    return SP


SP = create_sp_client()
