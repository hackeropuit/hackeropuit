#!/usr/bin/env python3

# Install required libraries in environment
# pip install ruamel.yaml
# pip install icalendar
# pip install beautifulsoup4
# pip install lxml

# Dependencies
# * Directories
#   - events
#   - ical
# * Files
#   - .github/CODEOWNERS
#   - favicon.ico
#   - hackeropuit.css
#   - hackeropuit.js
#   - hackeropuit-header.jpg
#   - hackeropuit-index.tpl
#   - OCRAStd.woff
#   - rss.gif
#   - update-website.py


import os
import glob
from ruamel.yaml import YAML, YAMLError
from pathlib import Path
from operator import itemgetter
from datetime import datetime, date, timedelta, timezone
from icalendar import Calendar, Event
from bs4 import BeautifulSoup, CData
from email.utils import format_datetime
import re

# Configuration
SITE_TITLE = "Hackeropuit"
SITE_DESC = "The best overview of which cool maker events, festive parties, educational workshops, and other remarkable events are coming up."
SITE_URL = "https://hackeropuit.nl"
SITE_LANG = "en-us"

OUTPUTFILE = "new_index.html"

RSS_FILE = "rss.xml"
RSS_DAYS = 180

ATOM_FILE = "atom.xml"
ATOM_DAYS = 180
ATOM_CATS = "Hackers,Workshops,Events,Festivities"

EVENTDIR = "events"
ICALDIR = "ical"
VERSION = "2.0"
AUTHORS = ("sigio,ubuntu-demon,kominoshja,tjclement,dekkers,JolienF,"
           "dutchmartin,amarsman,brainsmoke,eloydegen,juerd,stappersg,"
           "xesxen,mischapeters,polyfloyd,zeno4ever,toshywoshy,boekenwuurm,"
           "dvanzuilekom,elborro"
           )


def read_event_data():
    """
    Read and preprocess all event.yaml files

    Returns:
    all_events -- list with all events represented dict per event
    current_events -- list with current events represented by dict per event
    """

    # Read yaml event files
    all_events = []
    yaml = YAML(typ="safe", pure=True)
    for filename in sorted(glob.glob(f"{EVENTDIR}/*.yaml")):
        try:
            print("Reading file:", filename)

            pubDate = datetime.fromtimestamp(os.path.getmtime(filename), tz=timezone.utc)

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
                    event["pubDate"] = pubDate

                    # OPTIONAL new fields to enrich information in feeds (atom)
                    if not "Authors" in event:
                        event["Authors"] = None

                    if not "Summary" in event:
                        event["Summary"] = None

                    if not "Content" in event:
                        event["Content"] = None

                    if not "Categories" in event:
                        event["Categories"] = None

                    if not "Contributors" in event:
                        event["Contributors"] = None

                all_events.extend(events)
        except YAMLError as ex:
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
    author_list = AUTHORS.split(",")
    try:
        # Read the file
        codeowners_list = []
        with open(".github/CODEOWNERS", 'r', encoding="utf-8") as file:
            codeowners_file = file.read()
            codeowners_list = re.findall(r'@(\w+)', codeowners_file)
            author_list.extend(codeowners_list)

    except Exception as ex:
        print(f"Error retrieving authors : {ex}")

    author_list = [author.strip().lower() for author in author_list]
    authors = ",".join(sorted(set(author_list)))


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
        "{{AUTHORS}}": authors,
        "{{RSSFEED}}": f"{SITE_URL}/{RSS_FILE}",
        "{{ATOMFEED}}": f"{SITE_URL}/{ATOM_FILE}"
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

def pretty_minify(soup, formatter="minimal"):
    """
    Convert the beautifulsoup structure into a nicely formatted xml
    structure, but wihout the excessive whitespace what's breaking
    some online xml formats like Atom.

    Keyword arguments:
    soup -- filled beautifulsoup instance to format
    soup -- filled beautifulsoup instance to format

    Returns:
    Text with minified pretty xml structure
    """
    minified = re.sub(
        r'(<(\w+)[^>]*>)\s*([^<\n][^<]*?)\s*(</\2>)',
        lambda m: f"{m.group(1)}{m.group(3).strip()}{m.group(4)}",
        soup.prettify(formatter=formatter)
    )
    return minified

