#!/usr/bin/env python3

import os
import glob
import ruamel.yaml as ruamel_yaml
from pathlib import Path
from operator import itemgetter
from datetime import datetime, date, timedelta, timezone
from icalendar import Calendar, Event
from bs4 import BeautifulSoup
import re

# Configuration
OUTPUTFILE = 'new_index.html'
EVENTDIR   = 'events'
ICALDIR    = 'ical'
VERSION    = '1.0'
AUTHORS    = 'sigio,ubuntu-demon,kominoshja,markjanssen,dborghuis,tjclement,dekkers,JolienF,dutchmartin,amarsman,brainsmoke,eloydegen,juerd,stappersg,xesxen,mischapeters,polyfloyd,zeno4ever,toshywoshy,boekenwuurm,dvanzuilekom,elborro'

# Store now to use the same timestamp in all generated files
now = datetime.now(timezone.utc)


# Read yaml event files
all_events = []
yaml = ruamel_yaml.YAML(typ='safe', pure=True)
for filename in glob.glob("events/*.yaml"):
    try:
        with open(filename, "r", encoding="utf-8") as eventfile:
            eventdata = yaml.load(eventfile)

            events=[]
            if isinstance(eventdata, list):
                events.extend(eventdata)
            elif isinstance(eventdata, dict):
                events.append(eventdata)

            for idx, event in enumerate(events):
                filestem = Path(filename).stem
                event['file'] = filestem
                event['iCal'] = f"ical/{filestem}{idx}.ics"

            all_events.extend(events)
    except ruamel_yaml.YAMLError as ex:
        print(f"Error parsing {filename}: {ex}")
    except Exception as ex:
        print(f"Error handling {filename}: {ex}")


# Sort events in chronological order
all_events = sorted(all_events, key=itemgetter('StartDate'))


# Filter already passed events
today = date.today()
upcoming_events = [event for event in all_events if event['StartDate'] <= event['EndDate'] and today <= event['EndDate']]


# Clean up iCalender folder
for filename in glob.glob("ical/*.ics"):
    try:
        os.remove(filename)
    except Exception as ex:
        print(f"Failed to delete {filename}. {ex}")


# Generate iCalendar file with all events
cal = Calendar()
cal.add('prodid', '-//Hack er op uit//hackeropuit.nl//')
cal.add('version', '2.0')

for source_event in all_events:
    event = Event()
    event.add('dtstamp', now)
    event.add('uid', f"/{source_event['Name']}/{source_event['StartDate']}")
    event.add('summary', source_event['Name'])
    event.add('transp', 'TRANSPARENT')
    event.add('dtstart', source_event['StartDate'])
    event.add('dtend', source_event['EndDate'] + timedelta(days=1))
    event.add('location', source_event['Location'])
    event.add('description', source_event['Comment'])
    event.add('url', source_event['URL'])
    cal.add_component(event)

with open('ical/all_events.ics', 'wb') as f:
    f.write(cal.to_ical())


# Generate iCalendar files per event source
files = list({event['file'] for event in all_events})
for file in files:
    source_events = [event for event in all_events if event['file'] == file]

    cal = Calendar()
    cal.add('prodid', '-//Hack er op uit//hackeropuit.nl//')
    cal.add('version', '2.0')

    for source_event in source_events:
        event = Event()
        event.add('dtstamp', now)
        event.add('uid', f"/{source_event['Name']}/{source_event['StartDate']}")
        event.add('summary', source_event['Name'])
        event.add('transp', 'TRANSPARENT')
        event.add('dtstart', source_event['StartDate'])
        event.add('dtend', source_event['EndDate'] + timedelta(days=1))
        event.add('location', source_event['Location'])
        event.add('description', source_event['Comment'])
        event.add('url', source_event['URL'])
        cal.add_component(event)

    with open(f"ical/{file}.ics", 'wb') as f:
        f.write(cal.to_ical())


# Generate iCalendar files per single upcoming event
for source_event in upcoming_events:
    cal = Calendar()
    cal.add('prodid', '-//Hack er op uit//hackeropuit.nl//')
    cal.add('version', '2.0')

    event = Event()
    event.add('dtstamp', now)
    event.add('uid', f"/{source_event['Name']}/{source_event['StartDate']}")
    event.add('summary', source_event['Name'])
    event.add('transp', 'TRANSPARENT')
    event.add('dtstart', source_event['StartDate'])
    event.add('dtend', source_event['EndDate'] + timedelta(days=1))
    event.add('location', source_event['Location'])
    event.add('description', source_event['Comment'])
    event.add('url', source_event['URL'])
    cal.add_component(event)

    with open(source_event['iCal'], 'wb') as f:
        f.write(cal.to_ical())


# Collect key information


# Retrieve timestamp of youngest event file
youngest_event_file = now

try:
  # Get all files (not directories) in the directory with full paths
  directory = EVENTDIR
  files = [os.path.join(directory, f) for f in os.listdir(directory) 
    if os.path.isfile(os.path.join(directory, f))]
    
  if files:
    # Find the file with the latest (youngest) modification time
    youngest_file = max(files, key=os.path.getmtime)
    timestamp = os.path.getmtime(youngest_file)
    youngest_event_file = datetime.fromtimestamp(timestamp)

except Exception as ex:
  print(f"Error retrieving youngest timestamp : {ex}")


