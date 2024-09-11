import os
from os.path import join, dirname
from dotenv import load_dotenv
from spotdl import Spotdl
from spotdl.types.options import DownloaderOptions

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=int(os.environ.get("LOG_LEVEL", "40")),
        datefmt='%Y-%m-%d %H:%M:%S')

downloader_options = DownloaderOptions()
spotdl_client = Spotdl(client_id="9ec13a413da6462595ddaffceed18342", client_secret="8fa2ecbd00344cbd8914ca9ef5317440", no_cache=True)
spotdl_client.downloader.settings["output"] = os.environ.get("MUSIC_DIR", "/music") + "/{artist}/{artists} - {album} ({year}) - {track-number} - {title}.{output-ext}"

def download_track(track)
    songs = spotdl_client.search([track])
    if songs is not none and len(songs) > 0:
        for song in songs:
            if song.album_name is None or not song.album_name.lower().contains("live"):
                spotdl_client.download(song[0])
                break

