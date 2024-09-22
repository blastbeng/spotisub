import os
import random
import string

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """All application configurations"""

    # Secret key
    SECRET_KEY = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(128))

    # Database configurations
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'cache/spotisub.sqlite3')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