# Retrieve all codeowners
authors = ""
try:
  # Read the file
  codeowners_list = []
  with open('.github/CODEOWNERS', 'r', encoding='utf-8') as file:
    codeowners_file = file.read()
    codeowners_list = re.findall(r'@(\w+)', codeowners_file)

  author_list = AUTHORS.split(',')
  author_list.extend(codeowners_list)

  author_list = [author.strip().lower() for author in author_list]

  authors = ','.join(sorted(set(author_list)))

except Exception as ex:
  print(f"Error retrieving authors : {ex}")



# Store results in info dictionary
keys = {
    "{{NOW}}"                : now.isoformat(),
    "{{GENERATOR_VERSION}}"  : VERSION,
    "{{GENERATOR_REVISION}}" : datetime.fromtimestamp(os.path.getmtime(__file__)).isoformat(),
    "{{LASTREFRESH}}"        : now.strftime("%Y-%m-%d %H:%M"),
    "{{LASTEDIT}}"           : youngest_event_file.strftime("%Y-%m-%d %H:%M"),
    "{{AUTHORS}}"            : authors
}


# Create static index file

tablefmt = {
    "📅"        : {"hidden":"n", "export":"n", "type":"url", "field":"iCal"},
    "Name"      : {"hidden":"n", "export":"y", "type":"txt", "field":"Name"},
    "Location"  : {"hidden":"n", "export":"y", "type":"txt", "field":"Location"},
    "Date"      : {"hidden":"n", "export":"n", "type":"txt", "field":"StartDate - EndDate"},
    "StartDate" : {"hidden":"y", "export":"y", "type":"txt", "field":"StartDate"},
    "EndDate"   : {"hidden":"y", "export":"y", "type":"txt", "field":"EndDate"},
    "Comment"   : {"hidden":"n", "export":"y", "type":"txt", "field":"Comment"},
    "Website"   : {"hidden":"n", "export":"y", "type":"url", "field":"URL"}
}

field_separators = [' ','-']

def split_by_separators(text, separators):
    escaped = [re.escape(sep) for sep in separators]
    pattern = f"({'|'.join(escaped)})"
    return [part for part in re.split(pattern, text) if part != '']

def get_field_value(event, column_name):
    formatted_value = ""

    try:
        fmt = tablefmt[column_name]

        retrieved = []
        values = []
        fields = split_by_separators(fmt['field'], field_separators)

        for field in fields:
            try:
                value = str(event[field])
                retrieved.append(value)

            except:
                value = str(field)

            values.append(value)

        if len(retrieved) > len(set(retrieved)):
            formatted_value = values[0]
        else:
            formatted_value = "".join(values)

        if fmt['type'] == "url":
            formatted_value = f"<a href='{formatted_value}'>{column_name}</a>"

    except Exception as ex:
        formatted_value = f"get_field_value: {ex}"

    return formatted_value


def get_column_class(column_name):
    class_txt = ""

    fmt = tablefmt[column_name]
    if fmt['hidden'] == 'y':
        class_txt += "hidden-col"

    if fmt['export'] == 'n':
        if class_txt != "":
            class_txt += " "
        class_txt += "noexport"

    return class_txt



#try:
with open("index.tpl", "r", encoding="utf-8") as htmlfile:
    content = htmlfile.read()

    # Find and replace all keys
    for key in keys:
        content = content.replace(key, keys[key])

    # Parse html
    soup = BeautifulSoup(content, "html.parser")
    if not soup:
        print("ERROR Template index.tpl not recognized as HTML")
    else:
        eventtable = soup.find(id="events")

        if not eventtable:
            print('ERROR Eventtable ID not found')
        else:
            table = soup.new_tag("table")
            table['id'] = 'eventtable'
            eventtable.append(table)

            # Create header
            thead = soup.new_tag("thead")
            table.append(thead)

            tr = soup.new_tag("tr")
            thead.append(tr)

            for idx, column_name in enumerate(tablefmt):
                #fmt = tablefmt[key]

                th = soup.new_tag("th")
                th['onclick'] = f'sortTable({idx})'

                class_text = get_column_class(column_name)
                if class_text != "":
                    th['class'] = class_text

                th.string = column_name
                tr.append(th)

            # Create content
            tbody = soup.new_tag("tbody")
            table.append(tbody)

            rowpow = ''
            for idx, event in enumerate(upcoming_events):
                if idx % 2 == 0:
                    rowpos = 'even'
                else:
                    rowpos = 'odd'

                tr = soup.new_tag("tr")
                tr['class'] = rowpos
                tbody.append(tr)

                for column_name in tablefmt:
                    #fmt = tablefmt[column_name]

                    td = soup.new_tag("td")

                    class_text = get_column_class(column_name)
                    if class_text != "":
                       td['class'] = class_text

                    #td.string = get_field_value(event, column_name)
                    #tr.append(td)

                    formatted_value = get_field_value(event, column_name)
                    fragment_soup = BeautifulSoup(formatted_value, "html.parser")
                    td.append(fragment_soup)
                    tr.append(td)



    pretty_safe_html = soup.prettify(formatter="html")
    with open(OUTPUTFILE, "w", encoding="utf-8") as htmlfile:
        htmlfile.write(str(pretty_safe_html))

#except Exception as ex:
#    print(f'Error creating index.html: {ex}')
