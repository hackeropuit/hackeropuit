let sortDirection = {};

function sortTable(colIndex) {
  const table = document.getElementById("eventtable");
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);
  const ths = table.querySelectorAll("th");

  ths.forEach((th) => th.classList.remove("sorted-asc", "sorted-desc"));
  sortDirection[colIndex] = !sortDirection[colIndex];

  rows.sort((a, b) => {
    const aText = a.cells[colIndex].textContent.trim().toLowerCase();
    const bText = b.cells[colIndex].textContent.trim().toLowerCase();
    const isDate = !isNaN(Date.parse(aText)) && !isNaN(Date.parse(bText));
    return sortDirection[colIndex]
      ? isDate
        ? new Date(aText) - new Date(bText)
        : aText.localeCompare(bText)
      : isDate
        ? new Date(bText) - new Date(aText)
        : bText.localeCompare(aText);
  });

  rows.forEach((row, index) => {
    row.classList.remove("odd", "even");
    row.classList.add(index % 2 === 0 ? "even" : "odd");
    tbody.appendChild(row);
  });

  ths[colIndex].classList.add(
    sortDirection[colIndex] ? "sorted-asc" : "sorted-desc",
  );
}

function filterTable() {
  const input = document.getElementById("searchInput");
  const filter = input.value.toLowerCase();
  const table = document.getElementById("eventtable");
  const rows = table.tBodies[0].rows;

  let visibleRowIndex = 0;

  for (let row of rows) {
    let match = false;

    for (let cell of row.cells) {
      const plainText = cell.textContent;
      const lowerText = plainText.toLowerCase();

      if (filter && lowerText.includes(filter)) {
        match = true;
        const regex = new RegExp(`(${filter})`, "gi");
        cell.innerHTML = plainText.replace(regex, "<mark>$1</mark>");
      } else {
        cell.innerHTML = plainText;
      }
    }

    if (match || !filter) {
      row.style.display = "";
      row.classList.remove("odd", "even");
      row.classList.add(visibleRowIndex % 2 === 0 ? "even" : "odd");
      visibleRowIndex++;
    } else {
      row.style.display = "none";
      row.classList.remove("odd", "even");
    }
  }
}

function exportTableToCSV() {
  const table = document.getElementById("eventtable");
  const rows = Array.from(table.querySelectorAll("tbody tr")).filter(
    (row) => row.style.display !== "none",
  );
  let csv = [];

  // Get all <th> elements and determine which indexes to include (not marked with 'noexport')
  const thElements = Array.from(table.querySelectorAll("thead th"));
  const includedIndexes = thElements
    .map((th, index) => (th.classList.contains("noexport") ? null : index))
    .filter((index) => index !== null);

  // Build the header row, excluding 'exclude' columns
  const headers = includedIndexes.map((index) =>
    thElements[index].textContent.trim(),
  );
  csv.push(headers.join(","));

  // Process each row
  for (let row of rows) {
    const cells = Array.from(row.cells);
    const filteredCells = includedIndexes.map((index) => {
      const cell = cells[index];
      const link = cell.querySelector("a");
      const content = link ? link.href : cell.textContent;
      const cleaned = content
        .replace(/[\r\n]+/g, " ")
        .trim()
        .replace(/"/g, '""');
      return cleaned;
    });
    csv.push(filteredCells.join(","));
  }

  const csvString = csv.join("\n");
  const blob = new Blob([csvString], { type: "text/csv" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "events.csv";
  link.click();
}

function exportToICalendar() {
  const now = new Date();

  // Find eventtable with data first
  const table = document.getElementById("eventtable");

  // Look for position of required data in the eventtable
  const headerCells = Array.from(table.querySelectorAll("thead th"));
  const summaryIndex = headerCells.findIndex(
    (th) => th.textContent.trim() === "Name",
  );
  const locationIndex = headerCells.findIndex(
    (th) => th.textContent.trim() === "Location",
  );
  const descriptionIndex = headerCells.findIndex(
    (th) => th.textContent.trim() === "Comment",
  );
  const urlIndex = headerCells.findIndex(
    (th) => th.textContent.trim() === "Website",
  );
  const dtStartIndex = headerCells.findIndex(
    (th) => th.textContent.trim() === "StartDate",
  );
  const dtEndIndex = headerCells.findIndex(
    (th) => th.textContent.trim() === "EndDate",
  );

  let icsContent = "";

  // Select all (filtered) rows
  const rows = Array.from(table.querySelectorAll("tbody tr")).filter(
    (row) => row.style.display !== "none",
  );

  for (const row of rows) {
    const cells = row.cells;

    const uid = escapeICalText(
      cells[summaryIndex].textContent.trim() +
        cells[dtStartIndex].textContent.trim(),
    );
    const summary = escapeICalText(cells[summaryIndex].textContent.trim());
    const location = escapeICalText(cells[locationIndex].textContent.trim());
    const description = escapeICalText(
      cells[descriptionIndex].textContent.trim(),
    );
    const link = escapeICalText(cells[urlIndex].querySelector("a")?.href || "");
    const start = formatICalDate(cells[dtStartIndex].textContent.trim());
    const end = formatICalDate(cells[dtEndIndex].textContent.trim());
    const stamp = now.toISOString();

    icsContent += "BEGIN:VEVENT\n";
    icsContent += `UID:${uid}\n`;
    icsContent += `SUMMARY:${summary}\n`;
    icsContent += `LOCATION:${location}\n`;
    icsContent += `DESCRIPTION:${description}\n`;
    icsContent += `URL:${link}\n`;
    icsContent += `DTSTART;VALUE=DATE:${start}\n`;
    icsContent += `DTEND;VALUE=DATE:${end}\n`;
    icsContent += `DTSTAMP;VALUE=DATE:${stamp}\n`;
    icsContent += "END:VEVENT\n";
  }

  icsContent =
    "BEGIN:VCALENDAR\n" +
    "VERSION:2.0\n" +
    "PRODID:-//Hack er op uit//hackeropuit.nl\n" +
    icsContent +
    "END:VCALENDAR";

  const blob = new Blob([icsContent], { type: "text/calendar" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "events.ics";
  link.click();
}

function formatICalDate(dateStr) {
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}${month}${day}`;
}

function escapeICalText(text) {
  return text
    .replace(/\\n/g, "\\n")
    .replace(/,/g, "\\,")
    .replace(/;/g, "\\;")
    .replace(/\r?\n/g, "\\n");
}
