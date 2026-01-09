#!/usr/bin/python3

import glob
from ruamel.yaml import YAML
import simplejson as json
from datetime import datetime, date, timedelta, timezone
from icalendar import Calendar, Event

def eventdate(elem):
    return elem['StartDate']

today = date.today()
okevents = []
yaml = YAML(typ="safe", pure=True)

# Read all .yaml files from 'events' subdirectory
all_events = []
for filename in glob.glob("events/*.yaml"):
    try:
        with open(filename, "r", encoding="utf-8") as stream:
            loaded = yaml.load(stream)
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

json_output = {
    "last_updated": datetime.utcnow().isoformat() + "Z",
    "events": okevents
}
with open("events.json", "w", encoding="utf-8") as output:
    json.dump(json_output, output, indent=4, default=str, ensure_ascii=False)

# Generate iCalendar
cal = Calendar()
cal.add('prodid', '-//Hack er op uit//hackeropuit.nl//')
cal.add('version', '2.0')

for source_event in all_events:
    event = Event()
    event.add('transp', 'TRANSPARENT')
    event.add('dtstamp', datetime.now(timezone.utc))
    event.add('uid', f"/{source_event['Name']}/{source_event['StartDate']}")
    event.add('summary', source_event['Name'])
    event.add('dtstart', source_event['StartDate'])
    event.add('dtend', source_event['EndDate'] + timedelta(days=1))
    event.add('location', source_event.get('Location'))
    event.add('description', source_event.get('Comment'))
    event.add('url', source_event.get('URL'))
    cal.add_component(event)

with open('events.ics', 'wb') as f:
    f.write(cal.to_ical())
