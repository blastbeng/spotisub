# Rescan and reimport

A rescan re-reads a Spotify playlist and rewrites the corresponding Subsonic playlist.
Nothing is cached away: what you see in the interface is the result of the last import.

## Rescan one playlist

Open the playlist and press :material-refresh: **Rescan and reimport** in the toolbar,
then confirm.

## Rescan everything

On the dashboard, **Rescan** offers *all playlists*. That runs the `reimport_all` job:
every playlist Spotisub knows about is re-read and rewritten, honouring the same ignore
flags.

!!! warning "Only one full reimport at a time"

    `reimport_all` refuses to start if it is already running; the interface says so
    instead of queueing a second copy. The same applies to a per-playlist rescan of a
    playlist that is currently being imported.

## What a rescan does, step by step

1. Reads the playlist's tracks from Spotify (50 at a time).
2. For each track: fills in missing album/ISRC/URI metadata.
3. Looks up ISRC → recording MBIDs on MusicBrainz (rate-limited, with retries).
4. Looks each MBID up in the Subsonic index cache, or falls back to text comparison if
   `TEXT_COMAPRE_MATCHING_ENABLED=1`.
5. Stores every result — matched *and* missing — in `cache/spotisub.db`.
6. Creates or updates the Subsonic playlist with the matched song ids.

## Self-healing behaviour worth knowing

- If the playlist is **deleted on the server**, Spotisub notices, drops the stale
  relations and re-creates it on the next import.
- If a playlist matches **nothing**, the Subsonic playlist is removed instead of being
  left empty; the row stays so you can fix matching and rescan.
- If a Spotify playlist disappears, the `remove_deleted_playlists` job (every 8 hours)
  cleans up its rows.

## When to rescan

| Situation | Action |
|---|---|
| You added a playlist on Spotify | Nothing: `init_jobs` discovers it within an hour, then import it |
| You added tracks to a playlist | Nothing: the next scheduled import catches it |
| You fixed tags / added files | Rescan the playlist (and rescan the library in your music server first) |
| You changed `EXCLUDED_WORDS` or text comparison | Rescan the affected playlists |
| You un-ignored something | Rescan |
| You upgraded Spotisub | Nothing; imports resume on schedule |

## How long it takes

The importer sleeps about 0.25 s after each Spotify object fetch and 2 s between
pagination pages, on purpose: without it, Spotify rate-limits (429) the whole
installation. A 1000-track playlist therefore takes a few minutes even when everything
matches immediately. Do not disable the sleep to "make it faster" — the work simply
fails.

MusicBrainz is the other bottleneck: its ISRC lookups are sequential and rate-limited to
roughly one request per second, and Spotisub does not cache ISRC results. A very large
library can therefore take hours on **every** full reimport. Rescan one playlist while
you tune matching, not all of them.