def generate_index_html(current_events, key_info):
    """
    Create new index.html by using hackeropuit-index.tpl template
    1. Find and replace all meta data
    2. Create table with event information

    Keyword arguments:
    current_events -- list with current events represented by dict per event
    key_info -- list with meta values
    """

    try:
        with open("hackeropuit-index.tpl", "r", encoding="utf-8") as htmlfile:
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

            pretty_safe_html = pretty_minify(soup, formatter="html")
            with open(OUTPUTFILE, "w", encoding="utf-8") as htmlfile:
                htmlfile.write(str(pretty_safe_html))
    
                print(f"Index written to {OUTPUTFILE}")

    except Exception as ex:
        print(f"Error creating index.html: {ex}")

# Convert ISO8601 string to RFC-2822 format required by RSS 2.0
# This thing is butt ugly and needs a revisit/rewrite later.
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
        dt = datetime.combine(date_value, datetime.min.time())
        #print(f"1a {date_value} : {str(dt)}")
    elif isinstance(date_value, datetime):
        dt = date_value
        #print(f"1b {date_value} : {str(dt)}")
    elif isinstance(date_value, str):
        try:
            dt = datetime.fromisoformat(date_value)
            #print(f"1c {date_value} : {str(dt)}")
        except Exception as e:
            print(
                f"Invalid date {date_value}: {e}"
            )

    if dt:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        #print(f"2 {date_value} : {str(dt)}")
        rfcdate = format_datetime(dt)
        #print(f"3 {date_value} : {rfcdate}")

    return rfcdate

