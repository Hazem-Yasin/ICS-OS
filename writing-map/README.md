# writing-map

A map of the writing repo (`ICS-Writing`): every file, how files reference each other, canon-rule checks, a timeline, a people graph, and a SQLite database behind it. Python 3 standard library only; the viewer works offline.

It lives here, in the ICS-OS repo, so the writing repo stays writing only. It reads `../ICS-Writing` (or the folder in `ICS_WRITING`) and never writes there.

## Use it

    python writing-map/build_map.py          # rebuild, then open writing-map/writing_map.html
    python writing-map/build_map.py --quiet  # no output
    python writing-map/watch.py              # rebuild a few seconds after you stop editing
    python writing-map/build_map.py --cat <scan#> "<path>"   # a file as it was in an earlier scan

Each run is compared with the previous scan and, if nothing changed, nothing new is recorded. Every run also rebuilds `ics-os.html` (it calls `build_os.build()`), so one command refreshes both. To rebuild only the OS: `python build_os.py`.

`writing_map.db` and `writing_map.html` are generated and git-ignored. The database keeps the scan history (a compressed copy of every file version), so it only exists on the machine that built it.

## What it scans

`.md` files under `canon/`, `story/` and `design/`, plus the repo `README.md`. `meta/` and `reference/` are generated or working files and are left out. The map's classifier was written for the old single `writing/` folder, so `LAYOUT` at the top of `build_map.py` turns a current path into that old layout (for example `canon/documents/2.01…` becomes `documents/2.01…`). The Explorer shows the real path. Path references resolve in either form.

## Viewer tabs

Overview, Graph, People, Timeline, Coverage, Canon, Health, Matrix, Explorer, Database ERD, Export, History. Same as before; see the viewer's own help text.

## Canon rules

`canon_rules.json` holds rules of the form `{id, label, pattern, allowed, line_filter, line_exclude, flags, ignore_files}` plus `accepted` exceptions. Copy an entry to add one, rebuild, and look at the Canon tab. `@doc_count` in `allowed` means the number of documents on disk.

## Known gaps

- Message and document references for items that moved (for example `writing/…` paths in old notes) show as broken in Health.
- The repo's own checker, `python3 tools/ics.py check` in ICS-Writing, is separate and is the one used for sign-off.
