# Login and security

Spotisub is designed for a home network. It has one local account, it speaks plain HTTP,
and it holds credentials to two other services. Treat it accordingly.

## The local account

- Created on first visit (`/register`); only one account can ever exist.
- Its password is stored **hashed** in `cache/spotisub.db`.
- It exists to stop other people on your LAN from using your instance; it is not
  multi-user. Every visitor shares the same Spotify and Subsonic credentials.
- `Logout` clears the session.

Lost the password? There is no reset flow. Delete the row (container stopped) or delete
`cache/spotisub.db` and re-register — the latter also loses the match history, so prefer
the former:

```bash
docker compose stop spotisub
docker run --rm -it -v /opt/spotisub/cache:/c keinos/sqlite3 \
  sqlite3 /c/spotisub.db 'DELETE FROM user;'
docker compose start spotisub
```

## Sessions

Sessions are signed with `SECRET_KEY`. If it is unset, Spotisub generates one once and
stores it in `cache/secret_key` (mode `0600`), so restarts no longer log everybody out.
If you delete `cache/`, sessions die with it.

!!! note "Stale cookies"

    If a session cookie refers to a key that no longer exists, Spotisub detects it on the
    next request, clears the cookie and sends you to the login page instead of bouncing
    between `/overview/` and `/login`. If you still see a redirect loop, clear the site's
    cookies once.

## `LOGIN_DISABLED`

`LOGIN_DISABLED=1` removes authentication completely: anyone who can reach the port gets
full access, including the Subsonic credentials through the UI.

!!! danger "Only for local development"

    Never set it on a machine reachable from anything but `localhost`. It is not needed
    for normal use, including with a reverse proxy.

## Exposing Spotisub to the internet

If you must, do all of these:

1. Put it behind a reverse proxy with **HTTPS**, and set `APPLICATION_ROOT` if it lives
   under a sub-path ([Reverse proxy](reverse-proxy.md)).
2. Register the HTTPS callback in the Spotify app
   (`https://your.host/callback`) — Spotify only exempts loopback from HTTPS.
3. Give the proxy its own authentication (basic auth, an SSO forward-auth) in addition
   to Spotisub's login, or restrict by source IP.
4. Keep `LOGIN_DISABLED=0`.

## Secrets that Spotisub stores

| Secret | Where |
|---|---|
| Spotify client ID / secret | `.env` (plain text, your responsibility) |
| Spotify refresh token | `cache/spotipy_cache` (contains a live token — treat as a password) |
| Subsonic credentials | `.env` |
| Lidarr API key | `.env` |
| Local account password | hashed in `cache/spotisub.db` |
| Flask session key | `cache/secret_key` or `.env` |

Back up `cache/` as you would back up a password store.

## Container hardening (optional)

```yaml
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
```

`read_only` works because only `cache/` needs to be writable; keep that volume. The
container already runs as an unprivileged user after the entrypoint remaps it to
`PUID`/`PGID`.
