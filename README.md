# Subtify

Spotify to subsonic Playlist Generator and Importer

## Description

Simple playlist generator based on spotify user and artists reccomendations with Subsonic API support

This script will try to match all your Spotify playlists to your music library using Subsonic APIs

This generator works with Navidrome and every Subsonic API enabled media center 

This is an example about what it generates using Navidrome:

![image](https://github.com/user-attachments/assets/99f46930-2e8d-4330-aa73-10b094d0b70a)

Also there are three endpoints available for manually importing playlists.

FLASK APP ENDPOINTS:
* /generate/artist_reccomendations/<artist_name>/ => Generate artist reccomendation playlists, if no artist is provided it will choose a random one from your library
* /generate/reccomendations => Generate a random reccomendation Playlist
* /generate/user_playlists => import a random playlist from your spotify account

SCRIPT FEATURES:
* Generate 5 playlist based on your history, top tracks and saved tracks
* Generate artist reccomendation playlists for every artist in your library
* Generate playlists based on your created and followed playlists on Spotify

## Getting Started

### Dependencies

* python3.5 with pip enabled
* rust compiler (not needed if using python with pyenv)


### Prerequisite

* Create an APP on https://developer.spotify.com/dashboard and put this as redirect URI http://127.0.0.1:8080/

### Installing

Using the pushed docker image:
```
mkdir -p /opt/projects/subtify
cd /opt/projects/subtify
wget https://raw.githubusercontent.com/blastbeng/subtify/main/docker-compose.yml
wget https://raw.githubusercontent.com/blastbeng/subtify/main/.env.sample
mv .env.sample .env
docker compose pull
```

The docker image is available at https://hub.docker.com/r/blastbeng/subtify/tags


Building the FlaskApp:
```
mkdir -p /opt/projects
cd /opt/projects
git clone https://github.com/blastbeng/subtify
cd subtify
cp .env.sample .env
docker compose build
```

As Script:
```
mkdir -p /opt/projects
cd /opt/projects
git clone https://github.com/blastbeng/subtify
cd subtify
./installdeps_script.sh
cp .env.sample .env
```

### Executing program

* Make sure you modify the parameters inside .env file
* You'll need a spotify dev account on https://developer.spotify.com/dashboard

First run using the docker image:
```
cd /opt/projects/subtify
touch .cache
docker compose up -d
docker compose exec -it subtify /home/user/subtify/first_run.sh
docker compose down
```
This is necessary, to generate the cache file used by spotify authentication

Run as Flask App with docker compose:
```
cd /opt/projects/subtify
docker compose up
```

Run as Script:
```
cd /opt/projects/subtify
source .venv/bin/activate
python run.py
```

## Help

NOTE. Depending on your library size and your playlists number and size on Spotify, the script execution may take a very long time.
To avoid Spotify rate limiting a lot of time.sleep() have ben added to the code.

Using the Flask App is the reccomended way.


For any help contact me on Discord blastbong#9151

## Authors

Fabio Valentino - [blastbeng](https://github.com/blastbeng)  

## Changelog

* Implemented script
* Implemented flask APIs and Scheduler
* Implemented via subsonic api calls instead of file system

## Next steps and improvements

* Better reccomendation generation (generate non existent playlists instead of doing it randomly)
* Better playlist importing (import non existent playlists instead of doing it randomly)
* Import specific playlist by name

## Acknowledgments

A big thanks to the Spotipy library
* [spotipy](https://github.com/spotipy-dev/spotipy)
