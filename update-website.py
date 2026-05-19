#!/usr/bin/env python3

import os
import glob
import ruamel.yaml as ruamel_yaml
from pathlib import Path
from operator import itemgetter
from datetime import datetime, date, timedelta, timezone
from icalendar import Calendar, Event
from bs4 import BeautifulSoup, CData
from email.utils import format_datetime
import re

# Configuration
SITE_TITLE = 'Hackeropuit'
SITE_DESC = 'Hacky events'
SITE_URL = 'https://hackeropuit.nl'
SITE_LANG = 'en-us'

OUTPUTFILE = 'new_index.html'
EVENTDIR = 'events'
ICALDIR = 'ical'
VERSION = '2.0'
AUTHORS = ("sigio,ubuntu-demon,kominoshja,tjclement,dekkers,JolienF,"
           "dutchmartin,amarsman,brainsmoke,eloydegen,juerd,stappersg,"
           "xesxen,mischapeters,polyfloyd,zeno4ever,toshywoshy,boekenwuurm,"
           "dvanzuilekom,elborro"
           )

RSS_FILE = 'rss.xml'


def read_event_data():
    """
    Read and preprocess all event.yaml files

    Returns:
    all_events -- list with all events represented dict per event
    current_events -- list with current events represented by dict per event
    """

    # Read yaml event files
    all_events = []
    yaml = ruamel_yaml.YAML(typ="safe", pure=True)
    for filename in sorted(glob.glob(f"{EVENTDIR}/*.yaml")):
        try:
            print("Reading file:", filename)
            with open(filename, "r", encoding="utf-8") as eventfile:
                eventdata = yaml.load(eventfile)

                events = []
                if isinstance(eventdata, list):
                    events.extend(eventdata)
                elif isinstance(eventdata, dict):
                    events.append(eventdata)

                for idx, event in enumerate(events):
                    filestem = Path(filename).stem
                    event["file"] = filestem
                    event["iCal"] = f"{ICALDIR}/{filestem}{idx}.ics"

                all_events.extend(events)
        except ruamel_yaml.YAMLError as ex:
            print(f"Error parsing {filename}: {ex}")
        except Exception as ex:
            print(f"Error handling {filename}: {ex}")


    # Sort events in chronological order
    all_events = sorted(all_events, key=itemgetter("StartDate"))


    # Filter already passed events
    today = date.today()
    current_events = [
                       event
                       for event in all_events
                       if event["StartDate"] <= event["EndDate"]
                       and today <= event["EndDate"]
                      ]

    return all_events, current_events


