# Manual Docker install

Use this when you want the compose file under your own control, or when the
[installer script](install-script.md) does not fit your environment.

## 1. Create the directory

```bash
mkdir -p /opt/spotisub/cache
cd /opt/spotisub
```

Put it somewhere backed up. The `cache/` folder holds the database, the Spotify token,
the Subsonic index cache and the log.

## 2. Write `.env`

```ini title="/opt/spotisub/.env"
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:5183/callback

SUBSONIC_API_HOST=http://127.0.0.1
SUBSONIC_API_PORT=4533
SUBSONIC_API_USER=your_user
SUBSONIC_API_PASS=your_password

ITEMS_PER_PLAYLIST=1000
SCHEDULER_ENABLED=1
LOG_LEVEL=20
```

The full list, with defaults, is in
[Environment variables](../configuration/environment-variables.md).

!!! danger "Quote nothing, escape nothing — except in compose"

    `.env` files are read literally by Docker Compose: no quotes needed, no `$`
    expansion wanted. A password containing `$` must be escaped as `$$` **only** if you
    inline it in `docker-compose.yml` instead of `.env`.

## 3. Write `docker-compose.yml`

```yaml title="/opt/spotisub/docker-compose.yml"
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
      - "5183:5183"
    healthcheck:
      test: curl -s http://127.0.0.1:5183/api/v1/utils/healthcheck | grep -q 'Ok!' || exit 1
      interval: 30s
      retries: 20
      start_period: 30s
```

Pin `image:` to a release (`blastbeng/spotisub:0.3.8`) if you do not want upgrades to
happen on `docker compose pull`.

## 4. First start

```bash
docker compose up -d
docker compose logs -f --tail=50
curl -fsS http://127.0.0.1:5183/api/v1/utils/healthcheck   # Ok!
```

Open <http://127.0.0.1:5183/> and follow
[3. Log in to Spotify](first-run.md).

## File ownership (PUID / PGID)

The container remaps its internal user to `PUID`/`PGID` (default `1000:1000`) and
`chown`s `cache/` accordingly. If your host user is not `1000`, set it:

```yaml
    environment:
      - PUID=1001
      - PGID=1001
```

Otherwise `cache/` ends up owned by a user id that does not exist on the host.

## Behind a reverse proxy

Set `APPLICATION_ROOT` and see [Reverse proxy](../configuration/reverse-proxy.md).
