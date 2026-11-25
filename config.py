import os
import random
import string
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

basedir = os.path.abspath(os.path.dirname(__file__))


def _load_secret_key():
    """Return SECRET_KEY from env, or persist a generated one in cache/secret_key."""
    env_key = os.environ.get("SECRET_KEY", "")
    if env_key:
        return env_key
    key_file = os.path.join(basedir, "cache", "secret_key")
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            return f.read().strip()
    key = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(128))
    os.makedirs(os.path.dirname(key_file), exist_ok=True)
    with open(key_file, "w") as f:
        f.write(key)
    return key


class Config(object):
    """All application configurations"""

    # Secret key — set SECRET_KEY in .env, or a stable key is auto-generated in cache/secret_key
    SECRET_KEY = _load_secret_key()

    # Database configurations
    SQLALCHEMY_DATABASE_NAME = 'spotisub.db'
    SQLALCHEMY_DATABASE_PATH = 'sqlite:///' + os.path.join(basedir, 'cache')
    SQLALCHEMY_DATABASE_URI = os.path.join(
        SQLALCHEMY_DATABASE_PATH, SQLALCHEMY_DATABASE_NAME)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SCHEDULER_API_ENABLED = True
    SCHEDULER_API_PREFIX = "/api/v1/scheduler"
    SCHEDULER_EXECUTORS = {
        "default": {
            "type": "threadpool",
            "max_workers": 10}}

    APPLICATION_ROOT = os.environ.get("APPLICATION_ROOT", "")
    LOGIN_DISABLED = os.environ.get("LOGIN_DISABLED", "0") == "1"
