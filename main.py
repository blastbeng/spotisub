import os
from os.path import dirname
from os.path import join
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

from spotisub import spotisub
from spotisub.models import User
from spotisub import configuration_db


@spotisub.shell_context_processor
def make_shell_context():
    return dict(db=configuration_db, User=User)
