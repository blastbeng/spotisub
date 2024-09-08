# Spotify Playlist Generator

## Description

Simple playlist generator based on spotify user and artists reccomendations with Navidrome support

This script will also try to match all your Spotify playlists to your music library

SCRIPT FEATURES:
* Generate 5 playlist based on your history, top tracks and saved tracks
* Generate artist reccomendation playlists for every artist in your library
* Generate playlists based on your created and followed playlists on Spotify

For every playlist created if a navidrome.db file has been specified, it will try to delete the playlist by name from the Navidrome database.
This because I noted that Navidrome doesn't automatically update modified playlists, but deleting and letting it reimporting everything solved this problem.

## Getting Started

### Dependencies

* python3.5 with pip enabled
* spotipy
* pysqlite3
* python-dotenv

### Installing

As Script:
* cd /opt/projects
* git clone https://github.com/blastbeng/spotify-playlist-generator
* cd spotify-playlist-generator
* ./installdeps_script.sh
* cp .env.sample .env and modify it with your keys from spotify dev dashboard

As Flask App with docker compose:
* cd /opt/projects
* git clone https://github.com/blastbeng/spotify-playlist-generator
* cd spotify-playlist-generator
* ./installdeps_script.sh
* cp .env.sample .env and modify it with your keys from spotify dev dashboard
* python run.py => To generate the .cache file, used by the docker compose file
* docker compose build

### Executing program

* !!It is important that you have all the artists folder at the root of your library!!
* An acceptable folder structure is /music_dir/artist/album/cd1/song.mp3, /music_dir/artist/song.mp3 or /music_dir/artist/album/song.mp3
* A non acceptable folder structure is /music_dir/song.mp3
* !!Make sure you modify the parameters inside .env, you'll need a spotify dev account on https://developer.spotify.com/dashboard!!

As Script:
```
cd /opt/projects/spotify-playlist-generator
source .venv/bin/activate
python run.py
```

As Flask App with docker compose:
```
cd /opt/projects/spotify-playlist-generator
docker compose up
```

## Help

NOTE. Depending on your library size and your playlists number and size on Spotify, the script execution may take a very long time.
To avoid Spotify rate limiting a lot of time.sleep() have ben added to the code.

Using the Flask App is the reccomended way.


For any help contact me on Discord blastbong#9151

## Authors

Fabio Valentino - [blastbeng](https://github.com/blastbeng)  

## Version History

* 0.1
    * Initial Release
* 0.2
    * Implemented flask APIs and Scheduler
 
## TODO:

* Better Playlist Naming and Sorting
* Implement Subsonic APIs Mode instead of using file system paths and sqlite

## Acknowledgments

A big thanks to the Spotipy library
* [spotipy](https://github.com/spotipy-dev/spotipy)
