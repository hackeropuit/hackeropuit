function getJSON(url) {
  var resp;
  var xmlHttp;

  resp = '';
  xmlHttp = new XMLHttpRequest();

  if (xmlHttp != null) {
    xmlHttp.open("GET", url, false);
    xmlHttp.send(null);
    resp = xmlHttp.responseText;
  }

  return resp;
}

//var jsondata = getJSON('https://hackeropuit.nl/events.json');
var jsondata = getJSON('events.json');
var columns = ["Name", "Location", "StartDate", "EndDate", "Comment", "URL"]

// (B) PARSE JSON INTO OBJECT
var data = JSON.parse(jsondata);
var parsed = data.events;
console.table(parsed);

// Display the last updated timestamp
var updatedElem = document.getElementById("lastUpdated");
if (updatedElem && data.last_updated) {
  updatedElem.innerText = "Laatst bijgewerkt: " + data.last_updated;
}

// (C) TABLE HEADER
var theWrap = document.getElementById("tableWrap");
var theCell = null;
for (let key in columns) {
  theCell = document.createElement("div");
  theCell.innerHTML = columns[key];
  theCell.classList.add("cell");
  theCell.classList.add("head");
  theWrap.appendChild(theCell);
}

// (D) TABLE CELLS
var theEvent = null;
var altRow = false;
for (let key in parsed) {
  theEvent = parsed[key];
  for (let i in theEvent) {
    theCell = document.createElement("div");
    if (i == "URL") {
      if (theEvent[i] != null) {
        theCell.innerHTML = "<A HREF='" + theEvent[i] + "'>" + theEvent[i] + "</A>";
      }
    } else {
      theCell.innerHTML = theEvent[i];
    }
    theCell.classList.add("cell");
    if (altRow) {
      theCell.classList.add("alt");
    }
    theWrap.appendChild(theCell);
  }
  altRow = !altRow;
}
