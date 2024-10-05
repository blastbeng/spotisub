import os
import random
import string
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """All application configurations"""

    # Secret key
    SECRET_KEY = ''.join(
        random.choice(
            string.ascii_lowercase +
            string.digits) for _ in range(128))

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
