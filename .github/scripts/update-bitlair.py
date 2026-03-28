#!/usr/bin/env python3

from datetime import datetime, timedelta
import pytz
import re
import sys

import requests
from ruamel.yaml import YAML


# Asks for all events and returns their name, start, end and location.
start = datetime.now() - timedelta(days=365)
events_url = f"https://bitlair.nl/Special:Ask/-5B-5BCategory:Event-5D-5D-20-5B-5BStart::%E2%89%A5{start.day}-20{start.month}-20{start.year}-5D-5D/-3FStart/-3FEnd/-3FEventStatus/-3FEventLocation/-3FEventPromote/mainlabel%3D/limit%3D500/order%3DASC/sort%3DStart/prettyprint%3Dtrue/format%3Djson"

response_body = requests.get(events_url).json()
smw_events = response_body["results"]

# Unix timestamps from semwiki are not in UTC but in $localtime
time_offset = pytz.timezone("Europe/Amsterdam").utcoffset(datetime.now())

events = []

for page_path, value in smw_events.items():
    start_time = None
    end_time = None
    if (tt := value["printouts"]["Start"]) and tt:
        start_time = datetime.fromtimestamp(int(tt[0]["timestamp"])) - time_offset
    if (tt := value["printouts"]["End"]) and tt:
        end_time = datetime.fromtimestamp(int(tt[0]["timestamp"])) - time_offset

    # Only include events that explicitly request to be actively promoted via 3rd party channels.
    if value["printouts"]["EventPromote"] != ["t"]:
        continue

    # Only include events that are confirmed.
    if len(value["printouts"]["EventStatus"]) == 0:
        continue
    # A status as per RFC5545 3.8.1.11
    status_value = value["printouts"]["EventStatus"][0].upper()
    if status_value not in ("CONFIRMED", "DEFINITIVE", "DEFINITIEF", "BEVESTIGD"):
        continue

    if not start_time:
        continue
    if not end_time:
        end_time = start_time + timedelta(hours=4)

    # Remove preceding 'Events/YYYY-MM-DD ' if existant from pagename to result in the actual event name
    eventname = page_path
    if (m := re.search(r"Events\/....-..-.. (.*)", page_path)) and m:
        eventname = m[1]

    # If an event ends when humans are usually asleep, truncate the time range to midnight.
    # This prevents calendar items from cluttering the next day when viewed.
    if end_time.hour < 6:
        end_time = datetime(
            end_time.year, end_time.month, end_time.day, 23, 59
        ) - timedelta(days=1)

    events.append(
        {
            "Name": eventname,
            "Location": "Bitlair, Amersfoort, NL",
            "StartDate": start_time.date(),
            "EndDate": end_time.date(),
            "URL": value["fullurl"],
            "Comment": "",
        }
    )


print("---")
print("")
yaml = YAML()
yaml.dump(events, sys.stdout)
