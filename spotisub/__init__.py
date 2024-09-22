"""Spotisub init module"""
import logging
import os

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from spotisub import database
from spotisub import constants
from spotisub import utils

utils.print_logo(constants.VERSION)

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=int(
        os.environ.get(
            constants.LOG_LEVEL,
            constants.LOG_LEVEL_DEFAULT_VALUE)),
    datefmt='%Y-%m-%d %H:%M:%S')

log = logging.getLogger('werkzeug')
log.setLevel(int(os.environ.get(constants.LOG_LEVEL,
             constants.LOG_LEVEL_DEFAULT_VALUE)))

spotisub = Flask(__name__)
spotisub.config.from_object(Config)

bootstrap = Bootstrap(spotisub)
configuration_db = SQLAlchemy(spotisub)
login = LoginManager(spotisub)
login.login_view = 'login'

from spotisub import routes, classes, errors