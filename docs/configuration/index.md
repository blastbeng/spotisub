# Configuration

Spotisub is configured entirely with environment variables: there is no config file and
no settings screen. With Docker that means the `env_file: .env` line in your compose
file; without Docker it means exported variables.

<div class="grid cards" markdown>

-   [**Environment variables**](environment-variables.md) — The full reference, with defaults and which are mandatory.
-   [**Scheduler**](scheduler.md) — What runs when, and how to turn each job off.
-   [**Reverse proxy**](reverse-proxy.md) — Nginx, Caddy and Traefik in front of Spotisub.
-   [**Login and security**](security.md) — The local account, sessions, TLS, exposure.
-   [**Upgrading**](upgrading.md) — Safe upgrade, rollback, and what changed between versions.

</div>

## Changing a value

1. Edit `.env`.
2. Recreate the container so the new environment is read:

   ```bash
   docker compose up -d --force-recreate
   ```

   A `restart` is **not** enough: environment variables are set at container creation.

## The three values people get wrong

| Value | Correct form |
|---|---|
| `SPOTIPY_REDIRECT_URI` | Must equal the URI registered in the Spotify app, e.g. `http://127.0.0.1:5183/callback` |
| `SUBSONIC_API_HOST` | Includes the scheme: `http://navidrome`, not `navidrome` |
| `SUBSONIC_API_BASE_URL` | A **path prefix only**: `/music` when Navidrome's `ND_BASEURL` is `/music`; no host, no trailing `/rest` |
