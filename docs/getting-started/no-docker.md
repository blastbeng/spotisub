# Run without Docker

Spotisub is a normal Flask application; Docker is only packaging. This path is for
people who prefer a virtualenv or a systemd unit.

!!! note "Python version"

    The official image uses **Python 3.10**. The pinned dependencies
    (`sqlalchemy==2.0.7`, `werkzeug==2.2.2`, `Flask~=2.2.2`, `eventlet==0.37`) are known
    to work there. Python 3.12+ is not tested and may fail to import.

## 1. Get the code

```bash
git clone https://github.com/blastbeng/spotisub.git
cd spotisub
```

## 2. Virtualenv and dependencies

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

`ffmpeg` is a system dependency of the optional spotdl integration; install it with
your package manager, not with pip.

## 3. Configuration

The application reads plain environment variables. Create `cache/` and export them:

```bash
mkdir -p cache
cp .env.sample .env
$EDITOR .env
set -a; . ./.env; set +a
```

`SECRET_KEY` may be left empty: Spotisub then generates one once and stores it in
`cache/secret_key`, so sessions survive restarts.

## 4. Start it

The container runs gunicorn with the **eventlet** worker (required by SocketIO) and a
single worker (the scheduler lives inside the process — never raise `workers`):

```bash
gunicorn -k eventlet -b 0.0.0.0:5183 -c config_gunicorn.py spotisub:spotisub
```

Check it:

```bash
curl -fsS http://127.0.0.1:5183/api/v1/utils/healthcheck
# Ok!
```

`python main.py` is **not** the entry point; `main.py` only provides the Flask CLI and
shell context.

## 5. systemd (optional)

```ini title="/etc/systemd/system/spotisub.service"
[Unit]
Description=Spotisub
After=network-online.target

[Service]
Type=simple
User=spotisub
WorkingDirectory=/opt/spotisub
EnvironmentFile=/opt/spotisub/.env
ExecStart=/opt/spotisub/.venv/bin/gunicorn -k eventlet -b 0.0.0.0:5183 -c config_gunicorn.py spotisub:spotisub
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now spotisub
journalctl -u spotisub -f
```

## Notes and gotchas

- Run from the repository root: `CACHE_DIR` and the Spotify token path are resolved
  relative to the working directory (`cache/`).
- Use one process. Multiple gunicorn workers would run multiple schedulers and import
  everything several times.
- The SQLite file is `cache/spotisub.db`; back it up together with
  `cache/spotipy_cache`, `cache/subsonic_cache.pkl` and `cache/secret_key`.
