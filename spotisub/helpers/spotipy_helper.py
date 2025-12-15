"""Spotipy helper"""
import os
import logging
import spotipy
from spotipy import SpotifyOAuth
from spotisub import spotisub
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
    scope = "user-top-read,user-library-read,user-read-recently-played,playlist-read-private"
    cache_path = os.path.abspath(os.curdir) + '/cache/spotipy_cache'
    
    try:
        creds = SpotifyOAuth(
            scope=scope,
            client_id=secrets["client_id"],
            client_secret=secrets["client_secret"],
            redirect_uri=secrets["redirect_uri"],
            open_browser=False,
            cache_path=cache_path)

        return spotipy.Spotify(auth_manager=creds)
    except EOFError as e:
        logging.error(
            "Failed to authenticate with Spotify in non-interactive environment. "
            "Please ensure a valid cached token exists at: %s", cache_path)
        logging.error(
            "To fix this, run Spotisub interactively once to obtain a valid token, "
            "or ensure the SPOTIPY_CACHE file is properly set up.")
        raise SpotifyApiException(
            "Spotify authentication failed in non-interactive mode. "
            "Please run Spotisub interactively first to cache a valid token.") from e


def get_spotipy_client():
    """Get the previously created spotipy client"""
    return SP


SP = create_sp_client()
