import spotipy  
import random
import logging
import os
import sys
import glob
import time
import libsonic
from spotipy import SpotifyOAuth
from os.path import join, dirname
from dotenv import load_dotenv

os.environ["VERSION"] = "0.0.3"

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=int(os.environ.get("LOG_LEVEL", "40")),
        datefmt='%Y-%m-%d %H:%M:%S')

client_id=os.environ.get("SPOTIPY_CLIENT_ID")
client_secret=os.environ.get("SPOTIPY_CLIENT_SECRET")
redirect_uri=os.environ.get("SPOTIPY_REDIRECT_URI")
scope="user-top-read,user-library-read,user-read-recently-played"

creds = SpotifyOAuth(scope=scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, open_browser=False, cache_path=os.path.dirname(os.path.abspath(__file__)) + "/cache/spotipy_cache")

sp = spotipy.Spotify(auth_manager=creds)

pysonic = libsonic.Connection(os.environ.get("SUBSONIC_API_HOST"), os.environ.get("SUBSONIC_API_USER"),  os.environ.get("SUBSONIC_API_PASS"), appName="spotify-playlist-generator", port=int(os.environ.get("SUBSONIC_API_PORT")))

def get_artists_array_names():
    artists = pysonic.getArtists()
    
    artist_names = []

    for index in pysonic.getArtists()["artists"]["index"]:
        for artist in index["artist"]:
            artist_names.append(artist["name"])

    return artist_names


def my_reccommendations(count = None):
    try:
        top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term')
        logging.info('Loaded your custom top tracks')
        time.sleep(2)
        liked_tracks = sp.current_user_saved_tracks(limit=50)
        logging.info('Loaded your top liked tracks')
        time.sleep(2)
        history = sp.current_user_recently_played(limit=50)
        logging.info('Loaded your played tracks')
        time.sleep(2)
        for i in range(int(os.environ.get("NUM_USER_PLAYLISTS","5"))):
            if count is None or (count is not None and count == i):
                logging.info('Searching your reccomendations (playlist %s)', str(i+1))
                top_track_ids = [track['id'] for track in top_tracks['items']]
                liked_track_ids = [track['track']['id'] for track in liked_tracks['items']]
                history_track_ids = [track['track']['id'] for track in history['items']]
                seed_track_ids = top_track_ids + liked_track_ids + history_track_ids
                random.shuffle(seed_track_ids)
                results = sp.recommendations(seed_tracks=seed_track_ids[0:5], limit=int(os.environ.get("ITEMS_PER_PLAYLIST")))
                playlist_name = "00" + str(i+1) + " - My Reccomendations"
                write_playlist(playlist_name, results)
                if count is not None:
                    break
            time.sleep(10)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)

def get_artist(name):
    results = sp.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        return items[0]
    else:
        return None

def write_playlist(playlist_name, results):
    try:
        song_ids = []
        for track in results['tracks']:
            for artist_spotify in track['artists']:
                artist_name_spotify = artist_spotify["name"]
                logging.info('Searching %s - %s in your music library', artist_name_spotify, track['name'])
                navidrome_search = pysonic.search2(artist_name_spotify + " " + track['name'])
                if len(navidrome_search["searchResult2"]) and "song" in navidrome_search["searchResult2"]:
                    for song in navidrome_search["searchResult2"]["song"]:
                        song_title  = song["title"].strip().lower()
                        song_artist = song["artist"].strip().lower()
                        song_album  = song["album"].strip().lower()
                        if ((song_artist != '' and (artist_name_spotify.lower() == song_artist or song_artist in artist_name_spotify.lower() or artist_name_spotify.lower() in song_artist))
                            and (not "live" in song_title and not "acoustic" in song_title and not "live" in song_album and not "acoustic" in song_album)
                            and (song_title != '' and (track['name'].lower() == song_title or song_title in track['name'].lower() or track['name'].lower() in song_title))):
                                song_ids.append(song["id"])
        if len(song_ids) > 0:
            playlist_id = None
            for playlist in pysonic.getPlaylists()["playlists"]["playlist"]:
                if playlist["name"].strip() == playlist_name.strip():
                    playlist_id = playlist["id"]
                    break
            random.shuffle(song_ids)
            if playlist_id is not None:
                pysonic.createPlaylist(playlistId = playlist_id, songIds = song_ids)
            else:
                pysonic.createPlaylist(name = playlist_name, songIds = song_ids)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)

