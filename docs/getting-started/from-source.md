# Build from source

Use this to run a branch that has fixes or features not in a release yet, or to test
your own changes. You still get a container, you just build it locally.

!!! warning "Local builds are for development"

    Images built on your machine are **not** release artifacts: do not tag them or push
    them to a registry. Releases are built and signed off by CI — see
    [Release history](../release-history.md).

## 1. Clone

```bash
git clone https://github.com/blastbeng/spotisub.git
cd spotisub
git checkout dev      # or your branch
```

## 2. Build

`docker-compose.build.yml` builds `blastbeng/spotisub:latest` from the local checkout:

```bash
docker compose -f docker-compose.build.yml build
```

This compiles every dependency (including `cffi` on 32-bit ARM) and can take several
minutes the first time. It builds for your host architecture only.

## 3. Configure

```bash
cp .env.sample .env
$EDITOR .env
docker compose -f docker-compose.build.yml up -d
```

Or run the `docker-compose.yml` you already have, with the image it just built.

## 4. Seed the Spotify token

Same as a normal install: open <http://127.0.0.1:5183/> and press
**Authenticate Spotify**, or use the terminal fallback:

```bash
docker exec -it spotisub ./first_run.sh
```

## Rebuilding after a change

```bash
git pull
docker compose -f docker-compose.build.yml build
docker compose -f docker-compose.build.yml up -d
```

## Development loop without containers

If you want to edit Python files and see the change immediately, run the app from a
virtualenv instead — see [Run without Docker](no-docker.md). Note that Spotisub has
**no auto-reload**: restart gunicorn after each change.

## Running the checks

The same gates CI runs before a release:

```bash
python3 -m py_compile main.py config.py init.py \
  spotisub/*.py spotisub/helpers/*.py spotisub/threading/*.py
python3 -m pylint spotisub main.py config.py init.py --disable=import-error --fail-under=6
python3 -m pytest -q
```

See [Contributing](../contributing.md) for the commit and pull-request conventions.
