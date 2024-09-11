# Subtify
![subtify-high-resolution-logo](https://github.com/user-attachments/assets/8e5d50d9-8aec-4864-b2d6-78f8d01d25b1)

Spotify to subsonic Playlist Generator and Importer

## Description

Simple playlist generator based on spotify user and artists reccomendations with Subsonic API support

This software will try to match all your Spotify playlists to your music library using Subsonic APIs

This generator works with Navidrome and every Subsonic API enabled media center 

This is an example about what it generates using Navidrome:

![image](https://github.com/user-attachments/assets/99f46930-2e8d-4330-aa73-10b094d0b70a)

Also there are five endpoints available for manually importing playlists.

The default endpoint path is: http://127.0.0.1:50811



FEATURES:
* Generate 5 playlist based on your history, top tracks and saved tracks
* Generate artist reccomendation playlists for every artist in your library
* Generate playlists based on your created and followed playlists on Spotify
* Generate playlist with all your saved tracks on Spotify
* Optional spotdl integration, to automate the dowload process of missing tracks from the subsonic database

Take a look at spotdl here: [https://github.com/spotDL/spotify-downloader](https://github.com/spotDL/spotify-downloader) 

FLASK APP ENDPOINTS:
* /generate/artist_reccomendations/<artist_name>/ => Generate artist reccomendations playlists, if no artist is provided it will choose a random one from your library
* /generate/artist_reccomendations/all/ => Generate reccomendations playlists for all the artists in your library
* /generate/reccomendations => Generate a random reccomendations Playlist
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
wget https://raw.githubusercontent.com/blastbeng/subtify/main/.env.sample
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

First run using the docker image:
```
cd /opt/projects/subtify
docker compose up -d
docker compose exec -it subtify /home/user/subtify/first_run.sh --interactive --tty
docker compose down
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
version: "3.7"
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
            ND_BASEURL: ""
        volumes:
            - "./data:/data"
            - "/music:/music:ro"
        deploy:
            restart_policy:
                condition: on-failure
                delay: 5s
                max_attempts: 3
                window: 120s
    subtify:
        container_name: subtify
        environment:
            - PUID=1000
            - PGID=1000
            - TZ=Europe/Rome
            - SPOTIPY_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXX
            - SPOTIPY_CLIENT_SECRET=XXXXXXXXXXXXXXXXXXXXXXXX
            - SPOTIPY_REDIRECT_URI=http://127.0.0.1:8080/
            - SUBSONIC_API_HOST=http://127.0.0.1
            - SUBSONIC_API_PORT=4533
            - SUBSONIC_API_USER=user
            - SUBSONIC_API_PASS=pass
        image: "blastbeng/subtify:latest"
        restart: always
        volumes:
            - ".env:/home/user/subtify/.env"
            - "./cache:/home/user/subtify/cache"
        ports:
            - 50811:50811
        healthcheck:
            test: ["CMD", "curl", "-f", "http://127.0.0.1:50811/utils/healthcheck"]
            interval: 15s
            timeout: 5s
            retries: 12
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
| ITEMS_PER_PLAYLIST  | How many items per playlists for reccomendations playlists, take care to not set this too high | 100 | No |
| NUM_USER_PLAYLISTS  | How many custom reccomendations playlist to generate | 5 | No |
| SCHEDULER_ENABLED  | Set to 0 to disable the integrated scheduler, you will need to use the rest APIs if you disable this | 1 | No |
| ARTIST_GEN_SCHED  | Interval in hours to schedule the artists reccomendations generation, set to 0 to disable this generator | 1 | No |
| RECCOMEND_GEN_SCHED  | Interval in hours to schedule the custom reccomendations generation, set to 0 to disable this generator | 4 | No |
| PLAYLIST_GEN_SCHED  | Interval in hours to schedule the custom playlist import, set to 0 to disable this generator | 3 | No |
| SAVED_GEN_SCHED  | Interval in hours to schedule the saved tracks playlist import, set to 0 to disable this generator | 2 | No |
| SPOTDL_ENABLED  | Automate the missing track download process using spotdl, set to 1 to enable | 0 | No |
| SPOTDL_OUT_FORMAT  | Spotdl output format, included the full absolute path to your music directory | "/music/{artist}/{artists} - {album} ({year}) - {track-number} - {title}.{output-ext}" | Yes if SPOTDL_ENABLED is 1 |
| LOG_LEVEL  | Log level | 40 | No |


For spotdl format examples please refer to: [https://spotdl.github.io/spotify-downloader/usage/](https://spotdl.github.io/spotify-downloader/usage/) 

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