def generate_icalendar_files(all_events, current_events, current_time):
    """
    Clean iCal folder and create all .ics files

    Keyword arguments:
    all_events -- list with all events represented by dict per event
    current_events -- list with current events represented by dict per event
    current_time -- datetime with time at startup
    """

    # Clean up iCalender folder
    for filename in sorted(glob.glob(f"{ICALDIR}/*.ics")):
        try:
            os.remove(filename)
        except Exception as ex:
            print(f"Failed to delete {filename}. {ex}")


    # Generate iCalendar file with all events
    cal = Calendar()
    cal.add("prodid", "-//Hack er op uit//hackeropuit.nl//")
    cal.add("version", "2.0")

    for evt in all_events:
        event = Event()
        event.add("dtstamp", current_time)
        event.add("uid", f"/{evt['Name']}/{evt['StartDate']}")
        event.add("summary", evt["Name"])
        event.add("transp", "TRANSPARENT")
        event.add("dtstart", evt["StartDate"])
        event.add("dtend", evt["EndDate"] + timedelta(days=1))
        event.add("location", evt.get("Location"))
        event.add("description", evt.get("Comment"))
        event.add("url", evt.get("URL"))
        cal.add_component(event)

    with open(f"{ICALDIR}/all_events.ics", "wb") as f:
        f.write(cal.to_ical())


    # Generate iCalendar files per event source
    files = list({event["file"] for event in all_events})
    for file in files:
        source_events = [event for event in all_events if event["file"] == file]

        cal = Calendar()
        cal.add("prodid", "-//Hack er op uit//hackeropuit.nl//")
        cal.add("version", "2.0")

        for evt in source_events:
            event = Event()
            event.add("dtstamp", current_time)
            event.add("uid", f"/{evt['Name']}/{evt['StartDate']}")
            event.add("summary", evt["Name"])
            event.add("transp", "TRANSPARENT")
            event.add("dtstart", evt["StartDate"])
            event.add("dtend", evt["EndDate"] + timedelta(days=1))
            event.add("location", evt.get("Location"))
            event.add("description", evt.get("Comment"))
            event.add("url", evt.get("URL"))
            cal.add_component(event)

        with open(f"{ICALDIR}/{file}.ics", 'wb') as f:
            f.write(cal.to_ical())


    # Generate iCalendar files per single upcoming event
    for evt in current_events:
        cal = Calendar()
        cal.add('prodid', '-//Hack er op uit//hackeropuit.nl//')
        cal.add('version', '2.0')

        event = Event()
        event.add("dtstamp", current_time)
        event.add("uid", f"/{evt['Name']}/{evt['StartDate']}")
        event.add("summary", evt["Name"])
        event.add("transp", "TRANSPARENT")
        event.add("dtstart", evt["StartDate"])
        event.add("dtend", evt["EndDate"] + timedelta(days=1))
        event.add("location", evt.get("Location"))
        event.add("description", evt.get("Comment"))
        event.add("url", evt.get("URL"))
        cal.add_component(event)

        with open(evt["iCal"], "wb") as f:
            f.write(cal.to_ical())


def collect_key_information(current_time):
    """
    Fill meta information array 

    Keyword arguments:
    current_time -- datetime with time at startup

    Returns:
    dict with collected values
    """

    # Retrieve timestamp of youngest event file
    youngest_event_file = current_time

    try:
        # Get all files (not directories) in the directory with full paths
        files = [os.path.join(EVENTDIR, f)
                 for f in os.listdir(EVENTDIR)
                 if os.path.isfile(os.path.join(EVENTDIR, f))
                 ]

        if files:
            # Find the file with the latest (youngest) modification time
            youngest_file = max(files, key=os.path.getmtime)
            timestamp = os.path.getmtime(youngest_file)
            youngest_event_file = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    except Exception as ex:
        print(f"Error retrieving youngest timestamp : {ex}")


    # Determine authors
    # 1. Use manual maintained author list and
    # 2. update with whomever is mentioned in codeowners file
    authors = ""
    try:
        # Read the file
        codeowners_list = []
        with open(".github/CODEOWNERS", 'r', encoding="utf-8") as file:
            codeowners_file = file.read()
            codeowners_list = re.findall(r'@(\w+)', codeowners_file)

        author_list = AUTHORS.split(",")
        author_list.extend(codeowners_list)

        author_list = [author.strip().lower() for author in author_list]

        authors = ",".join(sorted(set(author_list)))

    except Exception as ex:
        print(f"Error retrieving authors : {ex}")


    # Store results in info dictionary
    keys = {
        "{{NOW}}": current_time.isoformat(),
        "{{GENERATOR_VERSION}}": VERSION,
        "{{GENERATOR_REVISION}}": datetime.fromtimestamp(
                                                        os.path.getmtime(__file__)
                                                        )
                                          .isoformat(),
        "{{LASTREFRESH}}": current_time.strftime("%Y-%m-%d %H:%M"),
        "{{LASTEDIT}}": youngest_event_file.strftime("%Y-%m-%d %H:%M"),
        "{{AUTHORS}}": authors
    }

    return keys


