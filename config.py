import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """All application configurations"""

    # Secret key
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Database configurations
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'cache/spotisub.sqlite3')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