def show_recommendations_for_artist(name):
    logging.info('Searching reccomendations for: %s', name)
    artist = get_artist(name)
    results = sp.recommendations(seed_artists=[artist['id']], limit=int(os.environ.get("ITEMS_PER_PLAYLIST")))
    playlist_name = name + " - Reccomendations"
    write_playlist(playlist_name, results)

def get_playlist_tracks(item, result, offset_tracks = 0):
    response_tracks = sp.playlist_items(item['id'],
        offset=offset_tracks,
        fields='items.track.id,items.track.name,items.track.artists,total',
        limit=50,
        additional_types=['track'])
    for track_item in response_tracks['items']:
        track = track_item['track']
        logging.info('Found %s - %s inside playlist %s', track['artists'][0]['name'], track['name'], item['name'])
        track_dict = dict({'name': track['name'], 'artists': [{"name": track['artists'][0]['name']}]})
        result["tracks"].append(track)
    time.sleep(2)
    if len(response_tracks['items']) != 0:
        result = get_playlist_tracks(item, result, offset_tracks = offset_tracks + 50)
    return result

def get_user_playlists(offset = 0, single_execution = False, playlist_name = None):

    playlist_result = sp.current_user_playlists(limit=(50 if single_execution is False else 1), offset = offset)

    for item in playlist_result['items']:
        if item['name'] is not None and item['name'].strip() != '' and (playlist_name is None or (playlist_name is not None and item['name'].lower().strip() == playlist_name.lower().strip())):
            logging.info('Importing playlist: %s', item['name'])
            result = dict({'tracks': []})     
            result = get_playlist_tracks(item, result)    
            write_playlist(item['name'].strip(), result)
            if single_execution:
                break    
    
        
    if not single_execution and len(playlist_result['items']) != 0:
        get_user_playlists(offset = offset + 50)

def count_user_playlists(count, offset = 0):
    playlist_result = sp.current_user_playlists(limit=50, offset = offset)
    count = count + len(playlist_result['items'])

    if len(playlist_result['items']) != 0:
        count = count_user_playlists(count, offset = offset + 50)
    return count

def all_artists_recommendations():
    artist_names = get_artists_array_names()
    if len(artist_names) > 0:
        random.shuffle(artist_names)
        for artist_name in artist_names:
            show_recommendations_for_artist(artist_name)

def get_user_saved_tracks():
    result = dict({'tracks': []})
    result = get_user_saved_tracks_playlist(result)
    write_playlist("000 - Saved Tracks", result)

def get_user_saved_tracks_playlist(result, offset_tracks = 0):
    response_tracks = sp.current_user_saved_tracks(
        offset=offset_tracks,
        limit=50)
    for track_item in response_tracks['items']:
        track = track_item['track']
        logging.info('Found %s - %s inside your saved tracks', track['artists'][0]['name'], track['name'])
        track_dict = dict({'name': track['name'], 'artists': [{"name": track['artists'][0]['name']}]})
        result["tracks"].append(track)
    time.sleep(2)
    if len(response_tracks['items']) != 0:
        result = get_user_saved_tracks_playlist(result, offset_tracks = offset_tracks + 50)
    return result

def print_logo():
        version_len = len(os.environ.get("VERSION"))
        print(
            """

░██████╗██╗░░░██╗██████╗░████████╗██╗███████╗██╗░░░██╗
██╔════╝██║░░░██║██╔══██╗╚══██╔══╝██║██╔════╝╚██╗░██╔╝
╚█████╗░██║░░░██║██████╦╝░░░██║░░░██║█████╗░░░╚████╔╝░
░╚═══██╗██║░░░██║██╔══██╗░░░██║░░░██║██╔══╝░░░░╚██╔╝░░
██████╔╝╚██████╔╝██████╦╝░░░██║░░░██║██║░░░░░░░░██║░░░
╚═════╝░░╚═════╝░╚═════╝░░░░╚═╝░░░╚═╝╚═╝░░░░░░░░╚═╝░░░

"""
            + "\n"
            + "                                     "[: -(version_len + 2)]
            + "v{} ".format(os.environ.get("VERSION"))
        )