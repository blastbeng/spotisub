"""Spotisub exceptions"""


class SpotifyApiException(Exception):
    "Please set up your Spotify API Keys"


class SpotifyDataException(Exception):
    "Error loading data from Spotify"


class SubsonicOfflineException(Exception):
    "Can't reach Subsonic is your server Offline?"


class SubsonicDataException(Exception):
    "Error retrieving data from Subsonic"
