# ICS-OS

The in-world operating system for ICS Earth Branch: Hearth mail, ICS Cloud Drive and Folio, in one static page (`ics-os.html`). Deployed on Vercel as a plain static site; `/` serves `ics-os.html`.

## Build

The page is generated from the writing repo. Keep `ICS-Writing` next to this folder (or set `ICS_WRITING` to its path), then:

    python build_os.py

This reads `canon/internal-communications/*/*.md` and `canon/documents/2.*.md` and rewrites `ics-os.html`. No database or other dependencies are needed. Current build: 119 messages, 62 documents.

## Adding a document

Add a line for it to `DOCS` in `build_os.py` (number, folder, tier). A document that is missing from `DOCS` is reported as a warning at build time. For documents with `*[Access: X]*` marker lines, add a `LAYERS` entry with `{"access": True, "default": ...}`. The closing `*[PROPOSAL]*` author note is stripped from the body and shown as "Writer's notes" in the All files view.

## Files

- `build_mail.py`: reads and renders messages.
- `build_os.py`: document tables, access layers, and page assembly.
- `os_template.html`, `os.css`, `os.js`: the page shell, styles and script.
- `vercel.json`: static hosting settings.
