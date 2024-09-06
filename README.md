# Spotify Playlist Generator

## Description

Simple playlist generator based on spotify user reccomendations with Navidrome support

## Getting Started

### Dependencies

* python3.5 with pip enabled
* spotipy
* pysqlite3
* python-dotenv

### Installing

* cd /opt/projects
* git clone https://github.com/blastbeng/spotify-playlist-generator
* cd spotify-playlist-generator
* ./installdeps.sh
* cp .env.sample .env 

### Executing program



* !!It is important that you have all the artists folder at the root of your library!!
* An acceptable folder structure is /music_dir/artist/album/cd1/song.mp3, /music_dir/artist/song.mp3 or /music_dir/artist/album/song.mp3
* A non acceptable folder structure is /music_dir/song.mp3
* !!Make sure you modify the parameters inside .env, you'll need a spotify dev account on https://developer.spotify.com/dashboard!!
```
cd /opt/projects/spotify-playlist-generator
source .venv/bin/activate
python main.py
```

## Help

For any help contact me on Discord blastbong#9151

## Authors

Fabio Valentino - [blastbeng](https://github.com/blastbeng)  

## Version History

* 0.1
    * Initial Release

## Acknowledgments

A big thanks to the Spotipy library
* [spotipy](https://github.com/spotipy-dev/spotipy)