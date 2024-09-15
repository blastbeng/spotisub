# Subtify
![subtify-high-resolution-logo](https://github.com/user-attachments/assets/8e5d50d9-8aec-4864-b2d6-78f8d01d25b1)

Spotify to subsonic Playlist Generator and Importer

Since I haven't found an app to import my Spotify playlists, I started this project for myself, but then decided that this could be helpful for the community. 

!!! WORK IN PROGRESS !!!

The current release has all the base features, but it is still a work in progress, so expect bugs.

## Description

Simple playlist generator based on spotify user and artists reccommendations with Subsonic API support

This software will try to match all your Spotify playlists to your music library using Subsonic APIs

This generator works with Navidrome and every Subsonic API enabled media center 

This is an example about what it generates using Navidrome:

![image](https://github.com/user-attachments/assets/99f46930-2e8d-4330-aa73-10b094d0b70a)

Also there are five endpoints available for manually importing playlists.

The default endpoint path is: http://127.0.0.1:50811



FEATURES:
* Generate 5 playlist based on your history, top tracks and saved tracks
* Generate artist reccommendation playlists for every artist in your library
* Generate artist top tracks playlists for every artist in your library
* Generate playlists based on your created and followed playlists on Spotify
* Generate playlist with all your saved tracks on Spotify
* Optional Spotdl integration, to automate the dowload process of missing tracks from the subsonic database
* Optional Lidarr integration, used altogether with spotdl to make decision about download a matching song or not

Take a look at Spotdl here: [https://github.com/spotDL/spotify-downloader](https://github.com/spotDL/spotify-downloader) 
Take a look at Lidarr here: [https://github.com/Lidarr/Lidarr](https://github.com/Lidarr/Lidarr)

When both Spotdl and Lidarr integrations are enabled, if subtify doesn't find a song in subsonic database, it tries to search the artist returned from the spotify APIs inside the Lidarr database (via Lidarr APIs).
If this artist isn't found inside the Lidarr database, the download process is skipped.

So for example if you want to automate the download process, using this system you can skip the artists you don't like.

FLASK APP ENDPOINTS:
* /generate/artist_reccommendations/<artist_name>/ => Generate artist reccommendations playlists, if no artist is provided it will choose a random one from your library
* /generate/artist_reccommendations/all/ => Generate reccommendations playlists for all the artists in your library
* /generate/artist_top_tracks/<artist_name>/ => Generate artist top tracks playlists, if no artist is provided it will choose a random one from your library
* /generate/artist_top_tracks/all/ => Generate top tracks playlists for all the artists in your library
* /generate/reccommendations => Generate a random reccommendations Playlist
* /import/user_playlists => import a random playlist from your spotify account
* /import/user_playlists/all => import all playlist from your spotify account
* /import/saved_tracks => import a playlist with all your saved tracks from your spotify account

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
docker compose pull
```

Remember to modifiy the Environment variables inside docker-compose.yml.

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

### Executing program

* Make sure you modify the parameters inside .env file
* You'll need a spotify dev account on https://developer.spotify.com/dashboard

First run using python:
```
cd /opt/projects/subtify
mkdir cache
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python init.py
```

First run using the docker image:
```
cd /opt/projects/subtify
docker exec -it subtify bash
./first_run.sh
exit
```
or
```
cd /opt/projects/subtify
docker exec -it subtify ./first_run.sh --interactive --tty
```
This is necessary, to generate the cache file used by spotify authentication

Run as Flask App with docker compose:
```
cd /opt/projects/subtify
docker compose up
```

## Using with Navidrome

Sample docker-compose file using Navidrome

Remember to always run the init sh as described before:
* docker compose exec -it subtify /home/user/subtify/first_run.sh --interactive --tty

```
services:
    navidrome:
        container_name: navidrome
        image: deluan/navidrome:latest
        user: 1000:1000
        ports:
            - "4533:4533"
        environment:
            ND_SCANSCHEDULE: "@every 1m"
            ND_LOGLEVEL: "info"
            ND_SESSIONTIMEOUT: "24h"
            ND_BASEURL: "/music"
            ND_MUSICFOLDER: /music
            ND_PLAYLISTSPATH: playlist
            ND_SPOTIFY_ID: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            ND_SPOTIFY_SECRET: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            ND_LASTFM_APIKEY: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            ND_LASTFM_SECRET: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            ND_ENABLETRANSCODINGCONFIG: true
            ND_MAXSIDEBARPLAYLISTS: 50
        volumes:
            - "./data:/data"
            - "/music:/music:ro"
        deploy:
            restart_policy:
                condition: on-failure
                delay: 5s
                max_attempts: 3
                window: 120s
        networks:
            - ndsubtifynet
        labels:
            - "com.centurylinklabs.watchtower.enable=true"
    subtify:
        container_name: subtify
        user: 1000:1000
        environment:
            - PUID=1000
            - PGID=1000
            - TZ=Europe/Rome
            - SPOTIPY_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            - SPOTIPY_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            - SPOTIPY_REDIRECT_URI=http://127.0.0.1:8080/
            - SUBSONIC_API_BASE_URL=/music
            - SUBSONIC_API_HOST=http://navidrome
            - SUBSONIC_API_PORT=4533
            - SUBSONIC_API_USER=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            - SUBSONIC_API_PASS=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            - ITEMS_PER_PLAYLIST=100
            - NUM_USER_PLAYLISTS=5
            - ARTIST_GEN_SCHED=2
            - RECCOMEND_GEN_SCHED=8
            - PLAYLIST_GEN_SCHED=6
            - SAVED_GEN_SCHED=24
            - SCHEDULER_ENABLED=1
            - SPOTDL_ENABLED=0
            - SPOTDL_FORMAT="/music/{artist}/{artists} - {album} ({year}) - {track-number} - {title}.{output-ext}"
            - LOG_LEVEL=20
        image: "blastbeng/subtify:latest"
        pull_policy: build
        build:
          context: ./subtify
          dockerfile: Dockerfile
        restart: always
        networks:
            - ndsubtifynet
        volumes:
            - "./cache:/home/user/subtify/cache"
        ports:
            - 50811:50811
        healthcheck:
            test: ["CMD", "curl", "-f", "http://127.0.0.1:50811/utils/healthcheck"]
            interval: 15s
            timeout: 5s
            retries: 12
        labels:
            - "com.centurylinklabs.watchtower.enable=true"
networks:
  ndsubtifynet:
```

## Environment Variables:

| Name | Info | Default       | Mandatory     |
| ------------- | ------------- | ------------- | ------------- |
| SPOTIPY_CLIENT_ID      | Get this from https://developer.spotify.com/dashboard  | None | Yes |
| SPOTIPY_CLIENT_SECRET  | Get this from https://developer.spotify.com/dashboard  | None | Yes |
| SPOTIPY_REDIRECT_URI  | Get this from https://developer.spotify.com/dashboard | None | Yes |
| SUBSONIC_API_HOST  | Subsonic API host, with http:// or https:// | None | Yes |
| SUBSONIC_API_PORT  | Subsonic API port | None | Yes |
| SUBSONIC_API_USER  | Subsonic API user | None | Yes |
| SUBSONIC_API_PASS  | Subsonic API password | None | Yes |
| SUBSONIC_API_BASE_URL  | Subsonic API Base Url, if your Navidrome ND_BASEURL param is "/music", set this to /music | Empty | No |
| ITEMS_PER_PLAYLIST  | How many items per playlists for reccommendations playlists, take care to not set this too high | 100 | No |
| PLAYLIST_PREFIX  | Playlists prefix name, every Subtify created playlist will have this prefix for better filtering, if set Empty playlists won't have a prefix | "Subtify - " | No |
| EXCLUDED_WORDS  | List of excluded words separated by comma used to filter search results from the subsonic library | acoustic,instrumental,demo | No |
| NUM_USER_PLAYLISTS  | How many custom reccommendations playlist to generate | 5 | No |
| SCHEDULER_ENABLED  | Set to 0 to disable the integrated scheduler, you will need to use the rest APIs if you disable this | 1 | No |
| ARTIST_GEN_SCHED  | Interval in hours to schedule the artists reccommendations generation, set to 0 to disable this generator | 1 | No |
| ARTIST_TOP_GEN_SCHED  | Interval in hours to schedule the top artists playlist import, set to 0 to disable this generator | 1 | No |
| RECCOMEND_GEN_SCHED  | Interval in hours to schedule the custom reccommendations generation, set to 0 to disable this generator | 4 | No |
| PLAYLIST_GEN_SCHED  | Interval in hours to schedule the custom playlist import, set to 0 to disable this generator | 3 | No |
| SAVED_GEN_SCHED  | Interval in hours to schedule the saved tracks playlist import, set to 0 to disable this generator | 2 | No |
| SPOTDL_ENABLED  | Automate the missing track download process using spotdl, set to 1 to enable | 0 | No |
| SPOTDL_OUT_FORMAT  | Spotdl output format, included the full absolute path to your music directory | "/music/{artist}/{artists} - {album} ({year}) - {track-number} - {title}.{output-ext}" | Yes if SPOTDL_ENABLED is 1 |
| LIDARR_ENABLED  | Set to 1 to enable Lidarr integration, used altogether with spotdl. If lidarr is enabled and an artist isn't found in lidarr library, the matching song won't be downloaded | 0 | no |
| LIDARR_IP  | Lidarr IP | Empty | Yes if LIDARR_ENABLED is 1 |
| LIDARR_PORT  | Lidarr port number | Empty | Yes if LIDARR_ENABLED is 1 |
| LIDARR_BASE_API_PATH  | Lidarr base path, usually you don't need to edit this | Empty | No |
| LIDARR_TOKEN  | Your Lidarr API Key. Get this in Lidarr > Settings > General > Security | Empty | Yes if LIDARR_ENABLED is 1 |
| LIDARR_USE_SSL  | Set to 1 if you are using a SSL certificate | 0 | No |
| LOG_LEVEL  | Log level | 40 | No |


For spotdl format examples please refer to: [https://spotdl.github.io/spotify-downloader/usage/](https://spotdl.github.io/spotify-downloader/usage/) 

## Planned Features

Dashboard
* View which tracks are missing and decide to download it trough spotdl or just ignore em
* Configure some parameters of subtify trough the dashboard instead of docker env variables
* Ability to interact with spotdl and lidarr integrations from the dashboard

Initial imports
* Ability to enable initial imports at startup instead of just running em trough the scheduler

## TODO

At the actual state the song comparison is made by just comparing song name and artist name, but I think that the comparison will be more accurate by using something like AcoustID.

The problem is that the Spotify APIs doesn't return any AcoustID, it is needed to download the song with SpotDL, generate the AcoustID and compare it with the local track AcoustID.

This can take very long time and can be a very cpu intensive process. 

For now I decided not to implement it, but if I find a faster and less cpu intensive way of doing it I may choose to implement it. 

## Help

NOTE. Depending on your library size and your playlists number and size on Spotify, the execution may take a very long time.
To avoid Spotify rate limiting a lot of time.sleep() have ben added to the code.


For any help contact me on Discord blastbong#9151

## Authors

Fabio Valentino - [blastbeng](https://github.com/blastbeng)

## Acknowledgments

A big thanks to the developers and maintaners of these libraries\softwares:
* [Spotipy](https://github.com/spotipy-dev/spotipy)
* [py-sonic](https://github.com/crustymonkey/py-sonic)
* [Navidrome](https://github.com/navidrome/navidrome)
* [spotdl](https://github.com/spotDL/spotify-downloader) 
* [Lidarr](https://github.com/Lidarr/Lidarr) 
* [pyarr](https://github.com/totaldebug/pyarr) 

