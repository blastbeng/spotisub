"""Tests for the text-comparison fallback used when MBID matching fails (#107).

The Subsonic cache (`song_mbid_dict`) only contains songs that carry a
`musicBrainzId` tag. A library scanned by Navidrome without those tags (it
does not compute them) therefore produced an empty candidate list, and
text comparison -- the documented fallback -- could never match anything.
The fallback now asks the server for candidates when the cache scan finds
nothing, using the part of the Spotify title before "(", "-" or "feat".
"""
import pytest

from spotisub import utils
from spotisub.classes import ComparisonHelper
from spotisub.helpers import subsonic_helper


def _comparison_helper(title, artist):
    return ComparisonHelper(
        track={"name": title, "artists": [{"name": artist}]},
        artist_spotify={"name": artist},
        found=False,
        excluded=False,
        song_ids=[],
        track_helper=[])


class _FakeConnection:
    def __init__(self, songs):
        self.songs = songs
        self.queries = []

    def search2(self, query, songCount=20, artistCount=20, albumCount=20):
        """Record the query and answer like libsonic does."""
        self.queries.append(query)
        if not self.songs:
            return {"searchResult2": {}}
        return {"searchResult2": {"song": self.songs}}


@pytest.fixture
def fake_subsonic(monkeypatch):
    """Install a fake Subsonic connection and return it."""
    def _install(songs):
        connection = _FakeConnection(songs)
        monkeypatch.setattr(
            subsonic_helper, "check_pysonic_connection", lambda: connection)
        return connection
    return _install


def test_finds_song_on_server_when_mbid_cache_is_empty(fake_subsonic):
    """A Navidrome library without MBID tags can still be text-matched."""
    connection = fake_subsonic([{
        "id": "42",
        "title": "Six Days",
        "artist": "DJ Shadow",
        "album": "The Private Press",
    }])

    matched = subsonic_helper.get_subsonic_track_via_string_compare(
        _comparison_helper("Six Days", "DJ Shadow"), {})

    assert matched is not None
    assert matched["id"] == "42"
    assert connection.queries == ["six days"]


def test_search_query_drops_the_remaster_suffix(fake_subsonic):
    """Spotify's "- 2004 Remaster" suffix is not part of the local tags."""
    connection = fake_subsonic([])

    subsonic_helper.get_subsonic_track_via_string_compare(
        _comparison_helper("Silver Springs - 2004 Remaster", "Fleetwood Mac"), {})

    assert connection.queries == ["silver springs"]


def test_search_does_not_apply_exclusion_to_empty_album(fake_subsonic):
    """A song without album/title metadata must not crash the exclusion check."""
    fake_subsonic([{
        "id": "7",
        "title": "Aline",
        "artist": "Christophe",
        "album": "",
    }])

    matched = subsonic_helper.get_subsonic_track_via_string_compare(
        _comparison_helper("Aline", "Christophe"), {})

    assert matched is not None
    assert matched["id"] == "7"


def test_returns_none_when_the_server_has_no_match(fake_subsonic):
    """No candidate on the server keeps the previous "not found" result."""
    fake_subsonic([{
        "id": "9",
        "title": "Something Else",
        "artist": "Another Artist",
        "album": "Another Album",
    }])

    matched = subsonic_helper.get_subsonic_track_via_string_compare(
        _comparison_helper("Six Days", "DJ Shadow"), {})

    assert matched is None


def test_build_text_search_query_strips_parentheses_and_punctuation():
    """Parenthetical and punctuation suffixes are removed from the query."""
    assert subsonic_helper.build_text_search_query(
        "Un facho K.O (feat. Someone)") == "un facho k o"
    assert subsonic_helper.build_text_search_query("") == ""


def test_exclusion_with_empty_input_returns_false():
    """Empty metadata means "nothing excludes this track" (no UnboundLocalError)."""
    assert utils.compare_string_to_exclusion(None, ["demo"]) is False
    assert utils.compare_string_to_exclusion("", ["demo"]) is False
    assert utils.compare_string_to_exclusion("   ", ["demo"]) is False
