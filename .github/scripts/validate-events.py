#!/usr/bin/env python3

import glob
import sys
from datetime import datetime
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

CRITICAL_FIELDS = ["Name", "StartDate"]
WARNING_FIELDS = ["EndDate", "URL", "Comment"]
DATE_FMT = "%Y-%m-%d"

errors = []

for file in glob.glob("events/*.yaml"):
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = yaml.load(f)
    except Exception as e:
        errors.append(f"{file}: YAML syntax error - {e}")
        continue

    if not isinstance(data, list):
        errors.append(f"{file}: Expected a list of event entries")
        continue

    for i, event in enumerate(data):
        missing_critical = [f for f in CRITICAL_FIELDS if f not in event or not event[f]]
        missing_warn = [f for f in WARNING_FIELDS if f not in event or not event[f]]
    
        if missing_critical:
            errors.append(f"{file} (event {i}): Missing required fields: {', '.join(missing_critical)}")
    
        for f in missing_warn:
            print(f"WARNING: {file} (event {i}): Field '{f}' is missing or empty")
    
        if "StartDate" in event and "EndDate" in event and event.get("StartDate") and event.get("EndDate"):
            try:
                start = datetime.strptime(str(event["StartDate"]), DATE_FMT)
                end = datetime.strptime(str(event["EndDate"]), DATE_FMT)
                if end < start:
                    print(f"WARNING: {file} (event {i}): EndDate '{event['EndDate']}' is before StartDate '{event['StartDate']}' — this event will be ignored later.")
            except Exception as e:
                errors.append(f"{file} (event {i}): Date parsing error - {e}")

if errors:
    print("Validation failed with the following errors:\n")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)
else:
    print("All YAML event files are valid.")

