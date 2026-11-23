"""Musicbrainz helper"""
import time
import logging


import musicbrainzngs
from musicbrainzngs.musicbrainz import ResponseError
from spotisub import utils


# Disabling musicbrainz INFO log as we don't want to see ugly infos in the
# console
log = logging.getLogger("musicbrainzngs")
log.setLevel(40)

musicbrainzngs.set_useragent(
    "navidrome music",
    "0.1",
    "http://example.com/music")

# Bounded retry for transient network/DNS failures talking to the
# MusicBrainz API (see issue #99: a flaky resolver/link surfaces as
# musicbrainzngs.musicbrainz.NetworkError, which is not a ResponseError and
# was previously treated as a permanent "track not found" instead of a
# retryable hiccup). Genuine ResponseError cases (404 = not in MusicBrainz,
# 400 = bad request) are not retried, since retrying won't change the
# outcome.
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = (1, 2)


def get_mbids_from_isrc(isrc: str) -> list:
    isrc = isrc.replace('-', '').upper()

    res = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            res = musicbrainzngs.get_recordings_by_isrc(isrc)
            time.sleep(0.25)
            break
        except ResponseError as e:
            if "404" in str(e):
                logging.warning(
                    f'Spotify track with ISRC: {isrc} was not found in the MusicBrainz database. Consider manually submitting it.')
            elif "400" in str(e):
                logging.error(
                    f'HTTP Error 400 from MusicBrainz API for ISRC: {isrc}.')
            else:
                utils.write_exception()
            return []
        except Exception:
            if attempt < MAX_ATTEMPTS:
                logging.warning(
                    f'Transient error contacting MusicBrainz for ISRC: {isrc} '
                    f'(attempt {attempt}/{MAX_ATTEMPTS}). Retrying...')
                backoff_index = min(attempt - 1, len(RETRY_BACKOFF_SECONDS) - 1)
                time.sleep(RETRY_BACKOFF_SECONDS[backoff_index])
                continue
            utils.write_exception()
            return []

    if res is None:
        return []

    if "isrc" not in res:
        return []
    if "recording-list" not in res["isrc"]:
        return []

    return list(map(lambda rec: rec["id"], res["isrc"]["recording-list"]))
