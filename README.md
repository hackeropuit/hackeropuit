# HackErOpUit

An overview of hacker-events in and around the Netherlands

Patches welcome ;) (Both in the code as with new events)

## Contributing:

https://github.com/revspace/hackeropuit/

If requested, I can hand out write permissions (with codeowners) on specific event-files, so events can update these themselves.

Initial versions of the code to parse events and create the website were written by hand, but most changes to code since Jun 2025 have been done by AI coding bots. This includes the linter/workflows.

## Example event data:

```yaml
- Name: Event Name/Title
  Location: City, Country
  StartDate: 2022-07-22
  EndDate: 2022-07-26
  Comment: Something optional
  URL: https://hackeropuit.nl
```

If no date is known yet, just put in an approximate date, but have the end-date be before the start-date, so the entry will be ignored and not printed in the table.