# Define table structure
tablefmt = {
    "📅": {"hidden": "n",
            "export": "n",
            "sortable": "n",
            "type": "url",
            "field": "iCal"},
    "Name": {"hidden": "n",
             "export": "y",
              "sortable": "y",
             "type": "txt",
             "field": "Name"},
    "Location": {"hidden": "n",
                 "export": "y",
                 "sortable": "y",
                 "type": "txt",
                 "field": "Location"},
    "Date": {"hidden": "n",
             "export": "n",
             "sortable": "y",
             "type": "txt",
             "field": "StartDate - EndDate"},
    "StartDate": {"hidden": "y",
                  "export": "y",
                  "sortable": "n",
                  "type": "txt",
                  "field": "StartDate"},
    "EndDate": {"hidden": "y",
                "export": "y",
                "sortable": "n",
                "type": "txt",
                "field": "EndDate"},
    "Comment": {"hidden": "n",
                "export": "y",
                "sortable": "y",
                "type": "txt",
                "field": "Comment"},
    "Website": {"hidden": "n",
                "export": "y",
                "sortable": "n",
                "type": "url",
                "field": "URL"}
}

field_separators = [' ', '-']

def split_by_separators(text, separators):
    """
    Split definition into separate fieldnames based on defined field separators

    Keyword arguments:
    text -- the text to split into multiple fragments
    separators -- list with separators

    Returns:
    list with values filtered from text
    """
    escaped = [re.escape(sep) for sep in separators]
    pattern = f"({'|'.join(escaped)})"
    return [part for part in re.split(pattern, text) if part != '']


def get_field_value(event, column_name):
    """
    Get value based on definition in tablefmt

    Keyword arguments:
    event -- dict with event data
    column_name -- name of column specifying event source and formatter

    Returns:
    text filled with event values formatted according to spec for column_name
    """
    formatted_value = ""

    try:
        fmt = tablefmt[column_name]

        retrieved = []
        values = []
        fields = split_by_separators(fmt["field"], field_separators)

        for field in fields:
            try:
                value = str(event[field])
                retrieved.append(value)

            except Exception:
                value = str(field)

            values.append(value)

        if len(retrieved) > len(set(retrieved)):
            formatted_value = values[0]
        else:
            formatted_value = "".join(values)

        if fmt["type"] == "url":
            formatted_value = f"<a href='{formatted_value}'>{column_name}</a>"

    except Exception as ex:
        formatted_value = f"get_field_value: {ex}"

    return formatted_value


def get_column_class(column_name):
    """
    Get class name(s) based on definition in tablefmt

    Keyword arguments:
    column_name -- name of column specifying column classes

    Returns:
    text with all html class names defined for specified column
    """
    class_txt = ""

    fmt = tablefmt[column_name]
    if fmt["hidden"] == "y":
        class_txt += "hidden-col"

    if fmt["export"] == "n":
        if class_txt != "":
            class_txt += " "
        class_txt += "noexport"

    return class_txt


def generate_index_html(current_events, key_info):
    """
    Create new index.html by filling a copy of the index.tpl template
    1. Find and replace all meta data
    2. Create table with event information

    Keyword arguments:
    current_events -- list with current events represented by dict per event
    key_info -- list with meta values
    """

    try:
        with open("index.tpl", "r", encoding="utf-8") as htmlfile:
            content = htmlfile.read()

            # Find and replace all keys
            for key in key_info:
                content = content.replace(key, key_info[key])

            # Parse html
            soup = BeautifulSoup(content, "html.parser")
            if not soup:
                print("ERROR Template index.tpl not recognized as HTML")
            else:
                eventtable = soup.find(id="events")

                if not eventtable:
                    print("ERROR Eventtable ID not found")
                else:
                    table = soup.new_tag("table")
                    table["id"] = "eventtable"
                    eventtable.append(table)

                    # Create header
                    thead = soup.new_tag("thead")
                    table.append(thead)

                    tr = soup.new_tag("tr")
                    thead.append(tr)

                    for idx, column_name in enumerate(tablefmt):
                        th = soup.new_tag("th")
                        if tablefmt[column_name]["sortable"] == "y":
                            th["onclick"] = f"sortTable({idx})"

                        class_text = get_column_class(column_name)
                        if class_text != "":
                            th["class"] = class_text

                        label = column_name
                        if tablefmt[column_name]["field"] == "iCal":
                            label = f"<a href='ical/all_events.ics'>{label}</a>"

                        fragment_soup = BeautifulSoup(label, "html.parser")
                        for child in fragment_soup.contents:
                            th.append(child)
                        tr.append(th)

                    # Create content
                    tbody = soup.new_tag("tbody")
                    table.append(tbody)

                    rowpow = ""
                    for idx, event in enumerate(current_events):
                        if idx % 2 == 0:
                            rowpos = "even"
                        else:
                            rowpos = "odd"

                        tr = soup.new_tag("tr")
                        tr["class"] = rowpos
                        tbody.append(tr)

                        for column_name in tablefmt:
                            td = soup.new_tag("td")

                            class_text = get_column_class(column_name)
                            if class_text != "":
                                td["class"] = class_text

                            formatted_value = get_field_value(event, column_name)
                            fragment_soup = BeautifulSoup(formatted_value, "html.parser")
                            for child in fragment_soup.contents:
                                td.append(child)
                            tr.append(td)

            pretty_safe_html = soup.prettify(formatter="html")
            with open(OUTPUTFILE, "w", encoding="utf-8") as htmlfile:
                htmlfile.write(str(pretty_safe_html))
    
                print(f"Index written to {OUTPUTFILE}")

    except Exception as ex:
        print(f"Error creating index.html: {ex}")


