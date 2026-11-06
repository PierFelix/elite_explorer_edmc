import json

import requests
from requests.compat import quote_plus

HTTP_HEADERS = {"User-Agent": "Elite Explorer - Python"}

# Exploration status variables 
FULLYSCANNED = 4 # system is logged, amount of bodies is recorded and all bodies scanned
PARTIALSCAN = 3  # system is logged, amount of bodies is recorded and some bodies scanned/ not all scanned
UNKNOWNSCAN = 2  # system is logged, amount of bodies is NOT recorded but some bodies scanned
LOGGED = 1       # system is logged, amount of bodies is NOT recorded, no bodies scnned (system is only known by name and possibly cords)
MISSING = 0      # system is NOT known to Spansh

def send_http_request(url, headers = HTTP_HEADERS, timeout: float = 30):
    return requests.get(url, headers=headers, timeout=timeout)

def get_nearby_systems(system_name) -> dict:
    url = f"https://www.edsm.net/api-v1/sphere-systems?radius=20&showId=1&systemName={quote_plus(system_name)}"
    res = send_http_request(url)
    if res.ok:
        return res.json()
    raise requests.exceptions.HTTPError(response=res)

def get_nearby_systems_cords(x: float, y: float, z: float) -> dict:
    url = f"https://www.edsm.net/api-v1/sphere-systems?radius=20&showId=1&x={quote_plus(str(x))}&y={quote_plus(str(y))}&z={quote_plus(str(z))}"
    res = send_http_request(url)
    if res.ok:
        return res.json()
    raise requests.exceptions.HTTPError(response=res)

def get_exploration_status(SystemAddress: int) -> dict:
    """
    Requests a data dump of a system from Spansh

    :param int SystemAddress: id64 of the system (SystemAddress in journal)
    :return: json format of Spansh data dump
    """
    url = f"https://spansh.co.uk/api/dump/{SystemAddress}"
    res = send_http_request(url)
    if res.ok:
        return res.json()
    raise requests.exceptions.HTTPError(response=res)


def exploration_state_check(spansh_dump) -> list[int]:
    """
    Checks if the amount of fully scanned bodies matches the total bodyCount of the system. 

    :param spansh_dump: json of the Spansh system dump
    :return: [status, scanned bodies, bodyCount]
    :rtype: list[int]
    """
    scannedBodies: int = 0
    bodyCount: int = 0
    status = MISSING

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

    return [status, scannedBodies, bodyCount]


