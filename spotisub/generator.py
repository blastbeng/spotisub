"""Subsonic generator"""
import logging
import os
import random
import time
import re
from spotisub import constants
from spotisub.helpers import spotipy_helper
from spotisub.helpers import subsonic_helper


def get_spotipy_helper():
    """get spotipy helper"""
    return spotipy_helper


def get_subsonic_helper():
    """get subsonic helper"""
    return subsonic_helper


def artist_top_tracks(query):
    """artist top tracks"""
    sp = spotipy_helper.get_spotipy_client()
    results = sp.search(query)
    artists_uri = {}
    if "tracks" in results and "items" in results["tracks"] and len(
            results["tracks"]["items"]) > 0:
        for item in results['tracks']["items"]:
            if "artists" in item:
                for artist in item["artists"]:
                    artist_name_no_punct = re.sub(
                        r'[^\w\s]', '', artist["name"])
                    query_no_punct = re.sub(r'[^\w\s]', '', query)
                    if ("uri" in artist and "name" in artist
                        and ((query.lower() == artist["name"].lower()
                              or query.lower() in artist["name"].lower()
                              or artist["name"].lower() in query.lower())
                             or (query_no_punct.lower() == artist_name_no_punct.lower()
                                 or query_no_punct.lower() in artist_name_no_punct.lower()
                                 or artist_name_no_punct.lower() in query_no_punct.lower()))):
                        artists_uri[artist["name"]] = artist["uri"]

    for artist_name in artists_uri:
        artist_top = sp.artist_top_tracks(artists_uri[artist_name])
        playlist_name = artist_name + " - Top Tracks"
        subsonic_helper.write_playlist(sp, playlist_name, artist_top)


def my_recommendations(count=None):
    """my recommendations"""
    sp = spotipy_helper.get_spotipy_client()
    top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term')
    logging.info('Loaded your custom top tracks')
    time.sleep(2)
    liked_tracks = sp.current_user_saved_tracks(limit=50)
    logging.info('Loaded your top liked tracks')
    time.sleep(2)
    history = sp.current_user_recently_played(limit=50)
    logging.info('Loaded your played tracks')
    time.sleep(2)
    for i in range(int(os.environ.get(constants.NUM_USER_PLAYLISTS,
                   constants.NUM_USER_PLAYLISTS_DEFAULT_VALUE))):
        if count is None or (count is not None and count == i):
            logging.info(
                'Searching your recommendations (playlist %s)', str(
                    i + 1))
            top_track_ids = [track['id'] for track in top_tracks['items']]
            liked_track_ids = [track['track']['id']
                               for track in liked_tracks['items']]
            history_track_ids = [track['track']['id']
                                 for track in history['items']]
            seed_track_ids = top_track_ids + liked_track_ids + history_track_ids
            random.shuffle(seed_track_ids)
            results = sp.recommendations(seed_tracks=seed_track_ids[0:5], limit=int(
                os.environ.get(constants.ITEMS_PER_PLAYLIST, constants.ITEMS_PER_PLAYLIST_DEFAULT_VALUE)))
            playlist_name = "My Recommendations " + str(i + 1)
            subsonic_helper.write_playlist(
                sp, playlist_name, results)
            if count is not None:
                break
        time.sleep(10)


def get_artist(name):
    """get artist"""
    sp = spotipy_helper.get_spotipy_client()
    results = sp.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        return items[0]
    return None


def show_recommendations_for_artist(name):
    """show recommendations for artist"""
    sp = spotipy_helper.get_spotipy_client()
    logging.info('Searching recommendations for: %s', name)
    artist = get_artist(name)
    if artist is not None:
        results = sp.recommendations(
            seed_artists=[
                artist['id']],
            limit=int(
                os.environ.get(
                    constants.ITEMS_PER_PLAYLIST,
                    constants.ITEMS_PER_PLAYLIST_DEFAULT_VALUE)))
        playlist_name = name + " - Recommendations"
        subsonic_helper.write_playlist(sp, playlist_name, results)
    else:
        logging.warning('Artist: %s Not found!', name)


