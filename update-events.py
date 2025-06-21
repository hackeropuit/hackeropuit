#!/usr/bin/python3

import glob
import ruamel.yaml as yaml
import simplejson as json
from datetime import datetime, date, timedelta
from icalendar import Calendar, Event

def eventdate(elem):
    return elem['StartDate']

today = date.today()
okevents = []

# Read all .yaml files from 'events' subdirectory
all_events = []
for filename in glob.glob("events/*.yaml"):
    try:
        with open(filename, "r", encoding="utf-8") as stream:
            loaded = yaml.safe_load(stream)
            if isinstance(loaded, list):
                all_events.extend(loaded)
            elif isinstance(loaded, dict):
                all_events.append(loaded)
    except yaml.YAMLError as exc:
        print(f"Error parsing {filename}: {exc}")

# Filter and sort events
for event in all_events:
    if event['EndDate'] >= event['StartDate'] and today <= event['EndDate']:
        okevents.append(event)

okevents.sort(key=eventdate)

# Write JSON output
with open("events.json", "w", encoding="utf-8") as output:
    json.dump(okevents, output, indent=4, default=str, ensure_ascii=False, encoding="utf-8")

# Generate iCalendar
cal = Calendar()
cal.add('prodid', '-//Hack er op uit//hackeropuit.nl//')
cal.add('version', '2.0')

for source_event in all_events:
    event = Event()
    event.add('transp', 'TRANSPARENT')
    event.add('dtstamp', datetime.now())
    event.add('uid', f"/{source_event['Name']}/{source_event['StartDate']}")
    event.add('summary', source_event['Name'])
    event.add('dtstart', source_event['StartDate'])
    event.add('dtend', source_event['EndDate'] + timedelta(days=1))
    event.add('location', source_event['Location'])
    event.add('description', source_event['Comment'])
    event.add('url', source_event['URL'])
    cal.add_component(event)

with open('events.ics', 'wb') as f:
    f.write(cal.to_ical())
