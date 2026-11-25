# 2. Install with Docker

Spotisub is distributed as a multi-architecture container image:
`linux/amd64`, `linux/arm64` and `linux/arm/v7` (Raspberry Pi 2/3/4 on 32-bit).

You need Docker with the Compose plugin (`docker compose version` should print
something). Any recent Docker Engine works.

## The two-minute way

```bash
mkdir -p /opt/spotisub && cd /opt/spotisub
curl -fsSLO https://raw.githubusercontent.com/blastbeng/spotisub/dev/docker-compose.yml
curl -fsSLO https://raw.githubusercontent.com/blastbeng/spotisub/dev/.env.sample
mv .env.sample .env
```

Now open `.env` and fill in **at minimum** these values:

| Variable | What to put there |
|---|---|
| `SPOTIPY_CLIENT_ID` | from [step 1](spotify-app.md) |
| `SPOTIPY_CLIENT_SECRET` | from [step 1](spotify-app.md) |
| `SPOTIPY_REDIRECT_URI` | `http://127.0.0.1:5183/callback` for a local install |
| `SUBSONIC_API_HOST` | for example `http://127.0.0.1` or `http://navidrome` |
| `SUBSONIC_API_PORT` | for example `4533`; may be left empty to infer 80/443 |
| `SUBSONIC_API_USER` | your music server user |
| `SUBSONIC_API_PASS` | your music server password |

Then start it:

```bash
docker compose up -d
docker compose logs -f --tail=50
```

You should see Spotisub starting and, after a few seconds:

```bash
curl -fsS http://127.0.0.1:5183/api/v1/utils/healthcheck
# Ok!
```

Open <http://127.0.0.1:5183/> in your browser. Continue with
[3. Log in to Spotify](first-run.md).

## What the compose file does

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

- `env_file: .env` — all configuration is environment variables.
- `./cache` — the SQLite database, the Spotify token, the Subsonic cache and the log
  live here. **Back up this folder**; deleting it loses your account and the match
  history, not your music.
- `5183:5183` — the web interface. Nothing else is exposed.

## Which image tag?

| Tag | Meaning |
|---|---|
| `latest` | The current stable release. Recommended. |
| `X.Y.Z` (also `vX.Y.Z`, `X.Y`, `X`) | A pinned release, for reproducible installs. Preferred for unattended servers. |
| `dev` | Built from the development branch on every push: newest features, occasionally broken. |

Every published image is multi-arch and built by CI; see
[Release history](../release-history.md).

## Running next to Navidrome

If Navidrome (or Airsonic, Gonic, ...) is already a container, put Spotisub on the same
network and address the server by service name — see
[Navidrome](../integrations/navidrome.md). Do **not** use `localhost` inside the
Spotisub container.

## Next

[:octicons-arrow-right-24: 3. Log in to Spotify](first-run.md)