def generate_rss_feed(events, now):
    """
    Create new RSS 2.0 compliant rss.xml file

    Keyword arguments:
    events -- events to represent in the xml file
    now -- timestamp with current date and time
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

    rss_delta = date.today() + timedelta(days=RSS_DAYS)
    rss_events = [
                   event
                   for event in events
                   if event["StartDate"] <= rss_delta
                  ]

    # Feed items
    for event in rss_events:
        # Only accept events with all RSS mandatory fields supplied
        # AND StartDate and EndDate
        if (
            event["Name"] 
            and event["URL"]
            and event["Comment"]
            and event['StartDate']
            and event['EndDate']
        ):
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
            description = get_field_value(event, 'Date') + "<br>" + event["Comment"]
            item_description.append(CData(description))
            item.append(item_description)

            # guid
            guid = soup.new_tag(
                "guid",
                isPermaLink="true"
            )
            guid.string = f"{SITE_URL}/{event['iCal']}"
            item.append(guid)

            # pubDate
            pub_date = soup.new_tag("pubDate")
            #pub_date.string = rfc2822_date(event["StartDate"])
            pub_date.string = rfc2822_date(event["pubDate"])
            #pub_date.string = str(event["pubDate"])
            item.append(pub_date)

    # Write XML output
    with open(RSS_FILE, "w", encoding="utf-8") as f:
        f.write(pretty_minify(soup))

    print(f"RSS feed written to {RSS_FILE}")

def generate_atom_feed(events, now):
    """
    Create new ATOM 1.0 compliant news feed

    Keyword arguments:
    events -- events to represent in the xml file
    now -- timestamp with current date and time
    """

    # https://validator.w3.org/feed/docs/atom.html

    # Create XML document
    soup = BeautifulSoup(features="xml")

    # Root RSS tag
    feed = soup.new_tag(
        "feed",
        #version="2.0",
        **{
            "xmlns": "http://www.w3.org/2005/Atom",
            "xmlns:thr": "http://purl.org/syndication/thread/1.0",
            "xml:lang": SITE_LANG
        }
    )
    soup.append(feed)

    # Feed ID
    feedid = soup.new_tag("id")
    feedid.string = f"{SITE_URL}/{ATOM_FILE}"
    feed.append(feedid)

    # Feed Site reference
    link = soup.new_tag(
        "link",
        **{
            "rel": "alternate",
            "type": "text/html",
            "href": SITE_URL
        }
    )
    feed.append(link)

    # Feed Atom reference
    atom_link = soup.new_tag(
        "link",
        **{
            "rel": "self",
            "type": "application/atom+xml",
            "href": f"{SITE_URL}/{ATOM_FILE}"
        }
    )
    feed.append(atom_link)

    # Feed title
    title = soup.new_tag(
        "title",
        **{
            "type": "text"
        }
    )
    title.string = SITE_TITLE 
    feed.append(title)

    # Feed subtitle
    subtitle = soup.new_tag(
        "subtitle",
        **{
            "type": "text"
        }
    )
    subtitle.string = SITE_DESC 
    feed.append(subtitle)

    # Feed update timestamp
    updated = soup.new_tag("updated")
    updated.string = now.isoformat()
    feed.append(updated)

    # Feed author
    author = soup.new_tag("author")
    author_name = soup.new_tag("name")
    author_name.string = SITE_TITLE
    author.append(author_name)
    feed.append(author)

    # categories
    categories = ATOM_CATS.split(",")
    for category in categories:
        atom_category = soup.new_tag(
            "category",
            **{
                "scheme": SITE_URL,
                "term": category
            }
        )
        feed.append(atom_category)

    # Feed icon
    icon = soup.new_tag("icon")
    icon.string = f"{SITE_URL}/{ATOM_FILE}"
    feed.append(icon)

    # Filter feed content items ready to publish
    atom_delta = date.today() + timedelta(days=ATOM_DAYS)
    atom_events = [
                   event
                   for event in events
                   if event["StartDate"] <= atom_delta
                  ]

    # Feed content
    for event in atom_events:
        # Only accept events with all RSS mandatory fields supplied
        # AND StartDate and EndDate
        if (
            event["Name"] 
            and event["URL"]
            and event["Comment"]
            and event['StartDate']
            and event['EndDate']
        ):
            entry = soup.new_tag("entry")
            feed.append(entry)

            # id
            entry_id = soup.new_tag("id")
            entry_id.string = f"{SITE_URL}/{event['iCal']}"
            entry.append(entry_id)

            # title
            entry_title = soup.new_tag(
                "title",
                **{
                    "type": "html"
                }
            )
            entry_title.string = CData(event["Name"])
            entry.append(entry_title)

            # updated 
            entry_updated = soup.new_tag("updated")
            entry_updated.string = event["pubDate"].isoformat()
            entry.append(entry_updated)

            # link
            entry_link = soup.new_tag(
                "link",
                **{
                    "rel": "alternate",
                    "type": "text/html",
                    "href": event["URL"]
                }
            )
            entry.append(entry_link)

            # author
            if event["Authors"]:
                entry_author = soup.new_tag("author")

                authors = event["Authors"].split(",")
                for author in authors:
                    author_name = soup.new_tag("name")
                    author_name.string = author
                    entry_author.append(author_name)

                entry.append(entry_author)

            # summary
            summary = ""
            if event["Summary"]:
                summary = event["Summary"]
            else:
                summary = get_field_value(event, 'Date') + " " + event["Comment"]

            entry_summary = soup.new_tag(
                "summary",
                **{
                    "type": "html"
                }
            )
            entry_summary.string = CData(summary)
            entry.append(entry_summary)

            # content
            content = ""
            if event["Content"]:
                content = event["Content"]
            else:
                content = event["Comment"]

            entry_content = soup.new_tag(
                "content",
                **{
                    "type": "html"
                }
            )
            entry_content.string = CData(content)
            entry.append(entry_content)

            # published 
            entry_pubdate = soup.new_tag("published")
            entry_pubdate.string = event["pubDate"].isoformat()
            entry.append(entry_pubdate)

            # categories
            if event["Categories"]:
                categories = event["Categories"].split(",")
                for category in categories:
                    entry_category = soup.new_tag(
                        "category",
                        **{
                            "scheme": SITE_URL,
                            "term": category
                        }
                    )
                    entry.append(entry_category)

            # contributors
            if event["Contributors"]:
                entry_contributor = soup.new_tag("contributor")

                contributors = event["Contributors"].split(",")
                for contributor in contributors:
                    contributor_name = soup.new_tag("name")
                    contributor_name.string = contributor
                    entry_contributor.append(contributor_name)

                entry.append(entry_contributor)


    # Write XML output
    with open(ATOM_FILE, "w", encoding="utf-8") as f:
        f.write(pretty_minify(soup))

    print(f"ATOM feed written to {ATOM_FILE}")


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
    generate_rss_feed(current_events, now)

    # Create/refresh atom_rss.xml
    generate_atom_feed(current_events, now)

if __name__ == "__main__":
    main()
