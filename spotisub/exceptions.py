"""Spotisub exceptions"""


class SpotifyApiException(Exception):
    "Please set up your Spotify API Keys"


class SpotifyDataException(Exception):
    "Error loading data from Spotify"


class SubsonicOfflineException(Exception):
    "Subsonic is Offline"


class SubsonicDataException(Exception):
    "Subsonic is Offline"
