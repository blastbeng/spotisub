"""Shared pytest fixtures/setup for the spotisub test suite.

Importing anything under the `spotisub` package for real (as opposed to
re-implementing its logic under test) means importing spotisub/__init__.py,
which unconditionally builds the whole Flask app, registers routes.py, and
transitively imports spotisub.generator -> spotisub.helpers.spotipy_helper /
subsonic_helper -> several third-party packages (flask_bootstrap,
flask_restx, flask_apscheduler, flask_socketio, pygtail, spotdl) that have
nothing to do with the logic under test. Those packages are either
unmaintained/hard to install against a modern Python, or (spotdl) pull in a
heavy yt-dlp dependency chain purely because
spotisub.helpers.subsonic_helper imports spotisub.helpers.spotdl_helper
unconditionally, which in turn constructs a real Spotdl client at import
time regardless of whether SPOTDL_ENABLED is set.

To keep this suite runnable without installing that unrelated stack, and
without touching any real network service, tests/_stubs/ provides minimal
stand-ins for exactly those modules (see each stub file for what it's for
and why it's safe to fake). Everything a given test actually touches is
imported and exercised for real; only the unrelated import-time
dependencies listed above are faked out.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_STUBS_DIR = Path(__file__).resolve().parent / "_stubs"

# _STUBS_DIR first so its fakes win even if a real (but incompatible/heavy)
# version of one of those packages happens to be installed.
for _path in (str(_STUBS_DIR), str(_REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

# spotisub/__init__.py and its helpers read these from the environment at
# *import* time (module-level side effects: connecting a libsonic.Connection,
# raising if Spotify creds look unset, etc.), so they must be set before the
# first `import spotisub` anywhere in the test session -- which can happen
# as early as test collection, before any fixture runs.
os.environ.setdefault("SUBSONIC_API_HOST", "http://subsonic.invalid")
os.environ.setdefault("SUBSONIC_API_USER", "test-user")
os.environ.setdefault("SUBSONIC_API_PASS", "test-pass")
os.environ.setdefault("SUBSONIC_API_PORT", "4040")
# Non-empty dummy values only -- spotipy_helper.get_secrets() just checks
# these are non-empty at import time; no real Spotify auth happens unless a
# test calls out to spotipy itself, which none in this suite do.
os.environ.setdefault("SPOTIPY_CLIENT_ID", "test-client-id")
os.environ.setdefault("SPOTIPY_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("SPOTIPY_REDIRECT_URI", "http://localhost/callback")

# config.py hardcodes its SQLite path relative to the repo (no env override),
# and spotisub/database.py opens/creates that file as a module-level side
# effect of the first `import spotisub.database` anywhere in the process.
# Repoint it at a throwaway directory *before* that first import happens, so
# the real test run never touches (or creates) this repo's cache/spotisub.db.
_TEST_DB_DIR = tempfile.mkdtemp(prefix="spotisub-test-db-")
import config as _config  # noqa: E402  (must follow sys.path setup above)
_config.Config.SQLALCHEMY_DATABASE_PATH = "sqlite:///" + _TEST_DB_DIR


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    """Give every test a fresh, empty SQLite database.

    spotisub.database.dbms.db_engine is looked up at call time by every
    database.py function, so swapping it here (rather than re-importing the
    module) is enough to fully isolate each test's data -- including from
    the one-time throwaway database created when spotisub.database is first
    imported (see _TEST_DB_DIR above).
    """
    from sqlalchemy import create_engine
    from spotisub import database

    engine = create_engine(
        f"sqlite:///{tmp_path / 'test_spotisub.db'}", isolation_level=None)
    database.dbms.metadata.create_all(engine)
    monkeypatch.setattr(database.dbms, "db_engine", engine)
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def isolated_cache_dir(tmp_path, monkeypatch):
    """Redirect the on-disk Subsonic/Spotify object cache (pickle files)
    written as a side effect of build_subsonic_cache() and friends to a
    throwaway directory instead of this repo's real cache/ folder.
    """
    from spotisub import constants

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(constants, "CACHE_DIR", str(cache_dir))
    yield
