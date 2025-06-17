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

def get_mbids_from_isrc(isrc: str) -> list:
    isrc = isrc.replace('-', '').upper()

    try:
        res = musicbrainzngs.get_recordings_by_isrc(isrc)
        time.sleep(0.25)
    except ResponseError as e:
        if "404" in str(e):
            logging.warning(f'Spotify track with ISRC: {isrc} was not found in the MusicBrainz database. Consider manually submitting it.')
        elif "400" in str(e):
            logging.error(f'HTTP Error 400 from MusicBrainz API for ISRC: {isrc}.')
        else:
            utils.write_exception()
        return []
    except Exception:
        utils.write_exception()
        return []

    if "isrc" not in res:
        return []
    if "recording-list" not in res["isrc"]:
        return []

    return list(map(lambda rec: rec["id"], res["isrc"]["recording-list"]))
