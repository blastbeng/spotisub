# Spotisub
![image](https://github.com/user-attachments/assets/ad0740d9-e70c-4940-b98f-8d8b03deb200)

Spotify to subsonic Playlist Generator and Importer

Since I haven't found an app to import my Spotify playlists, I started this project for myself, but then decided that this could be helpful for the community. 

!!! WORK IN PROGRESS !!!

The current release has all the base features, but it is still a work in progress, so expect bugs.

## Description

Simple playlist generator based on spotify user and artists recommendations with Subsonic API support

This software will try to match all your Spotify playlists to your music library using Subsonic APIs

This generator works with Navidrome and every Subsonic API enabled media center 

This is an example about what it generates using Navidrome:

![image](https://github.com/user-attachments/assets/99f46930-2e8d-4330-aa73-10b094d0b70a)

For install instructions take a look at the WIKI: [https://github.com/blastbeng/spotisub/wiki](https://github.com/blastbeng/spotisub/wiki)


## Features

* Generate 5 playlist based on your history, top tracks and saved tracks
* Generate artist reccommendation playlists for every artist in your library
* Generate artist top tracks playlists for every artist in your library
* Generate playlists based on your created and followed playlists on Spotify
* Generate playlist with all your saved tracks on Spotify
* Optional Spotdl integration, to automate the dowload process of missing tracks from the subsonic database
* Optional Lidarr integration, used altogether with spotdl to make decision about download a matching song or not

Take a look at Spotdl here: [https://github.com/spotDL/spotify-downloader](https://github.com/spotDL/spotify-downloader) 
Take a look at Lidarr here: [https://github.com/Lidarr/Lidarr](https://github.com/Lidarr/Lidarr)

When both Spotdl and Lidarr integrations are enabled, if spotisub doesn't find a song in subsonic database, it tries to search the artist returned from the spotify APIs inside the Lidarr database (via Lidarr APIs).
If this artist isn't found inside the Lidarr database, the download process is skipped.

So for example if you want to automate the download process, using this system you can skip the artists you don't like.

## Track Matching

The track matching is made in two different ways, by ISRC comparison and simple text comparison.

For perfect track match by ISRC it is important that the songs in your library have the **musicBrainzId tag**.

### ISRC
The ISRC is univoque for song, read more about it on [ISRC - MusicBrainz](https://musicbrainz.org/doc/ISRC)

In case the song found in your library has a musicBrainzId tag, it will be used to retrieve the ISRC from Musicbrainz Database.

This ISRC will then be compared with the Spotify song ISRC (if present).

If these two ISRC matches, the song will be added to the playlist and the text comparison will be skipped.

### Simple Text Comparison
When the two ISRCs doesn't match, the text comparison will be executed between the Subsonic found song and Spotify song.

In case of successfull compare, the song will be added to the playlist.

## Planned Features

Dashboard
* View which tracks are missing and decide to download trough spotdl or just ignore em
* View which tracks are being matched with the Spotify playlists\recommendations, and decide to keep or exclude em
* Configure some parameters of spotisub trough the dashboard instead of docker env variables
* Ability to interact with spotdl and lidarr integrations from the dashboard

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

