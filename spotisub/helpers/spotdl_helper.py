"""Spotdl helper"""
import logging
import os

from spotdl import Spotdl
from spotdl.types.song import Song
from spotisub import constants
from spotisub.exceptions import SpotdlException

_client = None


def _build_client():
    """Build the spotdl client from the environment."""
    client = Spotdl(
        client_id=os.environ.get(constants.SPOTIPY_CLIENT_ID),
        client_secret=os.environ.get(constants.SPOTIPY_CLIENT_SECRET),
        no_cache=True)
    client.downloader.settings["output"] = os.environ.get(
        constants.SPOTDL_FORMAT,
        constants.SPOTDL_FORMAT_DEFAULT_VALUE).replace(
            "\"",
        "")
    return client


def get_client():
    """Return the shared spotdl client, building it on first use.

    The client is built lazily because constructing it runs yt-dlp's own
    setup, which can fail (deprecated python, missing providers). Doing that
    at import time would keep the whole application from starting even when
    SPOTDL_ENABLED is off.
    """
    global _client  # pylint: disable=global-statement
    if _client is None:
        _client = _build_client()
    return _client


def download_track(url):
    """Download a track using spotdl"""
    try:
        song = Song.from_url(url)
        get_client().downloader.search_and_download(song)
    except Exception as error:
        # Runs inside a worker thread; nothing would see the exception otherwise.
        logging.error("spotdl failed to download %s: %s", url, error)
        raise SpotdlException() from error
