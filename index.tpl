<!DOCTYPE html>
<html lang="en-US">
  <head>
    <title>HackErOpUit</title>
    <meta charset="utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="title" property="og:title" content="HackErOpUit" />
    <meta name="keywords" content="hackeropuit, hackoutandabout, workshops, festivities, events, creative, inspirational, fun" />
    <meta name="category" content="Hackerevents" />
    <meta name="description" content="Catalog of upcoming events and workshops for makers, hackers, and other creative minds." />
    <meta name="subject" content="Catalog of upcoming events and workshops for makers, hackers, and other creative minds." />
    <meta name="summary" content="Catalog of upcoming events and workshops for makers, hackers, and other creative minds." />
    <meta name="abstract" content="Catalog of upcoming events and workshops for makers, hackers, and other creative minds." />
    <meta name="revised" content="{{NOW}}" />
    <meta name="url" content="https://hackeropuit.nl" />
    <meta name="identifier-url" content="https://hackeropuit.nl" />
    <meta property="og:image" content="https://hackeropuit.nl/images/hackeropuit_logo_436_2.png" />
    <meta property="og:image:type" content="image/png" />
    <meta property="og:image:width" content="436" />
    <meta property="og:image:height" content="228" />
    <meta property="og:description" content="Catalog of upcoming events and workshops for makers, hackers, and other creative minds." />
    <meta property="og:updated_time" content="{{NOW}}" />
    <meta property="article:published_time" content="{{NOW}}" />
    <meta property="article:authors" content="{{AUTHORS}}" />
    <meta name="generator" content="HackerErOpUit" />
    <meta name="generator_version" content="{{GENERATOR_VERSION}}" />
    <meta name="generator_revision" content="{{GENERATOR_REVISION}}" />
    <meta name="generator_author" content="sigio,foobar,elborro">
    <meta name="robots" content="noindex" />
    <meta name='revisit-after' content='7 days'>
    <meta name="googlebot" content="notranslate" />
    <meta name="googlebot-news" content="nosnippet" /> 
    <link rel="canonical" href="https://hackeropuit.nl" />
    <link rel="stylesheet" href="hackeropuit.css" />
    <link rel="icon" type="image/x-icon" sizes="16x16" href="/images/ico/favicon.ico" />
    <link rel="icon" type="image/png" sizes="640x640" href="/images/ico/favicon.png" />
    <link rel="apple-touch-icon" sizes="640x640" href="/images/ico/favicon.png" />
  </head>

  <body>
    <h1 id="page-header">HackErOpUit</h1>

    <div id="infobar">
      <div id="info-left">
        <input type="text" id="searchInput" placeholder="Search table..." onkeyup="filterTable()" />
        <button onclick="exportTableToCSV()">Export CSV</button>
        <button onclick="exportToICalendar()">Export iCalendar</button>
      </div>
      <div id="info-mid">
        <span>
          Evenement of uitje toevoegen?
          <a href="https://github.com/revspace/hackeropuit">Pull request!</a>
        </span>
      </div>
      <div id="info-right">
        <span id="icalfile"><a href="ical/all_events.ics">📅 [AllEvents.ics]</a></span>
        <span id="lastUpdated">Last edit: {{LASTEDIT}}</span>
        <span id="lastRefresh">Last refresh: {{LASTREFRESH}}</span>
      </div>
    </div>

    <div id="events" />

    <script src="hackeropuit.js" />
  </body>
</html>
