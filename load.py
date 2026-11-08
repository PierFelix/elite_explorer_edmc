import logging
import os
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


class EEMainUI(tk.Frame):
    def __init__(
        self, parent: tk.Frame, systems_dict: dict
    ) -> None:  # , container, gridrow
        tk.Frame.__init__(self, parent)
        self.parent = parent

        self.systems_dict = systems_dict

        self.visible = 1
        self.systems_list_idx = 0
        self.systems_list_txt = ["Unknown Systems", "Partially Known Systems"]

        self.explored_colors = ["#FFA500", "#FFFF00", "#A5FF00"]

        self.IMG_SWAP = tk.PhotoImage(
            file=os.path.join(os.path.dirname(__file__), "assets", "swap.png")
        )

        current_row = 0
        # frame = tk.Frame(self.parent)

        self.sys_lis_frame = tk.Frame(self)
        self.sys_lis_frame.grid(row=current_row, sticky="ew")

        self.sys_lis_frame.columnconfigure(0, weight=0)
        self.sys_lis_frame.columnconfigure(1, weight=1)

        self.systems_list = tk.Label(self.sys_lis_frame, text="Waiting...")
        self.systems_list.grid(row=0, column=1, sticky="W")

        self.swap_but = tk.Button(
            self.sys_lis_frame,
            image=self.IMG_SWAP,
            width=14,
            height=14,
            borderwidth=0,
            command=self.systems_list_swap,
        )
        self.swap_but.grid(row=0, column=0, sticky=tk.NW, padx=10)
        current_row += 1

        self.list_container = tk.Frame(self)
        self.list_container.grid(row=current_row, sticky="ew")
        current_row += 1

        logger.info("Main UI initialized")

    def set_visible(self, visible: int) -> None:
        self.visible = visible
        if self.visible:
            self.grid()
            self.update()
        else:
            self.grid_remove()

    def systems_list_swap(self) -> None:
        self.systems_list_idx = 0 if self.systems_list_idx else 1
        self.update()

    def update(self) -> None:
        if self.visible:
            self.systems_list.config(text=self.systems_list_txt[self.systems_list_idx])

            for child in self.list_container.winfo_children():
                child.destroy()

            match self.systems_list_idx:
                case 0:
                    names = [
                        n for n, d in self.systems_dict.items() if not d["explored"]
                    ]
                    if len(names) > 0:
                        for i, name in enumerate(names):
                            tk.Label(self.list_container, text=name).grid(
                                row=i, column=0, sticky="w"
                            )
                    else:
                        tk.Label(
                            self.list_container,
                            text="No Unknown Systems Found",
                            fg=self.systems_list.cget("fg"),
                            bg=self.systems_list.cget("bg"),
                        ).grid(row=0, column=0, sticky="w")

                case 1:
                    names = [
                        (n, d)
                        for n, d in self.systems_dict.items()
                        if d["explored"] in [1, 2, 3]
                    ]

                    if len(names) > 0:
                        for i, (name, data) in enumerate(names):
                            scanned = (
                                str(data["scannedBodies"]).rjust(3, "0")
                                if data["scannedBodies"]
                                else "???"
                            )
                            total = (
                                str(data["bodyCount"]).rjust(3, "0")
                                if data["bodyCount"]
                                else "???"
                            )
                            tk.Label(
                                self.list_container,
                                text=f"[{scanned}/{total}]",
                                bg=self.explored_colors[data["explored"] - 1],
                                fg="black",
                            ).grid(row=i, column=0, sticky="w", padx=(0, 10))

                            tk.Label(
                                self.list_container,
                                text=name,
                                bg=self.explored_colors[data["explored"] - 1],
                                fg="black",
                            ).grid(row=i, column=1, sticky="w")
                    else:
                        tk.Label(
                            self.list_container,
                            text="No Partially Known Systems Found",
                            fg=self.systems_list.cget("fg"),
                            bg=self.systems_list.cget("bg"),
                        ).grid(row=0, column=0, sticky="w")


