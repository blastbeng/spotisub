# Scheduler

Spotisub imports on its own, inside the web process. There is no cron, no worker queue
and no external scheduler: a single APScheduler instance lives in the gunicorn process.

!!! danger "Never run more than one worker"

    Because the scheduler is in-process, raising gunicorn's `workers` would run the same
    imports several times in parallel against the same database. The shipped
    configuration uses one worker on purpose.

## Registered jobs

| Job id | Interval | What it does |
|---|---|---|
| `init_jobs` | 1 h | Discovers new Spotify playlists and creates **empty** playlist rows |
| `scan_library` | 24 h | Discovers artists in your library and creates their (optional) playlists |
| `remove_deleted_playlists` | 8 h | Drops rows for playlists deleted outside Spotisub |
| `saved_tracks` | `SAVED_GEN_SCHED`, 2 h | Imports your **Liked Songs** |
| `user_playlists` | `PLAYLIST_GEN_SCHED`, 3 h | Imports **one random** Spotify playlist |
| `artist_top_tracks` | `ARTIST_TOP_GEN_SCHED`, 1 h | Imports **one random** artist's top tracks (only with `ARTIST_PLAYLIST_ENABLED=1`) |
| `reimport_all` | manual | Rescan every playlist at once |

`init_jobs` and `scan_library` also run **once at every container start**, which is why
a restart refreshes the playlist list. The import jobs do not: an interval job first
fires one full interval after it is registered. If you want a playlist imported right
now, press **Rescan** — do not restart the container and wait.

## "One random playlist per interval" — read this

`user_playlists` and `artist_top_tracks` do **not** loop over everything each run. Each
run picks one playlist (or one artist) and imports it. That is a deliberate anti-rate-limit
design, and it has two consequences:

- With 40 Spotify playlists and a 3-hour interval, a given playlist is refreshed roughly
  every 5 days on average.
- With 800 artists and a 1-hour interval, top-tracks playlists take weeks to fill in.

If you want everything imported **now**, use **Rescan → all playlists** on the dashboard
(`reimport_all`), which does loop over everything. Then let the scheduler keep it fresh.

## Disabling a job

Set its interval to `0`:

```ini
SAVED_GEN_SCHED=0      # stop automatic Liked Songs imports
PLAYLIST_GEN_SCHED=0   # stop automatic user-playlist imports
```

Intervals are read when the job is registered, which happens at startup, so
**recreate the container** after changing them:

```bash
docker compose up -d --force-recreate
```

To stop *everything* automatic — for example while you reorganise your library — use:

```ini
SCHEDULER_ENABLED=0
```

With the scheduler paused, playlists are only touched when you press Rescan or call the
[REST API](../api/endpoints.md).

## Intervals: how to choose

| Library size | Suggestion |
|---|---|
| A handful of playlists, small library | Defaults are fine |
| Large library, slow MusicBrainz passes | Raise `PLAYLIST_GEN_SCHED` to `6`–`12` and use `reimport_all` occasionally |
| Artist playlists enabled | Keep `ARTIST_TOP_GEN_SCHED` at `1` or disable the feature; lower it only if you accept the load |

Lowering an interval below `1` is not supported: the unit is whole hours.

## Overlap protection

- Each job has `max_instances=1`, so a long import is not started twice.
- A manual rescan of the same playlist is refused while that playlist is being imported.
- `reimport_all` refuses to start while it is already running.

The interface reports in-flight work in **System → Tasks** and **System → Logs**.
