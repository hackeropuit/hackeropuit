#!/usr/bin/env python3

# This is run from a daily cronjob on the hackeropuit host

import sys
import icalendar

import requests
from ruamel.yaml import YAML


resp = requests.get("https://bitlair.nl/events.ics?subset=promote")
resp.raise_for_status()
cal = icalendar.Calendar.from_ical(resp.text)

events = []
for cal_event in cal.events:
    events.append(
        {
            "Name": str(cal_event["summary"]),
            "Location": str(cal_event["location"]),
            "StartDate": cal_event["dtstart"].dt.date(),
            "EndDate": cal_event["dtend"].dt.date(),
            "URL": str(cal_event["url"]),
            "Comment": "",
        }
    )


print("---")
print("")
yaml = YAML()
yaml.dump(events, sys.stdout)
