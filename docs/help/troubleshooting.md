# Troubleshooting

## Nothing loads / connection refused

- Is the container running? `docker compose ps`
- Is port 5183 published? The default compose maps `5183:5183`; if you changed it,
  browse to the host port, not to 5183 inside the container.
- `docker compose logs --tail=100` — if the last line is a Python traceback, the
  container is restarting in a loop. The most common causes: a malformed `.env` value
  (`SUBSONIC_API_PORT=abc`), or a `cache/` owned by another uid (see
  [Permission denied](#permission-denied-on-cache)).

## The healthcheck fails but the container is up

```bash
docker exec -it spotisub curl -s http://127.0.0.1:5183/api/v1/utils/healthcheck
```

- If this prints `Ok!`, the container is fine and the **compose healthcheck command** is
  wrong (an old compose file used `/utils/healthcheck`). Fix the path to
  `/api/v1/utils/healthcheck`.
- If it hangs, the app is still booting or blocked on its first Subsonic call. Wait a
  minute, then read the log.

## Redirect loop between `/overview/` and `/login`

A stale session cookie: the browser holds a cookie signed with a key that no longer
exists (typically because `cache/` was deleted or the secret changed).

1. Spotisub clears such cookies automatically on the next request and sends you to
   `/login`. If it does not, clear cookies for that host once.
2. Keep it from happening again: set a fixed `SECRET_KEY` in `.env`, or at least keep
   `cache/secret_key`.

## `INVALID_CLIENT: Invalid redirect URI`

`SPOTIPY_REDIRECT_URI` and the Spotify app's redirect URI differ. They must match
exactly. Copy the value from `.env` into the Spotify dashboard, save, and recreate the
container.

Note that `http://` is only accepted for `127.0.0.1`/`localhost`; anything else must be
`https://` and publicly reachable from your browser.

## Spotify answers `403` / "Premium required"

**Authenticate Spotify** fails, or every import stops with `403 Forbidden` and
`Your application is blocked from accessing the Web API since you do not have a Spotify
Premium subscription`.

Spotify's [February 2026 developer
policy](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security)
makes Premium mandatory for Development Mode: the account that owns the Client ID must
have an active subscription. Spotisub asks for read-only scopes and cannot work around
it — swap in credentials from a Premium account, or upgrade that one.

A `403` on a **single** playlist is something else: Spotify refuses that playlist to your
app (for example an editorial or region-locked one). Spotisub logs it and skips that
playlist, the rest of the import continues.

## Empty dashboard

The initial playlist scan is wrapped in a broad `try/except` on purpose, so a failure
there produces an empty list instead of a crash.

1. **Check Subsonic** in the sidebar.
2. Check `SUBSONIC_API_HOST` — it must include `http://` or `https://`.
3. Check `SUBSONIC_API_BASE_URL` — only the path prefix (`/music`), no host.
4. Check `SUBSONIC_API_PORT` — Navidrome 4533, Airsonic 4040.
5. Look in **System → Logs** for `search2 failed` or a connection error.
6. Restart the container: the scan runs at startup.

## Playlists created but empty

Nothing matched. That is a matching problem, not a playlist problem:
[Missing tracks](../guide/missing-tracks.md).

Also check [why only one playlist per interval is imported](../configuration/scheduler.md#one-random-playlist-per-interval-read-this):
with many playlists, most of them may simply not have had their turn yet. Use
**Rescan → all playlists** to force a full pass.

## Subsonic returns 401 / "40" / wrong credentials

Click **Check Subsonic** in the sidebar first. An authentication problem now says
*Subsonic Authentication Failed* and quotes the server's own reason (for example
`Wrong username or password`, error code 40) plus the URL and user it used, so you do
not have to guess whether the server is down or the password is wrong.

Spotisub authenticates with the Subsonic salted token scheme first and, if the server
rejects it, retries once with the plain password scheme. That fallback covers servers
older than Subsonic API 1.13, which answer error 40 to the token scheme even when the
password is correct.

If the check still fails:

- Verify with the server directly, bypassing Spotisub. Use `--data-urlencode` so a
  password with `&`, `+`, `%` or `#` is sent intact:

  ```bash
  curl -s --get "http://127.0.0.1:4533/rest/ping.view" \
    --data-urlencode "u=USER" --data-urlencode "p=PASS" \
    --data-urlencode "v=1.16.1" --data-urlencode "c=test"
  ```

  You must get `<subsonic-response status="ok"`. If this fails, the problem is the
  credentials or the port, not Spotisub.
- Check what Spotisub actually receives. In an `.env` file an unquoted `#` starts a
  comment and a `$` may be interpolated by Docker Compose, so the container can get a
  truncated password that still works when you type it in a browser. Quote the value
  (`SUBSONIC_API_PASS='pa#ss$word'`) or set it in the Compose `environment:` block.
  Trailing spaces after the value have the same effect.
- Behind a path-mounted server, `SUBSONIC_API_BASE_URL` must be the **path only**
  (`/music`), and the server must answer on `…/music/rest/ping.view`.
- Self-signed HTTPS: `SUBSONIC_API_VERIFY_SSL=0`.

## Tracks are "missing" but exist in the library

Work through [Missing tracks](../guide/missing-tracks.md). The short version: the
`musicBrainzId` tag is missing, or the ISRC is not in MusicBrainz, or text comparison is
off (it is off by default).

One more subtle case: an album or artist **ignored** in Spotisub makes all of its tracks
look "matched but excluded", not "missing". Check for ignore icons on the album/artist
page before concluding the matching is broken.

## Spotify rate limiting (HTTP 429)

Spotisub already sleeps between calls. If you still hit 429:

- lower the number of playlists imported per interval (raise `PLAYLIST_GEN_SCHED`),
- do not run several Spotisub instances against one Spotify app,
- do not run a full reimport while the scheduled jobs are also running
  (`SCHEDULER_ENABLED=0` during a one-off full import is a clean way).

## MusicBrainz is slow or unreachable

ISRC lookups are sequential and rate-limited. Transient network errors are retried three
times with backoff; a `404`/`400` means "not in MusicBrainz" and is not retried. If every
lookup fails, check DNS and outbound HTTPS from the container:

```bash
docker exec -it spotisub python3 -c "import musicbrainzngs; print('ok')"
docker exec -it spotisub curl -sI https://musicbrainz.org/ws/2/
```

## Permission denied on `cache/`

The container runs as `PUID:PGID` (default `1000:1000`) and `chown`s `cache/` at startup.
If your host user has another id — or `cache/` was created by root — fix the ownership
and set the ids:

```bash
sudo chown -R 1001:1001 /opt/spotisub/cache
# .env: PUID=1001, PGID=1001
docker compose up -d --force-recreate
```

## "Playlist has been deleted" on rescan

The Subsonic playlist no longer exists on the server (you deleted it there). Spotisub
detects it, drops the stale relations and recreates the playlist on the next attempt.
A second rescan normally succeeds.