class EliteExplorer:
    def __init__(self) -> None:
        self.clear_nearby: tk.IntVar
        self.show_partially_explored: tk.IntVar
        self.main_ui_visible: tk.IntVar
        self.enable_overlay: tk.IntVar
        self.debug_logging: tk.IntVar

        self.nearby_systems = {}
        self.jump_system = ""

        self.plugin_dir: str
        self.main_ui: EEMainUI

    def reload_config(self) -> None:
        self.clear_nearby = tk.IntVar(value=int(config.get_int("ee_clear_nearby")))
        self.show_partially_explored = tk.IntVar(
            value=int(config.get_int("ee_partially_explored"))
        )
        self.main_ui_visible = tk.IntVar(
            value=int(config.get_int("ee_main_ui_visible"))
        )
        self.enable_overlay = tk.IntVar(value=int(config.get_int("ee_enable_overlay")))
        self.debug_logging = tk.IntVar(value=int(config.get_int("ee_debug_logging")))

    def on_load(self, plugin_dir: str) -> str:
        self.plugin_dir = plugin_dir
        logger.info(f'Loaded "{PLUGIN_NAME}", located at dir "{plugin_dir}"')

        # I don't know if there is an intended way for default config options...
        if config.get("ee_clear_nearby") is None:
            config.set("ee_clear_nearby", 1)
        if config.get("ee_partially_explored") is None:
            config.set("ee_partially_explored", 1)
        if config.get("ee_main_ui_visible") is None:
            config.set("ee_main_ui_visible", 1)
        if config.get("ee_enable_overlay") is None:
            config.set("ee_enable_overlay", 0)
        if config.get("ee_debug_logging") is None:
            config.set("ee_debug_logging", 30)
        self.reload_config()

        return PLUGIN_NAME

    def on_unload(self) -> None:
        """
        on_unload is called by plugin_stop below.

        It is the last thing called before EDMC shuts down. Note that blocking code here will hold the shutdown process.
        """
        self.on_preferences_closed("", False)  # Save our prefs
        logger.info("Stopping")

    def setup_preferences(
        self, parent: nb.Notebook | tk.Frame, cmdr: str, is_beta: bool
    ) -> tk.Frame | None:
        """
        setup_preferences is called by plugin_prefs below.

        It is where we can setup our own settings page in EDMC's settings window. Our tab is defined for us.

        :param parent: the tkinter parent that our returned Frame will want to inherit from
        :param cmdr: The current ED Commander
        :param is_beta: Whether or not EDMC is currently marked as in beta mode
        :return: The frame to add to the settings window
        """
        current_row = 0
        frame: tk.Frame = nb.Frame(parent)

        self.clear_nearby = tk.IntVar(value=int(config.get_int("ee_clear_nearby")))
        self.show_partially_explored = tk.IntVar(
            value=int(config.get_int("ee_partially_explored"))
        )
        self.main_ui_visible = tk.IntVar(
            value=int(config.get_int("ee_main_ui_visible"))
        )
        self.enable_overlay = tk.IntVar(value=int(config.get_int("ee_enable_overlay")))
        self.debug_logging = tk.IntVar(value=int(config.get_int("ee_debug_logging")))

        # Title
        title_label = tk.Label(
            frame, text="Elite Explorer Settings", font=("TkDefaultFont", 12, "bold")
        )
        title_label.grid(
            row=current_row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(10, 20)
        )
        current_row += 1

        # Global Settings
        general_label = tk.Label(
            frame, text="Global Settings", font=("TkDefaultFont", 10, "bold")
        )
        general_label.grid(
            row=current_row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(10, 20)
        )
        current_row += 1

        nb.Checkbutton(
            frame, text="Clear Nearby List", variable=self.clear_nearby
        ).grid(row=current_row, column=0, sticky="NSEW")
        current_row += 1

        nb.Checkbutton(
            frame, text="Show Partially Explored", variable=self.show_partially_explored
        ).grid(row=current_row, column=0, sticky="NSEW")
        current_row += 1

        # TODO needs to be an option to select [NOTSET (optional), DEBUG, INFO, WARNING, ERROR, CRITICAL, NONE]
        # with values [0, 10, 20, 30, 40, 50, 51] (see Logging Levels)
        nb.Checkbutton(
            frame, text="Enable Debug Logging", variable=self.debug_logging
        ).grid(row=current_row, column=0, sticky="NSEW")
        current_row += 1

        # Main UI Settings
        general_label = tk.Label(
            frame, text="Main UI Settings", font=("TkDefaultFont", 10, "bold")
        )
        general_label.grid(
            row=current_row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(10, 20)
        )
        current_row += 1

        nb.Checkbutton(frame, text="Show Main UI", variable=self.main_ui_visible).grid(
            row=current_row, column=0, sticky="NSEW"
        )
        current_row += 1

        # Overlay Settings
        general_label = tk.Label(
            frame, text="Overlay Settings", font=("TkDefaultFont", 10, "bold")
        )
        general_label.grid(
            row=current_row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(10, 20)
        )
        current_row += 1

        nb.Checkbutton(frame, text="Enable Overlay", variable=self.enable_overlay).grid(
            row=current_row, column=0, sticky="NSEW"
        )
        current_row += 1

        return frame

    def on_preferences_closed(self, cmdr: str, is_beta: bool) -> None:
        """
        on_preferences_closed is called by prefs_changed below.

        It is called when the preferences dialog is dismissed by the user.

        :param cmdr: The current ED Commander
        :param is_beta: Whether or not EDMC is currently marked as in beta mode
        """
        config.set("ee_clear_nearby", int(self.clear_nearby.get()))
        config.set("ee_partially_explored", int(self.show_partially_explored.get()))
        config.set("ee_main_ui_visible", int(self.main_ui_visible.get()))
        self.main_ui.set_visible(int(self.main_ui_visible.get()))
        config.set("ee_enable_overlay", int(self.enable_overlay.get()))
        config.set("ee_debug_logging", int(self.debug_logging.get()))

    def setup_main_ui(self, parent: tk.Frame) -> tk.Frame:
        """
        Create our entry on the main EDMC UI.

        This is called by plugin_app below.

        :param parent: EDMC main window Tk
        :return: Our frame
        """
        self.main_ui = EEMainUI(parent, self.nearby_systems)
        self.main_ui.set_visible(self.main_ui_visible.get())
        return self.main_ui

    def journal_event(
        self,
        cmdrname: str,
        is_beta: bool,
        system: str,
        station: str,
        entry: dict,
        state: dict,
    ):
        # TODO: Add a way to trigger the first Location/ FDSDJump if
        # EDMC was started late (Now waits on next jump)
        match entry.get("event"):
            case "Location" | "FSDJump":
                # TODO Needs a better system that checks if it is more than 20 LYs away
                # would require calculating distance with cords...
                if self.clear_nearby.get():
                    self.nearby_systems.clear()
                else:
                    # Needs a better system, probably check for all
                    # bodies scanned journal event to update list
                    if not entry["StarSystem"] in self.nearby_systems:
                        self.nearby_systems[entry["StarSystem"]] = {}
                    add_explored_info(
                        self.nearby_systems[entry["StarSystem"]],
                        UNKNOWNSCAN,
                        scannedBodies=1,
                    )

                gather_nearby_edsm(
                    self.nearby_systems,
                    entry,
                    logger=logger,
                    debug_log=self.debug_logging.get(),
                )

                if self.show_partially_explored:
                    crosscheck_spansh(
                        self.nearby_systems,
                        logger=logger,
                        debug_log=self.debug_logging.get(),
                    )
                self.main_ui.update()

            case "FSDTarget":
                if self.nearby_systems:
                    system_name = entry["Name"]
                    if (
                        not system_name in self.nearby_systems
                        and self.jump_system != system_name
                    ):
                        self.nearby_systems[system_name] = {}
                        add_explored_info(self.nearby_systems[system_name])
                        self.main_ui.update()
                        if self.debug_logging.get() <= 20:
                            logger.info(f"{system_name} is not known by EDSM!")

            case "StartJump":
                # Jump can be more than 20 LY, meaning the system
                # is most times not in the nearby list
                if entry["JumpType"] == "Hyperspace":
                    self.jump_system = entry["StarSystem"]

            case "Music":
                if self.debug_logging.get() <= 20:
                    match entry["MusicTrack"]:
                        # Opening Powerplay or Galnet News
                        case "GalacticPowers":
                            logger.info("Fully Unexplored Systems:")
                            for k in [
                                sys
                                for sys, v in self.nearby_systems.items()
                                if v.get("explored") in [MISSING]
                            ]:
                                logger.info(f"{k}")

                        # Opening Codex
                        case "Codex":
                            logger.info("Partially Explored Systems:")
                            if self.show_partially_explored:
                                for k in [
                                    sys
                                    for sys, v in self.nearby_systems.items()
                                    if v.get("explored")
                                    in [LOGGED, UNKNOWNSCAN, PARTIALSCAN]
                                ]:
                                    scanned = (
                                        str(
                                            self.nearby_systems[k]["scannedBodies"]
                                        ).rjust(3, "0")
                                        if self.nearby_systems[k]["scannedBodies"]
                                        else "???"
                                    )
                                    total = (
                                        str(self.nearby_systems[k]["bodyCount"]).rjust(
                                            3, "0"
                                        )
                                        if self.nearby_systems[k]["bodyCount"]
                                        else "???"
                                    )
                                    logger.info(f"[{scanned}/{total}] {k}")
                            else:
                                logger.info("Checking partially explored is disabled!")

                        case _:
                            pass
            case _:
                pass


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


def journal_entry(
    cmdrname: str, is_beta: bool, system: str, station: str, entry: dict, state: dict
) -> None:
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
    ee.journal_event(cmdrname, is_beta, system, station, entry, state)
