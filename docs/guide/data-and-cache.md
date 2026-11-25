# Data, cache and backups

Everything Spotisub knows lives in one folder: `cache/` (mounted at
`/home/user/spotisub/cache` in the container, or `$CACHE_DIR`). Your music is never
modified by Spotisub — except by the optional [spotdl](../integrations/spotdl.md)
integration.

## What is in `cache/`

| File | What it is | Lose it and... |
|---|---|---|
| `spotisub.db` | SQLite database: your local account, generated playlists, matched/missing tracks, ignore flags | You lose the match history and your account; playlists are rebuilt on the next import |
| `spotipy_cache` | The Spotify OAuth token | You press **Authenticate Spotify** once more |
| `secret_key` | Flask session key (if `SECRET_KEY` is unset) | Everyone is logged out; it is regenerated |
| `subsonic_cache.pkl` | Index of `musicBrainzId → song` for your library | Rebuilt automatically, once |
| `spotify_object_cache.pkl` | Cached Spotify track metadata (12 h TTL) | Refetched, slower first import |
| `spotisub.log` (+ `.1` … `.5`) | Rotating application log, 1 MB each | Nothing |

Deleting `cache/` is the **factory reset**: after a restart you register a new local
account and reconnect Spotify. It is also the fix for a corrupted database — but try
backing it up first.

## Backup

Stop nothing; SQLite in this configuration survives a file copy of a quiescent database.
The reliable way:

```bash
docker compose stop spotisub
tar czf spotisub-cache-$(date +%F).tar.gz -C /opt/spotisub cache
docker compose start spotisub
```

Copy the archive somewhere else. That is a complete backup: configuration is in `.env`,
everything stateful is in `cache/`.

## Restore or move to another machine

```bash
docker compose down
tar xzf spotisub-cache-2026-11-25.tar.gz -C /opt/spotisub   # replaces cache/
# copy .env too, and keep SPOTIPY_REDIRECT_URI valid for the new address
docker compose up -d
```

If the host name or port changes, the redirect URI changes with it: update both
`.env` and the Spotify app settings.

## The database, briefly

You do not normally need to look inside, but for a bug report it helps to know that:

- playlists are rows in `playlist_info` (name, type, Spotify URI, ignored),
- every Spotify song/artist/album is stored once, with its URI,
- `subsonic_spotify_relation` is the per-playlist match: Subsonic song id, Subsonic
  artist id, or both empty (= missing),
- `ignored` exists on songs, albums, artists, relations and playlists.

Opening it read-only:

```bash
docker run --rm -it -v /opt/spotisub/cache:/c keinos/sqlite3 \
  sqlite3 /c/spotisub.db '.tables'
```

!!! danger "Do not edit the database while Spotisub runs"

    There is no migration path in this version and no locking against an external
    writer. Stop the container before changing anything by hand, and take a copy first.

## Disk usage

The database is small (a few tens of MB for large libraries); the Subsonic index and the
Spotify cache are bounded. The log is capped at 6 MB. Spotdl downloads are the only
thing that can grow without limit — they go to your music folder, not to `cache/`.
