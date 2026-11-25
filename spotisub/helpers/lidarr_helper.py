"""Lidarr helper"""
import logging
import os

from pyarr import LidarrAPI
from expiringdict import ExpiringDict
from spotisub import utils
from spotisub import constants

cache = ExpiringDict(max_len=1, max_age_seconds=3600)

_client = None


def _build_client():
    """Build the Lidarr client from the environment."""
    ipaddress = os.environ.get(constants.LIDARR_IP)
    port = os.environ.get(constants.LIDARR_PORT)
    if not ipaddress or not port:
        raise ValueError(
            "LIDARR_ENABLED is set but LIDARR_IP and LIDARR_PORT are required")
    base_api_path = os.environ.get(
        constants.LIDARR_BASE_API_PATH,
        constants.LIDARR_BASE_API_PATH_DEFAULT_VALUE)
    scheme = "https" if os.environ.get(
        constants.LIDARR_USE_SSL,
        constants.LIDARR_USE_SSL_DEFAULT_VALUE) == "1" else "http"
    api_token = os.environ.get(constants.LIDARR_TOKEN)
    lidarr_url = scheme + "://" + ipaddress + ":" + port + base_api_path
    logging.info("Lidarr client targeting %s", lidarr_url)
    return LidarrAPI(lidarr_url, api_token)


def get_client():
    """Return the shared Lidarr client, building it on first use."""
    global _client  # pylint: disable=global-statement
    if _client is None:
        _client = _build_client()
    return _client


def is_artist_monitored(artist_name):
    """Check if artist is monitored in Lidarr"""
    artists_list = None if "lidarr_artists" not in cache else cache["lidarr_artists"]
    if artists_list is None:
        artists_list = get_client().get_artist()
        cache["lidarr_artists"] = artists_list
    if artists_list is not None:
        for artist in artists_list:
            if artist["monitored"] is True and utils.compare_strings(
                    artist_name, artist["artistName"]):
                return True

    return False