if __name__ == "__main__":
    import glob
    import os
    import time

    CLEAR_UNKNOWNS = True
    SHOW_PARTIALLY_EXPLORED = True

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

    # journal_dir = os.path.expanduser(
    #     r"~\Saved Games\Frontier Developments\Elite Dangerous"
    # )
    journal_dir = os.path.expanduser(
        r"~/.local/share/Steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous/"
    )

    latest_file = get_latest_journal(journal_dir)

    if latest_file:
        with open(latest_file, "rb") as f:
            try:
                _ = f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    _ = f.seek(-2, os.SEEK_CUR)
            except OSError:
                _ = f.seek(0)
            
            try:
                line = f.readline()
                data = json.loads(line.strip())
                event_type = data.get("event")
                if event_type == "Shutdown":
                    ed_running = False
                    print("Waiting for Elite:Dangerous to start.")
                else:
                    ed_running = True

            except json.JSONDecodeError:
                    ed_running = True
        
        while not ed_running:
            time.sleep(5)
            new_latest_file = get_latest_journal(journal_dir)
            if new_latest_file != latest_file:
                latest_file = new_latest_file
                ed_running = True
                print("Detected new journal file!")

    else:
        print(f"Found no journals inside directory {journal_dir}")
        ed_running = False
        while not ed_running:
            time.sleep(5)
            latest_file = get_latest_journal(journal_dir)
            if latest_file:
                ed_running = True
                print("Detected new journal file!")

    if latest_file:
        print(f"Reading latest journal: {latest_file.split("\\")[-1]}")
        with open(latest_file, "r", encoding="utf-8") as f:
            # Move to the end of the file to read only new events (tail)
            _ = f.seek(0, os.SEEK_END)
            
            nearby = {}
            unexplored = {}
            partially_explored = {}
            jump_system = ""

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue

                try:
                    data = json.loads(line.strip())
                    match data.get("event"):
                        case "Location" | "FSDJump":
                            
                            # TODO Needs a better system that checks if it is more than 20 LYs away
                            # would require calculating distance with cords...
                            StarSystem: str = data["StarSystem"]
                            if CLEAR_UNKNOWNS:
                                unexplored.clear()
                                partially_explored.clear()
                            else:
                                _ = unexplored.pop(StarSystem, None)
                                _ = partially_explored.pop(StarSystem, None)
                            
                            x, y, z = data["StarPos"]

                            edsm_nearby = {}
                            tries = 0
                            while not edsm_nearby:
                                try:
                                    edsm_nearby = get_nearby_systems_cords(x, y, z)
                                except requests.exceptions.HTTPError as e:
                                    print(f"Got an {e.response.status_code}!\nReason: {e.response.reason}")
                                    if e.response.status_code != 503:
                                        print("Skipping this instance")
                                        nearby.clear()
                                        break
                                    elif tries < 5:
                                        tries += 1
                                        print(f"Will retry in 3 seconds... [{tries}/5]")
                                        time.sleep(3)
                                    else:
                                        print("Max retries exceeded, skipping this system...")
                                        nearby.clear()
                                        break
                            
                            _ = edsm_nearby.pop(StarSystem, None)
                            for system_info in edsm_nearby:
                                system_name = system_info["name"]
                                nearby[system_name] = {}

                                if SHOW_PARTIALLY_EXPLORED:
                                    id64 = system_info["id64"]
                                    if id64 and id64 >= 0:
                                        nearby[system_name]["id64"] = id64
                                        try:
                                            explo_status = get_exploration_status(id64)

                                            explored, scannedBodies, bodyCount = exploration_state_check(explo_status)
                                            nearby[system_name]["explored"] = explored
                                            nearby[system_name]["scannedBodies"] = scannedBodies
                                            nearby[system_name]["bodyCount"] = bodyCount

                                            match explored:
                                                case 0:
                                                    print(f"New unexplored (Spansh): {system_name}")
                                                    unexplored[system_name] = {}
                                                case 1 | 2 | 3:
                                                    scanned = str(scannedBodies).rjust(3, "0") if scannedBodies else "???"
                                                    total = str(bodyCount).rjust(3, "0") if bodyCount else "???"
                                                    print(f"New partially explored: {system_name}")
                                                    partially_explored[system_name]  = {}
                                        
                                        except requests.exceptions.HTTPError as e:
                                            if e.response.status_code != 404:
                                                print(f"Got an {e.response.status_code}!\nReason: {e.response.reason}")
                                            else:
                                                print(f"{system_name} is not known by Spansh!")
                                                unexplored[system_name] = {}


                            print("Finished checking nearby systems with Spansh")        
                                
                        case "FSDTarget":
                            if nearby:
                                system_name = data["Name"]
                                if not system_name in nearby and not jump_system == system_name:
                                    unexplored[system_name] = {}
                                    print(f"{system_name} is not known by EDSM!")

                        case "StartJump":
                            # Jump can be more than 20 LY, meaning the system will never be
                            # in the nearby list
                            if data["JumpType"] == "Hyperspace":
                                jump_system = data["StarSystem"]

                        case "Music":
                            match data["MusicTrack"]:
                                # Opening Powerplay or Galnet News
                                case "GalacticPowers":
                                    print("\nFully Unexplored Systems:")
                                    print("\n".join(unexplored.keys()))

                                # Opening Codex
                                case "Codex":
                                    print("\nFully Unexplored Systems:")
                                    print("\n".join(unexplored.keys()))
                                    print("\nPartially Explored Systems:")
                                    if SHOW_PARTIALLY_EXPLORED:
                                        for k in partially_explored.keys():
                                            scanned = str(nearby[k]["scannedBodies"]).rjust(3, "0") if nearby[k]["scannedBodies"] else "???"
                                            total = str(nearby[k]["bodyCount"]).rjust(3, "0") if nearby[k]["bodyCount"] else "???"
                                            print(f"[{scanned}/{total}] {k}")
                                    else:
                                        print("Checking partially explored is disabled!")
                                    
                                case _:
                                    continue

                        case "Shutdown":
                            exit()
                        
                        case _:
                            continue
  
                except json.JSONDecodeError:
                    pass
