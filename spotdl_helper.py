# loading in modules
from os.path import join, dirname
from dotenv import load_dotenv
from spotdl import Spotdl
from spotdl.types.options import DownloaderOptions

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

downloader_options = DownloaderOptions()

client_id=os.environ.get("SPOTIPY_CLIENT_ID")
client_secret=os.environ.get("SPOTIPY_CLIENT_SECRET")

spotdl_client = Spotdl(client_id=client_id, client_secret=client_secret, no_cache=True)

spotdl_format = None
if os.environ.get("SPOTDL_OUT_FORMAT") is None:
    spotdl_format = "/music/{artist}/{artists} - {album} ({year}) - {track-number} - {title}.{output-ext}"
else:
    spotdl_format = os.environ.get("SPOTDL_OUT_FORMAT")

spotdl_client.downloader.settings["output"] = os.environ.get("SPOTDL_OUT_FORMAT")

def download_track(track):
    songs = spotdl_client.search([track])
    if songs is not none and len(songs) > 0:
        for song in songs:
            if song.album_name is None or not song.album_name.lower().contains("live"):
                spotdl_client.download(song[0])

