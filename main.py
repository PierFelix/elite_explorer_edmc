import json
import urllib.request

from urllib.parse import quote


# Exploration status variables 
FULLYSCANNED = 4 # system is logged, amount of bodies is recorded and all bodies scanned
PARTIALSCAN = 3  # system is logged, amount of bodies is recorded and some bodies scanned/ not all scanned
UNKNOWNSCAN = 2  # system is logged, amount of bodies is NOT recorded but some bodies scanned scanned
LOGGED = 1       # system is logged, amount of bodies is NOT recorded, no bodies scnned (system is only known by name and possibly cords)
MISSING = 0      # system is NOT known to Spansh


def get_nearby_stars(system_name):
    html_safe_system_name = quote(system_name)
    my_url = f"https://www.edsm.net/api-v1/sphere-systems?radius=20&showId=1&systemName={html_safe_system_name}"
    my_headers = {"User-Agent": "Elite Explorer - Python"}
    my_request = urllib.request.Request(my_url, data=None, headers=my_headers)
    contents = urllib.request.urlopen(my_request, timeout=30).read()
    return json.loads(contents.strip())


def get_exploration_status(SystemAddress: int):
    """
    Requests a data dump of a system from Spansh

    :param int SystemAddress: id64 of the system (SystemAddress in journal)
    :return: json format of Spansh data dump
    """
    headers = {"User-Agent": "Elite Explorer - Python"}
    spansh_url = f"https://spansh.co.uk/api/dump/{SystemAddress}"
    spansh_request = urllib.request.Request(url=spansh_url, data=None, headers=headers)
    contents = urllib.request.urlopen(spansh_request, timeout=30).read()
    return json.loads(contents.strip())


def exploration_state_check(spansh_dump) -> list[int]:
    """
    Checks if the amount of fully scanned bodies matches the total bodyCount of the system. 

    :param spansh_dump: json of the Spansh system dump
    :return: [status, scanned bodies, bodyCount]
    :rtype: list[int]
    """
    scannedBodies: int = 0
    bodyCount: int = 0
    status: int

    if spansh_dump and spansh_dump.get("system"):
        bodyCount: int = spansh_dump.get("system").get("bodyCount")
        if spansh_dump.get("system").get("bodies"):
            for body in spansh_dump.get("system").get("bodies"):
                if body.get("type") in ("Planet", "Star"):
                    scannedBodies += 1

        if scannedBodies > 0:
            if bodyCount:
                if bodyCount == scannedBodies:
                    status = FULLYSCANNED
                else:
                    status = PARTIALSCAN
            else:
                status = UNKNOWNSCAN
        elif spansh_dump.get("system").get("name"):
            status = LOGGED
        else:
            # fallback option (should not be possible)
            status = MISSING
    else:
        status = MISSING

    return [status, scannedBodies, bodyCount]


if __name__ == "__main__":
    import glob
    import os
    import time

    def get_latest_journal(log_path):
        list_of_files = glob.glob(os.path.join(log_path, "Journal.*.log"))
        if not list_of_files:
            return None
        return max(list_of_files, key=os.path.getmtime)

    def better_print_nearby(nearby):
        sorted_nearby = sorted(nearby, key=lambda u: u["distance"])
        for system in sorted_nearby:
            # Example return entry
            # {'distance': 15.42, 'bodyCount': 1, 'name': 'Col 359 Sector GI-F c13-1'},
            print(
                f"LY: {system['distance']} Name: {system['name']} Bodies: {system['bodyCount']}"
            )

    journal_dir = os.path.expanduser(
        r"~\Saved Games\Frontier Developments\Elite Dangerous"
    )
    # This sometimes picks up the wrong journal if we start before the game does.
    # TODO FIXME
    latest_file = get_latest_journal(journal_dir)
    print(f"Reading latest journal: {latest_file}")

    if latest_file:
        with open(latest_file, "r", encoding="utf-8") as f:
            # Move to the end of the file to read only new events (tail)
            f.seek(0, os.SEEK_END)

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue

                try:
                    data = json.loads(line.strip())
                    event_type = data.get("event")
                    # ignore_list = [ 'Scan','FSSBodySignals', 'Music', 'FSDTarget' ]
                    if event_type == "Location":
                        print(
                            f"Event: {event_type} | Star System {data['StarSystem']} | StarPos {data['StarPos']}"
                        )
                        nearby = get_nearby_stars(data["StarSystem"])
                        better_print_nearby(nearby)
                    elif event_type == "FSDJump":
                        print(f"Event: {event_type} | Data: {data['StarSystem']}")
                        nearby = get_nearby_stars(data["StarSystem"])
                        better_print_nearby(nearby)
                    # elif event_type in ignore_list:
                    # continue
                    elif event_type == "Shutdown":
                        exit()
                    else:
                        # print(f"Event: {event_type} ")
                        continue
                except json.JSONDecodeError:
                    pass
