# Contributing

Spotisub is a small Flask application kept deliberately old-fashioned: no npm, no
bundler, no frontend framework. Pull requests against **`dev`** are welcome.

## Getting a development environment

```bash
git clone https://github.com/blastbeng/spotisub.git
cd spotisub
git checkout dev
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

Run it with the same command the container uses:

```bash
mkdir -p cache
gunicorn -k eventlet -b 0.0.0.0:5183 -c config_gunicorn.py spotisub:spotisub
```

There is **no auto-reload**: restart after each change. See
[Run without Docker](getting-started/no-docker.md) for the details and the
`SECRET_KEY` / `CACHE_DIR` notes.

## Checks before opening a pull request

```bash
python3 -m py_compile main.py config.py init.py \
  spotisub/*.py spotisub/helpers/*.py spotisub/threading/*.py
python3 -m pylint spotisub main.py config.py init.py --disable=import-error --fail-under=6
python3 -m pytest -q
```

CI runs the same three on Python 3.10, plus a multi-architecture image build on `dev`.
A pull request that fails them will not be merged.

## Conventions

**Commits** — `area: imperative summary`, with `Fixes #123` in the body when it closes an
issue. Areas in use: `generator`, `routes`, `database`, `subsonic`, `spotify`, `docker`,
`ci`, `docs`, `tests`.

**Branches** — `fix/<issue>-<slug>`, `feat/<slug>`, `chore/<slug>`, `docs/<slug>`, all
targeting `dev`.

**Python** — match the existing style: module and function docstrings (pylint requires
them), `snake_case`, lazy `%s` logging arguments prefixed with the thread id, SQLAlchemy
**Core** (`dbms.<table>`) rather than the ORM for anything except `User`. Target the
syntax the 3.10 image supports.

**Logging** — inside jobs and threads, always prefix with the thread ident:

```python
logging.info('(%s) Searching %s in your music library',
             str(threading.current_thread().ident), track['name'])
```

**Templates and JS** — Jinja, Bootstrap 3, vanilla JS. Route URLs are positional; add a
new route variant instead of reordering an existing one.

**Behaviour that must not change silently** — the matching pipeline, the
`subsonic_song_id IS NULL AND subsonic_artist_id IS NULL` definition of "missing", the
ignore flags, and the thread naming convention (`<job_id>_<uuid>`) the UI relies on.
Changes there need a test and a note in the changelog.

## Database changes

There is **no working migration path** in this version. Do not add, rename or drop a
column in a pull request without discussing it first: the release notes have to carry a
manual `ALTER TABLE` and a rollback. Prefer additive columns with a default.

## Documentation

Two files, two jobs:

| File | Contains |
|---|---|
| `README.md` | What Spotisub is **now**: install pointer, features, matching, links |
| `CHANGELOG.md` | Release history only, written by the release workflow |
| `docs/` (this site) | Everything else: guides, configuration, troubleshooting |

If you change user-facing behaviour, update `docs/` in the same pull request. Do not put
"what's new" text in `README.md`.

Building the site locally:

```bash
pip install -r requirements-docs.txt
mkdocs serve        # http://127.0.0.1:8000/spotisub/
```

## Releasing

Releases are built, tagged and published **only** by GitHub Actions. The maintainer
dispatches the `release` workflow with a `dry_run` first, reads the generated changelog
section, then runs it for real. Nothing is built or pushed from a workstation, and
`v*` tags are never created by hand.

What a release does: bumps `VERSION` in `spotisub/database.py`, appends the `VERSIONS`
history, prepends the `CHANGELOG.md` section, commits `chore(release): vX.Y.Z`, merges
`dev` into `latest`, tags, builds all three architectures, verifies the image digests and
the version inside the image, creates the GitHub Release, and finally republishes this
documentation site from the release commit so that the new changelog section is live.
