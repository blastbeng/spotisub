# Navidrome

Navidrome is the reference server for Spotisub: everything here is tested against it.

## Two containers, one network

The single most common mistake is using `localhost` in `SUBSONIC_API_HOST`. Inside the
Spotisub container, `localhost` is Spotisub itself. Either use the host's LAN address, or
put both containers on one Docker network and use the service name.

```yaml
name: media

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
      ND_ENABLETRANSCODINGCONFIG: true
      ND_MAXSIDEBARPLAYLISTS: 50
    volumes:
      - "./data:/data"
      - "/music:/music:ro"
    restart: unless-stopped
    networks:
      - media

  spotisub:
    container_name: spotisub
    image: "blastbeng/spotisub:latest"
    env_file: .env
    ports:
      - "5183:5183"
    volumes:
      - "./cache:/home/user/spotisub/cache"
    restart: unless-stopped
    networks:
      - media
    healthcheck:
      test: curl -s http://127.0.0.1:5183/api/v1/utils/healthcheck | grep -q 'Ok!' || exit 1
      interval: 30s
      retries: 20
      start_period: 30s

networks:
  media:
```

and in `.env`:

```ini
SUBSONIC_API_HOST=http://navidrome
SUBSONIC_API_PORT=4533
SUBSONIC_API_USER=admin
SUBSONIC_API_PASS=your-navidrome-password

# Only when ND_BASEURL is set:
SUBSONIC_API_BASE_URL=/music
```

With `ND_BASEURL=/music`, Navidrome's API lives at `http://navidrome:4533/music/rest`,
which is exactly what `SUBSONIC_API_USER`… `SUBSONIC_API_BASE_URL` compose into. Get this
wrong and every request returns 404 or an empty list.

## Playlists and the Spotisub prefix

Navidrome imports playlists from its `ND_PLAYLISTSPATH` folder and syncs API-created
playlists like any other. Spotisub names them `Spotisub - <original name>`
(`PLAYLIST_PREFIX`); the prefix is what makes them easy to find — and easy to exclude
from other tools.

To keep them out of Navidrome's web UI sidebar clutter, the usual trick is filtering by
playlist name in your client, or simply living with the prefix.

## MBIDs: the tag that decides everything

Navidrome exposes the file's **MusicBrainz recording id** tag as `musicBrainzId`. It does
not compute it and does not fetch it. If your files lack the tag, MBID matching cannot
work for them — see [Missing tracks](../guide/missing-tracks.md).

The tag to write is the **recording** MBID. What tools call it, per format:

| Format | Tag written by Picard |
|---|---|
| FLAC / OGG (Vorbis comments) | `MUSICBRAINZ_TRACKID` |
| MP3 (ID3v2) | `TXXX:MusicBrainz Recording Id` (and `UFID:http://musicbrainz.org`) |
| M4A / MP4 | `----:com.apple.iTunes:MusicBrainz Track Id` |

Verify what Navidrome actually exposes for one file — that is the value Spotisub
compares:

```bash
curl -s "http://127.0.0.1:4533/rest/getSong.view?u=USER&p=PASS&v=1.16.1&c=test&id=SONG_ID" \
  | grep -o '<musicBrainzId>[^<]*</musicBrainzId>'
```

No `musicBrainzId` element means the tag is not being read; fix the tag, rescan the
library in Navidrome, then rescan the playlist in Spotisub.

## After spotdl downloads something

Navidrome only sees new files when it scans. If `ND_SCANSCHEDULE` is set (for example
`@every 1m`) it happens automatically; otherwise trigger a scan from Navidrome's UI. A
downloaded track stays "missing" in Spotisub until both Navidrome has scanned it **and**
the Subsonic cache has been rebuilt (automatic, whenever the song count changes) and the
playlist has been rescanned.

## Playlist permissions

The Navidrome user given to Spotisub must be allowed to create playlists. An admin user
always is; a regular user can only modify its own. Do not share a single Navidrome user
between Spotisub and your phone if you care about that distinction.