# Convert ISO8601 string to RFC-2822 format required by RSS 2.0
def rfc2822_date(date_value):
    """
    Convert ISO8601 string to RFC-2822 format required by RSS 2.0

    Keyword arguments:
    date_value -- date/time as ISO formatted string value, date, or datetime

    Returns:
    RFC2822 formatted string value as used in RSS 2.0, e-mail, etc.
    """
    rfcdate = ""
    dt = None
    if isinstance(date_value, date):
        dt = datetime.combine(date_value.today(), datetime.min.time())
    elif isinstance(date_value, datetime):
        dt = date_value
    elif isinstance(date_value, str):
        try:
            dt = datetime.fromisoformat(date_value)
        except Exception as e:
            print(
                f"Invalid date {date_value}: {e}"
            )

    if dt:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        rfcdate = format_datetime(dt)

    return rfcdate

def generate_rss_feed(events):
    """
    Create new RSS 2.0 compliant rss.xml file

    Keyword arguments:
    events -- events to represent in the xml file
    """

    # Create XML document
    soup = BeautifulSoup(features="xml")

    # Root RSS tag
    rss = soup.new_tag(
        "rss",
        version="2.0",
        **{
            "xmlns:atom": "http://www.w3.org/2005/Atom"
        }
    )
    soup.append(rss)

    # Channel
    channel = soup.new_tag("channel")
    rss.append(channel)

    # Channel metadata
    title = soup.new_tag("title")
    title.string = SITE_TITLE 
    channel.append(title)

    link = soup.new_tag("link")
    link.string = SITE_URL
    channel.append(link)

    description = soup.new_tag("description")
    description.string = SITE_DESC
    channel.append(description)

    language = soup.new_tag("language")
    language.string = SITE_LANG
    channel.append(language)

    last_build = soup.new_tag("lastBuildDate")
    last_build.string = format_datetime(
        datetime.now(timezone.utc)
    )
    channel.append(last_build)

    # atom:link self-reference
    atom_link = soup.new_tag(
        "atom:link",
        href=f"{SITE_URL}/{RSS_FILE}",
        rel="self",
        type="application/rss+xml"
    )
    channel.append(atom_link)

    # Feed items
    for event in events:
        # Only accept events with all RSS mandatory fields supplied
        if event["Name"] and event["URL"] and event["Comment"]:
            item = soup.new_tag("item")
            channel.append(item)

            # title
            item_title = soup.new_tag("title")
            item_title.string = event["Name"]
            item.append(item_title)

            # link
            item_link = soup.new_tag("link")
            item_link.string = event["URL"]
            item.append(item_link)

            # description
            item_description = soup.new_tag("description")
            item_description.append(
                CData(event["Comment"])
            )
            item.append(item_description)

            # guid
            guid = soup.new_tag(
                "guid",
                isPermaLink="false"
            )
            guid.string = "".join(f"{event['Name']}:{event['StartDate']}".split())
            item.append(guid)

            # pubDate
            if event["StartDate"]:
                try:
                    pub_date = soup.new_tag("pubDate")
                    pub_date.string = rfc2822_date(event["StartDate"])
                    item.append(pub_date)

                except Exception as e:
                    print(
                        f"Invalid startdate "
                        f"{event['StartDate']}: {e}"
                    )

    # Write XML output
    with open(RSS_FILE, "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    print(f"RSS feed written to {RSS_FILE}")

def generate_rss_event_feed(events):
    """
    Create new RSS 2.0 compliant rss.xml events file

    Keyword arguments:
    events -- events to represent in the xml file
    """

    # https://web.resource.org/rss/1.0/modules/event/
    # https://validator.w3.org/feed/docs/howto/declare_namespaces.html
    # https://validator.w3.org/feed/check.cgi
    # http://www.gsite.org/RSS/modules/event_dates/
    # https://cyber.harvard.edu/rss/
    # https://www.rssboard.org/rss-specification

    # Create XML document
    soup = BeautifulSoup(features="xml")

    # Root RSS tag
    rss = soup.new_tag(
        "rss",
        version="2.0",
        **{
            "xmlns:ev": "http://purl.org/rss/2.0/modules/event/"
        }
    )
    soup.append(rss)

    # Channel
    channel = soup.new_tag("channel")
    rss.append(channel)

    # Channel metadata
    title = soup.new_tag("title")
    title.string = SITE_TITLE 
    channel.append(title)

    link = soup.new_tag("link")
    link.string = SITE_URL
    channel.append(link)

    description = soup.new_tag("description")
    description.string = SITE_DESC
    channel.append(description)

    language = soup.new_tag("language")
    language.string = SITE_LANG
    channel.append(language)

    last_build = soup.new_tag("lastBuildDate")
    last_build.string = format_datetime(
        datetime.now(timezone.utc)
    )
    channel.append(last_build)

    # atom:link self-reference
    atom_link = soup.new_tag(
        "atom:link",
        href=f"{SITE_URL}/{RSS_FILE}",
        rel="self",
        type="application/rss+xml"
    )
    channel.append(atom_link)

    # Feed items
    for event in events:
        # Only accept events with all RSS mandatory fields supplied
        if event["Name"] and event["URL"] and event["Comment"]:
            item = soup.new_tag("item")
            channel.append(item)

            # title
            item_title = soup.new_tag("title")
            item_title.string = event["Name"]
            item.append(item_title)

            # link
            item_link = soup.new_tag("link")
            item_link.string = event["URL"]
            item.append(item_link)

            # description
            item_description = soup.new_tag("description")
            item_description.append(
                CData(event["Comment"])
            )
            item.append(item_description)

            # guid
            guid = soup.new_tag(
                "guid",
                isPermaLink="false"
            )
            guid.string = "".join(f"{event['Name']}:{event['StartDate']}".split())
            item.append(guid)

            # pubDate
            if event["StartDate"]:
                try:
                    pub_date = soup.new_tag("pubDate")
                    pub_date.string = rfc2822_date(event["StartDate"])
                    item.append(pub_date)

                except Exception as e:
                    print(
                        f"Invalid startdate "
                        f"{event['StartDate']}: {e}"
                    )


    # Write XML output
    with open(RSS_FILE, "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    print(f"RSS event feed written to {RSS_FILE}")


def main():
    # Store current time to use the same timestamp in all generated files
    now = datetime.now(timezone.utc)

    # Read all event.yaml files
    all_events, current_events = read_event_data()

    # Create/refresh all .ics files
    generate_icalendar_files(all_events, current_events, now)

    # Collect meta information
    key_info = collect_key_information(now)

    # Create/refresh index.html
    generate_index_html(current_events, key_info)

    # Create/refresh rss.xml
    generate_rss_feed(current_events)
    #generate_rss_event_feed(current_events)

if __name__ == "__main__":
    main()
