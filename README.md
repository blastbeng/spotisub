# Spotisub

**Import your Spotify playlists into Navidrome — or any other Subsonic-API music
server — and keep them in sync automatically.**

[![Documentation](https://img.shields.io/badge/documentation-blastbeng.github.io%2Fspotisub-2ea44f)](https://blastbeng.github.io/spotisub/)
[![GitHub release](https://img.shields.io/github/v/release/blastbeng/spotisub?display_name=tag&sort=semver)](https://github.com/blastbeng/spotisub/releases)
[![Docker pulls](https://img.shields.io/docker/pulls/blastbeng/spotisub)](https://hub.docker.com/r/blastbeng/spotisub)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.md)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/)

> ## 📖 Documentation: <https://blastbeng.github.io/spotisub/>
>
> The project now has a full documentation site, and it is the place to start:
> a four-step quickstart, screenshots of every screen, the complete configuration
> reference, the REST API and a troubleshooting guide built from the recurring
> issue reports. Everything below is a summary — the site walks you through each
> step from an empty machine to a working playlist.

---

## What Spotisub does

Spotisub connects three things you already have — Spotify, a Subsonic-API media
server, and a folder full of music — and keeps them in step:

1. **Reads your Spotify account** with the Spotify Web API: the playlists you
   created or follow, your *Liked Songs*, and optionally a top-tracks playlist for
   every artist in your library.
2. **Matches every track against your library** — first by ISRC → MusicBrainz
   recording MBID, then (optionally) by a fuzzy title/artist comparison.
3. **Writes the result as a real playlist** on your server through the Subsonic
   API, named `Spotisub - <playlist name>`, and refreshes it on a schedule.
4. **Shows you what it could not match** on the *Missing* page, where a track,
   album, artist or whole playlist can be ignored so it is never searched again.

Nothing on Spotify is ever modified: the requested scopes are read-only
(`playlist-read-private`, `user-library-read`, `user-top-read`,
`user-read-recently-played`).

![A generated playlist in Navidrome](https://github.com/user-attachments/assets/99f46930-2e8d-4330-aa73-10b094d0b70a)

## Requirements

| You need | Why |
|---|---|
| A **Spotify Premium** account | Spotify has required Premium for Web API access since its February 2026 developer policy change — a free account gets the app blocked (`403`). See [Troubleshooting](https://blastbeng.github.io/spotisub/help/troubleshooting/). |
| A Spotify **app** (Client ID + Secret) | Every third-party client needs one. Creating it takes a minute and costs nothing: [Create a Spotify app](https://blastbeng.github.io/spotisub/getting-started/spotify-app/). |
| A Subsonic-API server with your music in it | Navidrome, Airsonic, Gonic, … — that is where the playlists are written. |
| `musicBrainzId` tags on your files *(optional)* | Enables exact MBID matching. Without them, only the text comparison can match. |
| Docker *(recommended)*, or Python 3.10 from source | How Spotisub is packaged. |
| Outbound HTTPS to Spotify and MusicBrainz | `accounts.spotify.com`, `api.spotify.com`, `musicbrainz.org`. |

## Quick start (Docker)

**1. Create the Spotify app.** Open the
[Spotify developer dashboard](https://developer.spotify.com/dashboard), create an
app, and add this exact Redirect URI:

```
http://127.0.0.1:5183/callback
```

Copy the Client ID and Client Secret. More detail, with screenshots:
[Create a Spotify app](https://blastbeng.github.io/spotisub/getting-started/spotify-app/).

**2. Create a folder** with a `docker-compose.yml`:

```yaml
name: spotisub

services:
  spotisub:
    container_name: spotisub
    env_file: .env
    image: "blastbeng/spotisub:latest"
    restart: always
    volumes:
      - "./cache:/home/user/spotisub/cache"
    ports:
      - 5183:5183
    healthcheck:
      test: curl -s http://127.0.0.1:5183/api/v1/utils/healthcheck | grep -q 'Ok!' || exit 1
      interval: 30s
      retries: 20
      start_period: 30s
```

**3. Make the `.env` file** next to it — the
[sample](https://github.com/blastbeng/spotisub/blob/dev/.env.sample) documents every
variable. The five that have to be right:

```ini
SPOTIPY_CLIENT_ID=your-client-id
SPOTIPY_CLIENT_SECRET=your-client-secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:5183/callback

SUBSONIC_API_HOST=http://192.168.1.10      # your server, as seen from the container
SUBSONIC_API_PORT=4533
SUBSONIC_API_USER=your-subsonic-user
SUBSONIC_API_PASS=your-subsonic-password
```

**4. Start it and open <http://127.0.0.1:5183/>**:

```bash
docker compose up -d
docker compose logs -f --tail=50     # `docker compose ps` shows the healthcheck
```

Create the dashboard login, click **Authenticate Spotify** (or run
`docker exec -it spotisub ./first_run.sh` to do the OAuth dance inside the
container), then import a playlist from **Playlists → Manage**.

Prefer not to touch compose files? There is an
[interactive installer](https://blastbeng.github.io/spotisub/getting-started/install-script/)
that writes them for you, and a
[manual, step-by-step Docker guide](https://blastbeng.github.io/spotisub/getting-started/docker/)
if you want to understand every line.

## How tracks are matched

| Step | What happens |
|---|---|
| **1. ISRC → MBID** | Each Spotify track carries an ISRC. That is resolved to MusicBrainz recording MBIDs, which are looked up in your library's `musicBrainzId` tags. A hit is added straight away. |
| **2. Text comparison** *(off by default)* | Only when step 1 finds nothing **and** `TEXT_COMAPRE_MATCHING_ENABLED=1`: titles and artists are normalised and compared against the server's search results. |
| **3. Exclusion words** | `EXCLUDED_WORDS` (`acoustic,instrumental,demo` by default) drops candidates **from the text comparison only**. An MBID match is always accepted, because it is an exact identity match. |
| **4. Missing** | Anything still unmatched is stored as a *missing* row and listed on the *Missing* page, where you can ignore it, or ignore its album/artist/playlist. |

The full explanation, including how to fix missing `musicBrainzId` tags, is in
[How matching works](https://blastbeng.github.io/spotisub/guide/matching/).

## Configuration

Everything is an environment variable; the
[reference](https://blastbeng.github.io/spotisub/configuration/environment-variables/)
lists all of them with defaults. The ones that change behaviour:

| Variable | Default | Meaning |
|---|---|---|
| `PLAYLIST_PREFIX` | `Spotisub - ` | Prefix of every playlist written on the server. |
| `ITEMS_PER_PLAYLIST` | `1000` | Maximum tracks per generated playlist. |
| `NUM_USER_PLAYLISTS` | `5` | How many Spotify playlists to import. |
| `TEXT_COMAPRE_MATCHING_ENABLED` | `0` | Enable the fuzzy comparison (**the name is misspelled in the code — copy it as-is**). |
| `EXCLUDED_WORDS` | `acoustic,instrumental,demo` | Comma-separated words that reject a text-comparison candidate. |
| `ARTIST_PLAYLIST_ENABLED` | `0` | Generate a top-tracks playlist for every artist in your library. |
| `PLAYLIST_GEN_SCHED` | `3` | Hours between two Spotify-playlist imports (`0` disables the job). |
| `SAVED_GEN_SCHED` | `2` | Hours between *Liked Songs* refreshes. |
| `ARTIST_TOP_GEN_SCHED` | `1` | Hours between artist top-tracks refreshes. |
| `SCHEDULER_ENABLED` | `1` | `0` stops all scheduled work; manual rescans still work. |
| `LOG_LEVEL` | `20` | Python log level (`10` debug … `50` critical). |
| `SECRET_KEY` | *(auto)* | Signing key for the dashboard session. If unset, one is generated once and stored in `cache/secret_key`. |
| `APPLICATION_ROOT` | *(empty)* | Path prefix when Spotisub lives under a sub-path; see [Reverse proxy](https://blastbeng.github.io/spotisub/configuration/reverse-proxy/). |
| `PUID` / `PGID` | `1000` | Owner of the cache files (and of downloaded music). |

Spotisub runs with a **single** gunicorn worker on purpose: the scheduler lives
inside the process, so raising `workers` would run every job several times.
Scheduler details: [Scheduler](https://blastbeng.github.io/spotisub/configuration/scheduler/).

## Data, cache and backups

The only stateful directory is the one mounted at `/home/user/spotisub/cache`:

| File | Contents |
|---|---|
| `spotisub.db` | Dashboard users and the match cache (playlists, tracks, matched/missing relations, ignore flags). |
| `secret_key` | Auto-generated session key, if `SECRET_KEY` is not set. |
| `spotipy_cache` | The Spotify OAuth token. Delete it to force a re-authentication. |
| `subsonic_cache.pkl` | MBID → song map of your library, rebuilt automatically when the library size changes. |
| `spotisub.log` | Rotating log (1 MB × 5), also streamed to `docker compose logs`. |

Back up that folder and you have backed up Spotisub. Deleting
`subsonic_cache.pkl` is always safe — it is rebuilt on the next run.

## Optional integrations

- **[spotdl](https://blastbeng.github.io/spotisub/integrations/spotdl/)** — download
  the tracks Spotisub could not find in your library, so the next scan completes the
  playlist. Writes into your music folder, so it must be mounted into the container.
- **[Lidarr](https://blastbeng.github.io/spotisub/integrations/lidarr/)** — only
  download an artist that Lidarr already monitors, which is a cheap way to say
  "never download artists I do not care about".

Spotdl is built on [spotDL](https://github.com/spotDL/spotify-downloader); Lidarr
access uses [pyarr](https://github.com/totaldebug/pyarr).

## REST API

Every action the dashboard can perform is also an endpoint under `/api/v1/`, with
interactive Swagger docs at **<http://127.0.0.1:5183/api/v1/docs/>** (namespaces
`generate`, `import`, `utils`; responses are `{"status": "ok"|"ko", "message": …}`).
The healthcheck used by Docker is
`GET /api/v1/utils/healthcheck` → `Ok!`. See
[REST API](https://blastbeng.github.io/spotisub/api/endpoints/).

## Something is broken?

Start with [Troubleshooting](https://blastbeng.github.io/spotisub/help/troubleshooting/),
which covers the failures that come up again and again — a redirect loop between
`/overview/` and `/login`, "no tracks matched" on Navidrome, `401` from the Subsonic
API, Spotify answers `403`, a library scan that seems frozen — and the
[FAQ](https://blastbeng.github.io/spotisub/help/faq/) for the behavioural questions
(Premium, multiple users, what it does to your files).

Then check **System → Logs** in the dashboard: every job logs with the thread id
that ran it, and the whole log is `cache/spotisub.log`.

Nothing helps? [Open an issue](https://github.com/blastbeng/spotisub/issues/new/choose)
with the log excerpt around the failure, your container image tag, and whether your
server is Navidrome or something else. Community: [Discord](https://discord.gg/jXQauuhy5w)
and [Reddit](https://www.reddit.com/r/spotisub/).

> Big libraries and long playlists mean long runs: a full scan of thousands of
> tracks can take hours. This is deliberate — the Spotify and MusicBrainz APIs are
> rate limited and Spotisub paces itself instead of getting throttled.

## Roadmap

The short list of things users keep asking for — each one is an issue, so comment
there rather than opening a duplicate:

- Configure Spotisub from the dashboard instead of environment variables.
- Delete, skip or download a matching track straight from the dashboard.
- An artist allow-list instead of ignoring hundreds of artists one by one.
- Multi-user support with per-user Spotify and Subsonic accounts.
- ListenBrainz / Last.fm as additional playlist sources.

## Contributing

- **Documentation** lives in [`docs/`](docs) and is published at
  <https://blastbeng.github.io/spotisub/> by `.github/workflows/pages.yml`
  (MkDocs Material). Fix a wrong instruction there, not in the wiki — there is no
  wiki any more.
- **Code** follows the existing patterns: Flask blueprints, SQLAlchemy Core,
  `flask_restx` under `/api/v1`, no build step for the frontend.
- **Tests** run with `pytest` and never touch Spotify or your library
  (`tests/_stubs/` stands in for the heavy import-time dependencies).
- **Releases** are built and published only by GitHub Actions: the `release`
  workflow bumps `VERSION`, writes the changelog, merges `dev` into `latest`, tags,
  builds all three architectures and publishes the image. No local tags, no local
  pushes. See [Contributing](https://blastbeng.github.io/spotisub/contributing/).

Container images: `blastbeng/spotisub:latest` (stable), `blastbeng/spotisub:X.Y.Z`
(and `vX.Y.Z`) for a pinned version, `blastbeng/spotisub:dev` for the development
branch. Platforms: `linux/amd64`, `linux/arm64`, `linux/arm/v7`.

## Acknowledgments

Spotisub stands on the shoulders of these projects:

- [Spotipy](https://github.com/spotipy-dev/spotipy) — Spotify Web API client
- [py-sonic](https://github.com/crustymonkey/py-sonic) — Subsonic API client
- [MusicBrainz](https://musicbrainz.org/) — ISRC → MBID resolution
- [Navidrome](https://github.com/navidrome/navidrome) — the server it was built against
- [spotdl](https://github.com/spotDL/spotify-downloader), [Lidarr](https://github.com/Lidarr/Lidarr),
  [pyarr](https://github.com/totaldebug/pyarr) — the optional integrations

## License

[MIT](LICENSE.md).

See [CHANGELOG.md](CHANGELOG.md) for release history.
