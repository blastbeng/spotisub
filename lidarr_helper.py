import os

from dotenv import load_dotenv
from os.path import dirname
from os.path import join
from pyarr import LidarrAPI
from expiringdict import ExpiringDict
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

ipaddress=os.environ.get("LIDARR_IP","")
port=os.environ.get("LIDARR_PORT","")
base_api_path=os.environ.get("LIDARR_BASE_API_PATH","")
ssl="https" if os.environ.get("LIDARR_USE_SSL","0") == 1 else "http"
api_token=os.environ.get("LIDARR_TOKEN")

lidarr_url = ssl + "://" + ipaddress + ":" + port + base_api_path

cache = ExpiringDict(max_len=1, max_age_seconds=3600)

lidarr_client = LidarrAPI(lidarr_url,api_token)

def is_artist_monitored(artist_name):
    monitored = False

    artists_list = None if "lidarr_artists" not in cache else cache["lidarr_artists"]
    if artists_list is None:
        artists_list = lidarr_client.get_artist()
        cache["lidarr_artists"] = artists_list
    if artists_list is not None:
        for artist in artists_list:
            if artist_name.strip().lower() == artist["artistName"].strip().lower() and artist["monitored"] is True:
                monitored = True
                break

    return monitored