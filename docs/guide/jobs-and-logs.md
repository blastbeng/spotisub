# Jobs and logs

**System** in the sidebar has the two diagnostic pages you will actually use.

## Tasks

`/tasks` lists every registered job with:

| Column | Meaning |
|---|---|
| Type | The job id, e.g. `saved_tracks`, `user_playlists`, `reimport_all` |
| Args | The playlist name, when the job is per-playlist |
| Next execution | When it will run next (`Manual` for `reimport_all`) |
| Interval | Configured interval in hours |
| Running | `1` while work is in progress |

A job that shows `Running = 1` for hours is not necessarily stuck: a first full import
genuinely takes that long. Compare with [Logs](#logs) before restarting anything.

If a job is missing from this list, it is disabled — either its interval is `0` or its
feature flag is off (for example `ARTIST_PLAYLIST_ENABLED=0` for artist jobs).

## Logs

`/logs` streams `cache/spotisub.log` live over a WebSocket, in the browser, with no
`docker logs` needed. The same file is on disk, rotated at 1 MB with 5 backups.

Useful patterns to look for:

| Line contains | Meaning |
|---|---|
| `Searching <title> in your music library` | The importer is working on that track |
| `was not found in the library via MBID` | No `musicBrainzId` match; text comparison will be tried only if enabled |
| `Found excluded word` | `EXCLUDED_WORDS` rejected a text-comparison candidate |
| `not found in the MusicBrainz database` | The ISRC is not in MusicBrainz; nothing to do locally |
| `Transient error contacting MusicBrainz` | Network hiccup; it retries up to 3 times |
| `429` / `rate limit` | Spotify throttling: lower the frequency, do not remove sleeps |
| `<job_id>_<uuid>` in a thread name | Which job is logging; the UUID is the playlist |

Set `LOG_LEVEL=10` (`DEBUG`) temporarily when diagnosing a match problem; it is very
verbose, so put it back to `20` afterwards.

## Check Subsonic

Sidebar → **Check Subsonic** performs a Subsonic `ping`. Use it whenever the dashboard is
empty or imports produce nothing: it separates "credentials/path wrong" from "matching
wrong".

## Health endpoint

For monitoring, use the same check the container healthcheck uses:

```bash
curl -fsS http://127.0.0.1:5183/api/v1/utils/healthcheck   # Ok!
```

!!! note "Backups of the log"

    The log grows fast during an import. If you are collecting it for a bug report, grab
    the relevant window (`docker compose logs --since 30m`) instead of the whole file.
