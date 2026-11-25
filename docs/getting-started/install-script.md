# Install with the script

The installer asks a handful of questions, writes a `docker-compose.yml`, pulls the
image and runs Spotisub's Spotify authorisation once. It is a shell script; read it
before running it if you like:

```bash
curl -fsSLO https://raw.githubusercontent.com/blastbeng/spotisub/dev/install_scripts/install_spotisub_docker.sh
less install_spotisub_docker.sh
```

## Run it

```bash
chmod +x install_spotisub_docker.sh
./install_spotisub_docker.sh
```

You will be asked for:

| Question | Notes |
|---|---|
| Install directory | Must be empty or non-existent. `cache/` is created inside it. |
| Spotify Client ID / Secret | From your [Spotify app](spotify-app.md). The secret is read without echo. |
| Subsonic address | `http://127.0.0.1` for a local server, or `http://navidrome` for a container |
| Subsonic port | `4533` for Navidrome, `4040` for Airsonic, ... |
| Subsonic path | Only if your server runs under a sub-path (Navidrome `ND_BASEURL`) |
| Subsonic user / password | Read without echo |

Afterwards the script:

1. pulls `blastbeng/spotisub:latest`,
2. starts it once and runs `first_run.sh` so you can paste the Spotify authorisation
   URL into a terminal,
3. leaves the container running on port `5183`.

Open <http://127.0.0.1:5183/>.

!!! note "The redirect URI the script registers"

    The script writes `SPOTIPY_REDIRECT_URI=http://127.0.0.1:5183/callback`. Register
    exactly that string in your Spotify app.

## Managing the install afterwards

```bash
cd /your/install/dir
docker compose logs -f --tail=100     # follow the log
docker compose restart                # restart
docker compose pull && docker compose up -d   # upgrade to the newest release
```

## If something goes wrong

The script is intentionally simple and does not validate your Subsonic credentials.
Use [Troubleshooting](../help/troubleshooting.md), or fall back to
[the manual install](manual-docker.md) where every value is visible in a file you can
edit.
