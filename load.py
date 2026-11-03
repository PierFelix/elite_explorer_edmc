import logging
import os

import tkinter as tk
from myNotebook import Frame

from config import appname, appversion, config



# This could also be returned from plugin_start3()
PLUGIN_NAME = "EDMC-Elite-Explorer" # os.path.basename(os.path.dirname(__file__))

# A Logger is used per 'found' plugin to make it easy to include the plugin's
# folder name in the logging output format.
# NB: plugin_name here *must* be the plugin's folder name as per the preceding
#     code, else the logger won't be properly set up.
logger = logging.getLogger(f"{appname}.{PLUGIN_NAME}")

# If the Logger has handlers then it was already set up by the core code, else
# it needs setting up here.
if not logger.hasHandlers():
    level = logging.INFO  # So logger.info(...) is equivalent to print()

    logger.setLevel(level)
    logger_channel = logging.StreamHandler()
    logger_formatter = logging.Formatter(
        f"%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s"
    )
    logger_formatter.default_time_format = "%Y-%m-%d %H:%M:%S"
    logger_formatter.default_msec_format = "%s.%03d"
    logger_channel.setFormatter(logger_formatter)
    logger.addHandler(logger_channel)


def plugin_start3(plugin_dir: str) -> str:
    logger.info(f"Loaded {PLUGIN_NAME}, located at dir {plugin_dir}")
    return PLUGIN_NAME

def plugin_prefs(parent, cmdr, is_beta):
    frame = Frame(parent)
    return frame

def plugin_stop() -> None:
    """
    Plugin stop method.

    :return:
    """
    logger.info('Stopping')


def journal_entry(cmdrname: str, is_beta: bool, system: str, station: str, entry: dict, state: dict) -> None:
    """
    Handle the given journal entry.

    :param cmdrname:
    :param is_beta:
    :param system:
    :param station:
    :param entry:
    :param state:
    :return: None
    """
    # logger.debug(
    #         f'cmdr = "{cmdrname}", is_beta = "{is_beta}"'
    #         f', system = "{system}", station = "{station}"'
    #         f', event = "{entry["event"]}"'
    # )
    # this.plugin_test.store(entry['timestamp'], cmdrname, system, station, entry['event'])
    pass