def get_playlist_tracks(item, result, offset_tracks=0):
    """get playlist tracks"""
    sp = spotipy_helper.get_spotipy_client()
    response_tracks = sp.playlist_items(item['id'],
                                        offset=offset_tracks,
                                        fields='items.track.id,items.track.name,items.track.artists,total',
                                        limit=50,
                                        additional_types=['track'])
    for track_item in response_tracks['items']:
        track = track_item['track']
        logging.info(
            'Found %s - %s inside playlist %s',
            track['artists'][0]['name'],
            track['name'],
            item['name'])
        if track is not None:
            result["tracks"].append(track)
    time.sleep(2)
    if len(response_tracks['items']) != 0:
        result = get_playlist_tracks(
            item, result, offset_tracks=offset_tracks + 50)
    return result


def get_user_playlist_by_name(playlist_name, offset=0):
    """get user playlist by name"""
    sp = spotipy_helper.get_spotipy_client()
    playlist_result = sp.current_user_playlists(limit=50, offset=offset)

    name_found = None

    for item in playlist_result['items']:
        if (item['name'] is not None and item['name'].strip() != ''
            and (playlist_name is None
            or (playlist_name is not None
                and item['name'].lower().strip() == playlist_name.lower().strip()))):
            name_found = item['name'].strip()
    if name_found is None and len(playlist_result['items']) != 0:
        name_found = get_user_playlist_by_name(
            playlist_name, offset=offset + 50)
    return name_found


def get_user_playlists(offset=0, single_execution=False, playlist_name=None):
    """get user playlists"""
    sp = spotipy_helper.get_spotipy_client()

    playlist_result = sp.current_user_playlists(
        limit=(50 if single_execution is False else 1), offset=offset)

    for item in playlist_result['items']:
        if item['name'] is not None and item['name'].strip() != '' and (playlist_name is None or (
                playlist_name is not None and item['name'].lower().strip() == playlist_name.lower().strip())):
            logging.info('Importing playlist: %s', item['name'])
            result = dict({'tracks': []})
            result = get_playlist_tracks(item, result)
            subsonic_helper.write_playlist(sp, item['name'].strip(), result)
            if single_execution:
                break

    if not single_execution and len(playlist_result['items']) != 0:
        get_user_playlists(offset=offset + 50)


def count_user_playlists(count, offset=0):
    """count user playlists"""
    sp = spotipy_helper.get_spotipy_client()
    playlist_result = sp.current_user_playlists(limit=50, offset=offset)
    count = count + len(playlist_result['items'])

    if len(playlist_result['items']) != 0:
        count = count_user_playlists(count, offset=offset + 50)
    return count


def all_artists_recommendations(artist_names):
    """all artists recommendations"""
    if len(artist_names) > 0:
        random.shuffle(artist_names)
        for artist_name in artist_names:
            show_recommendations_for_artist(artist_name)


def all_artists_top_tracks(artist_names):
    """all artists top tracks"""
    if len(artist_names) > 0:
        random.shuffle(artist_names)
        for artist_name in artist_names:
            artist_top_tracks(artist_name)


def get_user_saved_tracks(result):
    """get user saved tracks"""
    sp = spotipy_helper.get_spotipy_client()
    result = get_user_saved_tracks_playlist(result)
    subsonic_helper.write_playlist(sp, "Saved Tracks", result)


def get_user_saved_tracks_playlist(result, offset_tracks=0):
    """get user saved tracks playlist"""
    sp = spotipy_helper.get_spotipy_client()
    response_tracks = sp.current_user_saved_tracks(
        offset=offset_tracks,
        limit=50)
    for track_item in response_tracks['items']:
        if "track" in track_item:
            track = track_item['track']
            if track is not None:
                logging.info(
                    'Found %s - %s inside your saved tracks',
                    track['artists'][0]['name'],
                    track['name'])
                if track is not None:
                    result["tracks"].append(track)
    time.sleep(2)
    if len(response_tracks['items']) != 0:
        result = get_user_saved_tracks_playlist(
            result, offset_tracks=offset_tracks + 50)
    return result
