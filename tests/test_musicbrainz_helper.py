"""Tests for the MusicBrainz ISRC lookup retry behaviour (issue #99).

A transient network/DNS hiccup talking to the MusicBrainz API (e.g. a
flaky resolver returning `musicbrainzngs.musicbrainz.NetworkError`) used to
be caught by the generic `except Exception` branch in
`get_mbids_from_isrc()` and treated exactly like a permanent failure --
the track was immediately marked "not found" with no retry. During a large
playlist reimport this shows up as tracks failing progressively partway
through, which looks like the API rate-limiting or a flaky link rather than
any specific track being unresolvable.

`get_mbids_from_isrc()` now retries a bounded number of times (with a short
backoff) specifically for that generic-exception path, while a genuine
`ResponseError` (404 = not in MusicBrainz, 400 = bad request) still fails
immediately without retrying, since retrying can't change that outcome.
"""
import musicbrainzngs
from musicbrainzngs.musicbrainz import ResponseError

from spotisub.helpers import musicbrainz_helper


def _isrc_response(mbid):
    return {
        "isrc": {
            "id": "GBUM71029604",
            "recording-list": [{"id": mbid}],
        }
    }


def test_retries_on_transient_network_error_then_succeeds(monkeypatch):
    """A NetworkError-style failure (subclass of the library's base
    Exception, not ResponseError) is retried instead of immediately giving
    up, and a later successful attempt still returns the mbid list."""
    calls = {"count": 0}

    def flaky_get_recordings_by_isrc(isrc):
        calls["count"] += 1
        if calls["count"] < 3:
            raise musicbrainzngs.musicbrainz.NetworkError(
                "caused by: <urlopen error [Errno -3] Lookup timed out>")
        return _isrc_response("mbid-success")

    monkeypatch.setattr(
        musicbrainzngs, "get_recordings_by_isrc", flaky_get_recordings_by_isrc)
    monkeypatch.setattr(musicbrainz_helper.time, "sleep", lambda *_: None)

    result = musicbrainz_helper.get_mbids_from_isrc("GB-UM7-10-29604")

    assert result == ["mbid-success"]
    assert calls["count"] == 3


def test_gives_up_after_exhausting_retries_on_persistent_network_error(monkeypatch):
    """If MusicBrainz is genuinely down for the whole retry window, the
    function still returns [] afterwards instead of hanging the reimport,
    and it does not exceed the configured attempt budget."""
    calls = {"count": 0}

    def always_fails(isrc):
        calls["count"] += 1
        raise musicbrainzngs.musicbrainz.NetworkError(
            "caused by: <urlopen error [Errno -3] Lookup timed out>")

    monkeypatch.setattr(musicbrainzngs, "get_recordings_by_isrc", always_fails)
    monkeypatch.setattr(musicbrainz_helper.time, "sleep", lambda *_: None)
    monkeypatch.setattr(musicbrainz_helper.utils, "write_exception", lambda: None)

    result = musicbrainz_helper.get_mbids_from_isrc("GB-UM7-10-29604")

    assert result == []
    assert calls["count"] == musicbrainz_helper.MAX_ATTEMPTS


def test_response_error_404_fails_fast_without_retrying(monkeypatch):
    """A genuine 404 (track legitimately not in MusicBrainz) must not be
    retried -- it should fail immediately, as it did before this fix."""
    calls = {"count": 0}

    def not_found(isrc):
        calls["count"] += 1
        raise ResponseError("404 Not Found")

    monkeypatch.setattr(musicbrainzngs, "get_recordings_by_isrc", not_found)
    monkeypatch.setattr(musicbrainz_helper.time, "sleep", lambda *_: None)

    result = musicbrainz_helper.get_mbids_from_isrc("GB-UM7-10-29604")

    assert result == []
    assert calls["count"] == 1


def test_response_error_400_fails_fast_without_retrying(monkeypatch):
    """A genuine 400 (bad request) must also fail immediately without
    retrying."""
    calls = {"count": 0}

    def bad_request(isrc):
        calls["count"] += 1
        raise ResponseError("400 Bad Request")

    monkeypatch.setattr(musicbrainzngs, "get_recordings_by_isrc", bad_request)
    monkeypatch.setattr(musicbrainz_helper.time, "sleep", lambda *_: None)

    result = musicbrainz_helper.get_mbids_from_isrc("GB-UM7-10-29604")

    assert result == []
    assert calls["count"] == 1
