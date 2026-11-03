import json
import urllib.request

from urllib.parse import quote


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
