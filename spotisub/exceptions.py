"""Spotisub exceptions"""


class SpotifyApiException(Exception):
    "Please set up your Spotify API Keys"


class SpotifyDataException(Exception):
    "Error loading data from Spotify"


class SubsonicOfflineException(Exception):
    "Can't reach Subsonic is your server Offline?"


class SubsonicAuthException(SubsonicOfflineException):
    """The Subsonic server was reached but rejected the credentials"""


class SubsonicDataException(Exception):
    "Error retrieving data from Subsonic"


class SpotdlException(Exception):
    "Error downloading a track with spotdl"
