# Environment variables

Defaults shown are the ones compiled into the application
(`spotisub/constants.py`). "Mandatory" means Spotisub does not work without it.

## Spotify

| Variable | Default | Required | Description |
|---|---|---|---|
| `SPOTIPY_CLIENT_ID` | *(empty)* | **yes** | From <https://developer.spotify.com/dashboard> |
| `SPOTIPY_CLIENT_SECRET` | *(empty)* | **yes** | From the same page. Keep it private. |
| `SPOTIPY_REDIRECT_URI` | `http://127.0.0.1:5183/callback` | no | Must match the Redirect URI of the Spotify app **character for character**. Change it only if you publish Spotisub on another host, port or path. |

!!! warning "The URI must end in /callback"

    Spotisub only answers the Spotify callback on `/callback`. If
    `SPOTIPY_REDIRECT_URI` points anywhere else, Spotify sends the browser to a page
    that does not exist and the login silently fails; Spotisub logs a warning with the
    URL to whitelist when it starts. The scheme, host and port in the variable must be
    exactly what the browser types to reach Spotisub — never the container-internal
    name.

## Subsonic server

| Variable | Default | Required | Description |
|---|---|---|---|
| `SUBSONIC_API_HOST` | *(empty)* | **yes** | Scheme + host, e.g. `http://navidrome` or `https://music.example.com` |
| `SUBSONIC_API_PORT` | *(empty → inferred)* | no | Empty means `443` for an `https://` host and `80` for `http://` |
| `SUBSONIC_API_USER` | *(empty)* | **yes** | Subsonic user, not the Spotisub login |
| `SUBSONIC_API_PASS` | *(empty)* | **yes** | Subsonic password |
| `SUBSONIC_API_BASE_URL` | *(empty)* | no | Path prefix when the server is mounted under one, e.g. `/music` for Navidrome `ND_BASEURL=/music` |
| `SUBSONIC_API_VERIFY_SSL` | `1` | no | `0` disables certificate verification (self-signed HTTPS only) |

The REST URL Spotisub builds is
`{SUBSONIC_API_HOST}:{SUBSONIC_API_PORT}{SUBSONIC_API_BASE_URL}/rest`.

## Playlists and matching

| Variable | Default | Required | Description |
|---|---|---|---|
| `PLAYLIST_PREFIX` | `Spotisub - ` | no | Prefix of every created playlist. Empty means no prefix. |
| `ITEMS_PER_PLAYLIST` | `1000` | no | Track cap for generated recommendation playlists; keep it modest |
| `NUM_USER_PLAYLISTS` | `5` | no | How many recommendation playlists to keep (recommendations are currently disabled, see below) |
| `TEXT_COMAPRE_MATCHING_ENABLED` | `0` | no | `1` enables fuzzy text matching when MBID matching fails. The misspelling is part of the public interface. |
| `EXCLUDED_WORDS` | `acoustic,instrumental,demo` | no | Comma-separated words rejected **in text comparison only**; empty disables the filter |
| `ARTIST_PLAYLIST_ENABLED` | `0` | no | `1` enables the artist top-tracks playlists |

!!! note "Recommendations are disabled upstream"

    Spotify removed the `/recommendations` API in December 2024. The recommendation jobs
    and their endpoints remain in the code but are not scheduled. `NUM_USER_PLAYLISTS`
    and `ITEMS_PER_PLAYLIST` only affect them.

## Scheduler

| Variable | Default | Required | Description |
|---|---|---|---|
| `SCHEDULER_ENABLED` | `1` | no | `0` pauses the whole scheduler: nothing runs automatically, only rescans and API calls |
| `SAVED_GEN_SCHED` | `2` | no | Hours between *Liked Songs* imports; `0` disables |
| `PLAYLIST_GEN_SCHED` | `3` | no | Hours between user-playlist imports; `0` disables |
| `ARTIST_TOP_GEN_SCHED` | `1` | no | Hours between artist top-tracks imports; `0` disables |
| `ARTIST_GEN_SCHED` | `1` | no | Artist recommendations interval (job disabled upstream) |
| `RECOMMEND_GEN_SCHED` | `4` | no | Recommendation interval (job disabled upstream) |

Details, including the one-playlist-per-interval behaviour:
[Scheduler](scheduler.md).

## spotdl (automatic downloads)

| Variable | Default | Required | Description |
|---|---|---|---|
| `SPOTDL_ENABLED` | `0` | no | `1` enables downloading missing tracks |
| `SPOTDL_FORMAT` | `/music/{artist}/{artists} - {album} ({year}) - {track-number} - {title}.{output-ext}` | when spotdl is on | Output path template, **including the absolute music path** |

See [spotdl](../integrations/spotdl.md).

## Lidarr

| Variable | Default | Required | Description |
|---|---|---|---|
| `LIDARR_ENABLED` | `0` | no | `1` only downloads tracks whose artist is monitored in Lidarr |
| `LIDARR_IP` | *(empty)* | when enabled | Host or IP, without scheme |
| `LIDARR_PORT` | *(empty)* | when enabled | e.g. `8686` |
| `LIDARR_TOKEN` | *(empty)* | when enabled | Lidarr → Settings → General → Security → API Key |
| `LIDARR_BASE_API_PATH` | *(empty)* | no | Only for a Lidarr behind a path prefix |
| `LIDARR_USE_SSL` | `0` | no | `1` for HTTPS |

See [Lidarr](../integrations/lidarr.md).

## Application and runtime

| Variable | Default | Required | Description |
|---|---|---|---|
| `SECRET_KEY` | *(empty)* | no | Flask session key. Empty → generated once and stored in `cache/secret_key`. **Setting it explicitly is recommended** so sessions survive a `cache/` wipe |
| `LOG_LEVEL` | `20` | no | Python logging level: `10` DEBUG, `20` INFO, `30` WARNING, `40` ERROR, `50` CRITICAL |
| `APPLICATION_ROOT` | *(empty)* | no | Path prefix when served under a sub-path, e.g. `/spotisub` |
| `LOGIN_DISABLED` | `0` | no | `1` disables the web login entirely — **local debugging only** |
| `CACHE_DIR` | `<cwd>/cache` | no | Where the database, token, caches and log live |
| `PUID` / `PGID` | `1000` / `1000` | no | Container only: uid/gid that owns `cache/` |

## Complete example

```ini title=".env"
SPOTIPY_CLIENT_ID=0123456789abcdef0123456789abcdef
SPOTIPY_CLIENT_SECRET=0123456789abcdef0123456789abcdef
SPOTIPY_REDIRECT_URI=http://127.0.0.1:5183/callback

SUBSONIC_API_HOST=http://navidrome
SUBSONIC_API_PORT=4533
SUBSONIC_API_USER=admin
SUBSONIC_API_PASS=change-me
SUBSONIC_API_BASE_URL=
SUBSONIC_API_VERIFY_SSL=1

PLAYLIST_PREFIX=Spotisub - 
ITEMS_PER_PLAYLIST=1000
TEXT_COMAPRE_MATCHING_ENABLED=0
EXCLUDED_WORDS=acoustic,instrumental,demo
ARTIST_PLAYLIST_ENABLED=0

SCHEDULER_ENABLED=1
SAVED_GEN_SCHED=2
PLAYLIST_GEN_SCHED=3
ARTIST_TOP_GEN_SCHED=1

SPOTDL_ENABLED=0
LIDARR_ENABLED=0
LOG_LEVEL=20
SECRET_KEY=
```
