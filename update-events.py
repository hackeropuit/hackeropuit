#!/usr/bin/python3

import os
import glob
import ruamel.yaml as ruamel_yaml
import simplejson as json
from datetime import datetime, date, timedelta, timezone
from icalendar import Calendar, Event
from pathlib import Path

### REMOVE AFTER RUAMEL.YAML UPGRADE
# temporary dirty patch until ruamel.yaml has been upgraded
def yaml_load(stream):
    loaded = []

    try:
        # new style
        yaml = ruamel_yaml.YAML(typ='safe', pure=True)
        loaded = yaml.load(stream)
    except:
        loaded = ruamel_yaml.safe_load(stream)

    return loaded

### UNCOMMENT AFTER RUAMEL.YAML UPGRADE
# Instantiate YAML
#yaml = ruamel_yaml.YAML(typ='safe', pure=True)

def eventdate(elem):
    return elem['StartDate']

today = date.today()
okevents = []

# Read all .yaml files from 'events' subdirectory
all_events = []
for filename in glob.glob("events/*.yaml"):
    try:
        with open(filename, "r", encoding="utf-8") as stream:
            events = []
            #loaded = yaml.load(stream)
            loaded = yaml_load(stream) #use temporary patch
            if isinstance(loaded, list):
                events.extend(loaded)
            elif isinstance(loaded, dict):
                events.append(loaded)

            for idx, event in enumerate(events):
                event['iCal'] = "ical/%s%s.ical" % (Path(filename).stem, idx)

            all_events.extend(events)
            
    except yaml.YAMLError as exc:
        print(f"Error parsing {filename}: {exc}")

# Filter and sort events
#for event in all_events:
#    if event['EndDate'] >= event['StartDate'] and today <= event['EndDate']:
#        okevents.append(event)

# Filter events
okevents = [event for event in all_events if event['EndDate'] >= event['StartDate'] and today <= event['EndDate']]

# Sort events
okevents.sort(key=eventdate)


# Export results to json
json_output = {}
try:
    # New method after upgrading datetime
    json_output = {
        "last_updated": datetime.now(timezone.utc).isoformat() + "Z",
        "events": okevents
    }
except:
    # Depricated method. Delete after updating datetime-library
    json_output = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "events": okevents
    }

with open("events.json", "w", encoding="utf-8") as output:
    json.dump(json_output, output, indent=4, default=str, ensure_ascii=False, encoding="utf-8")



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


# Cleanup ical folder
for filename in glob.glob("ical/*.ical"):
    try:
        os.remove(filename)
    except Exception as ex:
        print('Failed to delete %s. %s.' % (filename, ex))


# Create individual iCalendar files
for source_event in okevents:
    cal = Calendar()
    cal.add('prodid', '-//Hack er op uit//hackeropuit.nl//')
    cal.add('version', '2.0')

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

    with open(source_event['iCal'], 'wb') as f:
        f.write(cal.to_ical())
