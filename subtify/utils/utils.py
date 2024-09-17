import os
import sys
import logging
from dotenv import load_dotenv
from os.path import dirname
from os.path import join
from ..constants import constants

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=int(os.environ.get(constants.LOG_LEVEL, constants.LOG_LEVEL_DEFAULT_VALUE)),
        datefmt='%Y-%m-%d %H:%M:%S')
        
        
def print_logo(version):
        version_len = len(version)
        print(
            """
░██████╗██╗░░░██╗██████╗░████████╗██╗███████╗██╗░░░██╗
██╔════╝██║░░░██║██╔══██╗╚══██╔══╝██║██╔════╝╚██╗░██╔╝
╚█████╗░██║░░░██║██████╦╝░░░██║░░░██║█████╗░░░╚████╔╝░
░╚═══██╗██║░░░██║██╔══██╗░░░██║░░░██║██╔══╝░░░░╚██╔╝░░
██████╔╝╚██████╔╝██████╦╝░░░██║░░░██║██║░░░░░░░░██║░░░
╚═════╝░░╚═════╝░╚═════╝░░░░╚═╝░░░╚═╝╚═╝░░░░░░░░╚═╝░░░
"""
            + "                                     "[: -(version_len + 2)]
            + "v{} ".format(version
            + "\n")
        )

def write_exception():
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    logging.error("%s %s %s", exc_type, fname, exc_tb.tb_lineno, exc_info=1)
