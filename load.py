import logging
import os

import time

import tkinter as tk
import myNotebook as nb

from config import appname, appversion, config

from main import *


# This could also be returned from plugin_start3()
PLUGIN_NAME = os.path.basename(os.path.dirname(__file__))

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

class EliteExplorer():
    def __init__(self) -> None:
        self.clear_unknows = tk.IntVar(value=int(config.get_int('ee_clear_unknows')))
        self.show_partially_explored = tk.IntVar(value=int(config.get_int('ee_partially_explored')))
        self.main_ui_visible = tk.IntVar(value=int(config.get_int('ee_main_ui_visible')))
        self.enable_overlay = tk.IntVar(value=int(config.get_int('ee_enable_overlay')))

        self.unexplored = {}
        self.nearby_systems = {}
        self.partially_explored = {}
        self.jump_system = ""

        self.plugin_dir: str
        self.main_ui: tk.Frame


    def on_load(self, plugin_dir: str) -> str:
        self.plugin_dir = plugin_dir
        logger.info(f'Loaded "{PLUGIN_NAME}", located at dir "{plugin_dir}"')
        
        # I don't know if there is an intended way for default config options...
        if config.set('ee_clear_unknows', int(self.clear_unknows.get())) is None:
            config.set('ee_clear_unknows', 1) 
        if config.set('ee_partially_explored', int(self.show_partially_explored.get())) is None:
            config.set('ee_partially_explored', 1) 
        if config.set('ee_main_ui_visible', int(self.main_ui_visible.get())) is None:
            config.set('ee_main_ui_visible', 1) 
        if config.set('ee_enable_overlay', int(self.enable_overlay.get())) is None:
            config.set('ee_enable_overlay', 0)        
        
        return PLUGIN_NAME
    
    def on_unload(self) -> None:
        """
        on_unload is called by plugin_stop below.

        It is the last thing called before EDMC shuts down. Note that blocking code here will hold the shutdown process.
        """
        self.on_preferences_closed("", False)  # Save our prefs
        logger.info("Stopping")

    def setup_preferences(self, parent: nb.Notebook, cmdr: str, is_beta: bool) -> nb.Frame | None:
        """
        setup_preferences is called by plugin_prefs below.

        It is where we can setup our own settings page in EDMC's settings window. Our tab is defined for us.

        :param parent: the tkinter parent that our returned Frame will want to inherit from
        :param cmdr: The current ED Commander
        :param is_beta: Whether or not EDMC is currently marked as in beta mode
        :return: The frame to add to the settings window
        """
        current_row = 0
        frame: nb.Frame = nb.Frame(parent)
        
        self.clear_unknows = tk.IntVar(value=int(config.get_int('ee_clear_unknows')))
        self.show_partially_explored = tk.IntVar(value=int(config.get_int('ee_partially_explored')))
        self.main_ui_visible = tk.IntVar(value=int(config.get_int('ee_main_ui_visible')))
        self.enable_overlay = tk.IntVar(value=int(config.get_int('ee_enable_overlay')))

        # Title
        title_label = tk.Label(frame, text="Elite Explorer Settings", font=('TkDefaultFont', 12, 'bold'))
        title_label.grid(row=current_row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(10, 20))
        current_row += 1
        

        # Global Settings
        general_label = tk.Label(frame, text="Global Settings", font=('TkDefaultFont', 10, 'bold'))
        general_label.grid(row=current_row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(10, 20))
        current_row += 1

        nb.Checkbutton(frame, text='Clear Unknowns List', variable=self.clear_unknows).grid(row=current_row, column=0, sticky="NSEW")
        current_row += 1

        nb.Checkbutton(frame, text='Show Partially Explored', variable=self.show_partially_explored).grid(row=current_row, column=0, sticky="NSEW")
        current_row += 1
        

        # Main UI Settings
        general_label = tk.Label(frame, text="Main UI Settings", font=('TkDefaultFont', 10, 'bold'))
        general_label.grid(row=current_row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(10, 20))
        current_row += 1

        nb.Checkbutton(frame, text='Show Main UI', variable=self.main_ui_visible).grid(row=current_row, column=0, sticky="NSEW")
        current_row += 1
        
        
        # Overlay Settings
        general_label = tk.Label(frame, text="Overlay Settings", font=('TkDefaultFont', 10, 'bold'))
        general_label.grid(row=current_row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(10, 20))
        current_row += 1

        nb.Checkbutton(frame, text='Enable Overlay', variable=self.enable_overlay).grid(row=current_row, column=0, sticky="NSEW")
        current_row += 1

        return frame

    def on_preferences_closed(self, cmdr: str, is_beta: bool) -> None:
        """
        on_preferences_closed is called by prefs_changed below.

        It is called when the preferences dialog is dismissed by the user.

        :param cmdr: The current ED Commander
        :param is_beta: Whether or not EDMC is currently marked as in beta mode
        """
        config.set('ee_clear_unknows', int(self.clear_unknows.get()))
        config.set('ee_partially_explored', int(self.show_partially_explored.get()))
        config.set('ee_main_ui_visible', int(self.main_ui_visible.get()))
        config.set('ee_enable_overlay', int(self.enable_overlay.get()))

    def setup_main_ui(self, parent: tk.Frame) -> tk.Frame:
        """
        Create our entry on the main EDMC UI.

        This is called by plugin_app below.

        :param parent: EDMC main window Tk
        :return: Our frame
        """
        current_row = 0
        frame = tk.Frame(parent)
        button = tk.Button(
            frame,
            text="Count me",
            # command=lambda: self.click_count.set(str(int(self.click_count.get()) + 1))
        )
        button.grid(row=current_row)
        current_row += 1
        tk.Label(frame, text="Count:").grid(row=current_row, sticky=tk.W)
        # tk.Label(frame, textvariable=self.click_count).grid(row=current_row, column=1)
        return frame


ee = EliteExplorer()

def plugin_start3(plugin_dir: str) -> str:
    """
    Handle start up of the plugin.

    See PLUGINS.md#startup
    """
    return ee.on_load(plugin_dir)

def plugin_stop() -> None:
    """
    Handle shutdown of the plugin.

    See PLUGINS.md#shutdown
    """
    return ee.on_unload()

def plugin_prefs(parent: nb.Notebook, cmdr: str, is_beta: bool) -> nb.Frame | None:
    """
    Handle preferences tab for the plugin.

    See PLUGINS.md#configuration
    """
    return ee.setup_preferences(parent, cmdr, is_beta)


def prefs_changed(cmdr: str, is_beta: bool) -> None:
    """
    Handle any changed preferences for the plugin.

    See PLUGINS.md#configuration
    """
    return ee.on_preferences_closed(cmdr, is_beta)


def plugin_app(parent: tk.Frame) -> tk.Frame | None:
    """
    Set up the UI of the plugin.

    See PLUGINS.md#display
    """
    return ee.setup_main_ui(parent)

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