"""Tests for the SPOTIPY_REDIRECT_URI sanity warning.

The OAuth callback route is /callback, so a redirect URI pointing anywhere else
makes Spotify send the browser to a page Spotisub does not serve. That looks
exactly like "the login does nothing" and left users guessing (#101).
"""
import logging

from spotisub import constants
from spotisub.helpers import spotipy_helper


def test_callback_uri_is_accepted(monkeypatch, caplog):
    """A URI that ends in /callback must not produce a warning."""
    monkeypatch.setenv(
        constants.SPOTIPY_REDIRECT_URI, "http://127.0.0.1:5183/callback")
    with caplog.at_level(logging.WARNING):
        spotipy_helper.check_redirect_uri()
    assert not caplog.records


def test_uri_without_callback_is_reported(monkeypatch, caplog):
    """A URI that lacks /callback must warn with the URL to whitelist."""
    monkeypatch.setenv(constants.SPOTIPY_REDIRECT_URI, "http://127.0.0.1:8080/")
    with caplog.at_level(logging.WARNING):
        spotipy_helper.check_redirect_uri()
    assert "http://127.0.0.1:8080/callback" in caplog.text


def test_default_is_the_container_callback():
    """The compiled-in default has to be a URL the container actually serves."""
    assert constants.SPOTIPY_REDIRECT_URI_DEFAULT_VALUE.endswith("/callback")
    assert ":5183" in constants.SPOTIPY_REDIRECT_URI_DEFAULT_VALUE
