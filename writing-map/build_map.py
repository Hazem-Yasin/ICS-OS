#!/usr/bin/env python3
"""
ICS - Rigged Sphere :: Writing Map builder
==========================================

Scans everything inside ../writing, then produces:

  writing_map.db    SQLite database (the "real" ERD: files, documents, messages,
                    characters, people, levels, weapons, refs, concepts, ...)
                    Scan history is PERSISTENT across runs, so you can always
                    see what was added / changed / deleted / moved since last time.
  writing_map.html  A self-contained, offline viewer (graph, ERD, explorer,
                    heat-matrix, health report, change history).

Usage (from anywhere):
    python writing-map/build_map.py

Re-run it any time the writing changes. Only Python's standard library is used.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analysis  # noqa: E402

OS_ROOT = HERE.parent
# The writing lives in its own repo, a sibling of this one (or the folder named in ICS_WRITING).
WRITING = Path(os.environ.get("ICS_WRITING") or OS_ROOT.parent / "ICS-Writing")
ROOT = WRITING
# The map still classifies files by their old writing/ layout. These rules turn a path in the
# current repo into that layout; anything not listed is left out of the map.
LAYOUT = [
    ("canon/", ""), ("story/scene-notes/", "scene-notes/"), ("story/scenes/", "scenes/"),
    ("story/trailers/", "trailers/"), ("story/", ""), ("design/", ""),
]
REAL = {}   # map path -> path in the writing repo
DB_PATH = HERE / "writing_map.db"
HTML_PATH = HERE / "writing_map.html"
TEMPLATE_PATH = HERE / "template.html"
CANON_PATH = HERE / "canon_rules.json"
SKIP_DIRS = {".obsidian"}
QUIET = False
EXPLICIT = ("document", "message", "character", "path", "weapon")

# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------
CATS = {
    "canon":        ("Canon & index",         "#f2c14e"),
    "systems":      ("Game systems",          "#4f9cf9"),
    "characters":   ("Characters",            "#ef6f8e"),
    "documents":    ("In-world documents",    "#8e7cf8"),
    "enemies":      ("Enemies",               "#e8573f"),
    "facility":     ("Facility / levels",     "#3fc7b4"),
    "comms":        ("Comms index",           "#9aa5b8"),
    "msg-employee": ("Msgs: employee (A)",    "#6fcf6f"),
    "msg-ptkw":     ("Msgs: PTKW (B)",        "#f28c38"),
    "msg-director": ("Msgs: director (C)",    "#d86bd8"),
    "msg-design":   ("Msgs: design team (D)", "#b7d84a"),
    "scenes":       ("Scene notes",           "#56c2f0"),
    "trailers":     ("Trailers",              "#ff9db1"),
    "weapons":      ("Weapons",               "#c7a27c"),
    "config":       ("Config",                "#6b7280"),
}
CANON_FILES = {"DESIGN", "STORY", "EXTENDED", "README"}
FOLDER_CAT = {
    "scenes": "scenes",
    "characters": "characters", "documents": "documents", "enemies": "enemies",
    "facility": "facility", "scene-notes": "scenes", "trailers": "trailers",
    "weapons": "weapons",
}
COMMS_CAT = {
    "employee": "msg-employee", "ptkw": "msg-ptkw",
    "branch-director": "msg-director", "design-team": "msg-design",
}
SERIES = {"A": "employee", "B": "ptkw", "C": "branch-director", "D": "design-team"}


def stem(name):
    return name[:-3] if name.lower().endswith(".md") else name


def strip_lead(s):
    """Remove leading separators such as ' - ', ' â€” ', mojibake, etc."""
    return re.sub(r"^[^\w(]+", "", s).strip()


def classify(rel):
    """Return (cat, kind, code, title_hint) for a path relative to writing/."""
    parts = rel.split("/")
    name = parts[-1]
    st = stem(name)
    if not name.lower().endswith(".md"):
        return "config", "config", None, st
    if len(parts) == 1:
        if st.lower() == "trailers":
            return "trailers", "trailer-index", None, st
        if st in CANON_FILES:
            return "canon", ("index" if st == "README" else "canon"), None, st
        return "systems", "system", None, st
    top = parts[0]
    if top == "internal-communications":
        if len(parts) == 2:
            return "comms", "index", None, st
        sub = parts[1]
        cat = COMMS_CAT.get(sub, "comms")
        if sub == "design-team":
            m = re.match(r"^(\d+)", st)
            code = "D-%02d" % int(m.group(1)) if m else None
            return cat, "message", code, strip_lead(st[m.end():]) if m else st
        m = re.match(r"^([ABC])-(\d+)", st)
        if m:
            return cat, "message", "%s-%02d" % (m.group(1), int(m.group(2))), strip_lead(st[m.end():])
        return cat, "message", None, st
    cat = FOLDER_CAT.get(top, "systems")
    if top == "documents":
        m = re.match(r"^(2\.\d+)", st)
        if m:
            return cat, "document", "2.%02d" % int(m.group(1)[2:]), strip_lead(st[m.end():])
    if top == "characters":
        m = re.match(r"^(E-\d{5})", st)
        if m:
            return cat, "character", m.group(1), strip_lead(st[m.end():])
        if st.startswith("Narrative Arc"):
            return cat, "arc", None, st
        return cat, "character", None, st
    if top == "facility":
        m = re.match(r"^Levels? (\d+)(?:-(\d+))?", st)
        if m:
            lo = int(m.group(1))
            hi = int(m.group(2)) if m.group(2) else lo
            return cat, "level", "L%d" % lo if lo == hi else "L%d-%d" % (lo, hi), st
        return cat, "facility-note", None, st
    if top == "weapons":
        if len(parts) == 2:
            return cat, "index", None, st
        sub = parts[1]
        key = re.split(r"\s+[â€”â€“-]\s+", st)[0].strip()
        return cat, "weapon-" + sub, key, st
    if top == "scene-notes":
        return cat, "scene", None, st
    if top == "trailers":
        m = re.match(r"^Trailer (\d+)", st)
        return cat, "trailer", ("T%s" % m.group(1)) if m else None, st
    if top == "enemies":
        return cat, ("index" if st == "README" else "enemy"), None, st
    return cat, "note", None, st


# --------------------------------------------------------------------------
# Reference extraction
# --------------------------------------------------------------------------
DOC_PREFIXED = re.compile(
    r"(?:Documents?|Docs?\.?)\s+(2\.\d{1,2}(?:\s*(?:,|and|&|â€“|â€”|-|/|to)\s*(?:2\.)?\d{1,2}\b)*)"
)
DOC_BARE = re.compile(r"(?<![\w.])2\.(0[1-9]|[1-4]\d|50)(?=\s*[(â€”â€“:)\],;]|\s+[A-Z])")
MSG_RE = re.compile(r"(?<![\w-])([ABC])-(\d{2})(?![\w-])")
ECODE_RE = re.compile(r"(?<![\w-])E-(\d{5})(?!\w)")
LEVEL_RE = re.compile(r"\bLevels?\s+(\d{1,2})(?:\s*(-|â€“|â€”|to|and|&)\s*(\d{1,2}))?")
PATH_RE = re.compile(r"((?:[\w][\w .\-â€”â€“]*/)*[\w][\w .\-â€”â€“]*\.md)\b")

CONCEPTS = [
    ("PTKW", "org", r"\bPTKW\b", 0),
    ("The Board", "org", r"\bBoard\b", 0),
    ("SOLCRED", "economy", r"\bSOLCRED\b", 0),
    ("AIDEN", "mascot", r"\bAIDEN\b", 0),
    ("SOL", "mascot", r"\bSOL\b", 0),
    ("CLEO", "mascot", r"\bCLEO\b", 0),
    ("VELO", "mascot", r"\bVELO\b", 0),
    ("SONA", "mascot", r"\bSONA\b", 0),
    ("BRIK", "mascot", r"\bBRIK\b", 0),
    ("EIMU", "tech", r"\bEIMU\b", 0),
    ("CCN", "tech", r"\bCCN\b", 0),
    ("Broadcast Display System", "tech", r"\bBDS\b|Broadcast Display System", 0),
    ("BES", "tech", r"\bBES\b", 0),
    ("ARM-27", "tech", r"\bARM-27\b", 0),
    ("Badge", "tech", r"\bbadges?\b", re.I),
    ("Schedule D", "lore", r"Schedule D", 0),
    ("Omega-1 / Category Omega", "lore", r"Omega-1|Category Omega", 0),
    ("Labor Source", "lore", r"Labor Source", 0),
    ("Resistance Index", "lore", r"Resistance [Ii]ndex", 0),
    ("Compliance Index", "lore", r"Compliance [Ii]ndex", 0),
    ("EOD (Executioner of Despair)", "lore", r"\bEOD\b|Executioner of Despair|Envoy of Devotion", 0),
    ("Rania's note", "lore", r"Rania['â€™]s (?:last )?note", 0),
    ("Branch Director's speech", "lore", r"Director['â€™]s (?:speech|address)", 0),
    ("Level 0", "place", r"Level 0\b", 0),
    ("Stairwell B", "place", r"Stairwell B", 0),
    ("Maintenance Network", "place", r"Maintenance Network", 0),
]


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def short(line, n=150):
    line = re.sub(r"\s+", " ", line).strip()
    return line if len(line) <= n else line[: n - 1] + "â€¦"


def clean_name(s):
    return re.sub(r"\s+", " ", s.replace("*", "").replace("\ufffd", "")).strip(" -â€”â€“:")


CODENAME_RE = re.compile(r"\b(K-\d+|VAH-?3|TOR-?9|ICS-OP-?7)\b")


def parse_party(raw):
    """Turn a From/To header value into (E-code or None, short display name)."""
    raw = raw.strip().strip("*").strip()
    m = ECODE_RE.search(raw)
    code = "E-" + m.group(1) if m else None
    rest = (raw[: m.start()] + raw[m.end():]) if m else raw
    if code:
        rest = clean_name(re.sub(r"[()\[\]]", " ", re.split(r"\s+[â€”â€“]\s+|[,;]", rest.strip(" ()"), maxsplit=1)[0]))
        return code, rest.strip(" ()") or code
    if raw.startswith("["):
        return None, "(unaddressed / device)"
    if "Brant" in raw:
        return None, "Brant"
    if re.search(r"Branch Director|Maren Voss", raw) and "Previous" not in raw:
        return None, "Branch Director"
    cn = CODENAME_RE.search(raw)
    if cn:
        n = cn.group(1)
        return None, n.replace("VAH3", "VAH-3").replace("TOR9", "TOR-9").replace("ICS-OP7", "ICS-OP-7")
    name = re.split(r"\s+[â€”â€“]\s+|[,;(]", raw, maxsplit=1)[0]
    return None, clean_name(name) or raw


# --------------------------------------------------------------------------
# Database schema
# --------------------------------------------------------------------------
PERSISTENT_SQL = """
CREATE TABLE IF NOT EXISTS scans (
  id         INTEGER PRIMARY KEY,
  ts         TEXT NOT NULL,
  git_commit TEXT,
  file_count INTEGER NOT NULL,
  added      INTEGER NOT NULL DEFAULT 0,
  modified   INTEGER NOT NULL DEFAULT 0,
  deleted    INTEGER NOT NULL DEFAULT 0,
  moved      INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS files (
  id         INTEGER PRIMARY KEY,
  path       TEXT NOT NULL UNIQUE,
  name       TEXT NOT NULL,
  folder     TEXT NOT NULL,
  cat        TEXT NOT NULL,
  kind       TEXT NOT NULL,
  code       TEXT,
  title      TEXT,
  bytes      INTEGER,
  lines      INTEGER,
  words      INTEGER,
  sha256     TEXT,
  first_scan INTEGER REFERENCES scans(id),
  last_scan  INTEGER REFERENCES scans(id),
  status     TEXT NOT NULL DEFAULT 'present'
);
CREATE TABLE IF NOT EXISTS snapshots (
  scan_id INTEGER NOT NULL REFERENCES scans(id),
  path    TEXT NOT NULL,
  sha256  TEXT,
  bytes   INTEGER,
  words   INTEGER,
  PRIMARY KEY (scan_id, path)
);
CREATE TABLE IF NOT EXISTS changes (
  scan_id  INTEGER NOT NULL REFERENCES scans(id),
  path     TEXT NOT NULL,
  change   TEXT NOT NULL,
  old_path TEXT,
  PRIMARY KEY (scan_id, path, change)
);
CREATE TABLE IF NOT EXISTS blobs (
  sha256  TEXT PRIMARY KEY,
  content BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS ref_changes (
  scan_id  INTEGER NOT NULL REFERENCES scans(id),
  src_path TEXT NOT NULL,
  dst_path TEXT NOT NULL,
  ref_type TEXT NOT NULL,
  change   TEXT NOT NULL,
  PRIMARY KEY (scan_id, src_path, dst_path, ref_type)
);
CREATE TABLE IF NOT EXISTS scan_metrics (
  scan_id INTEGER NOT NULL REFERENCES scans(id),
  metric  TEXT NOT NULL,
  value   REAL NOT NULL,
  PRIMARY KEY (scan_id, metric)
);
"""

DERIVED_TABLES = [
    "rel_edges", "rel_nodes", "lore_terms", "name_issues", "level_mentions", "phase_mentions",
    "msg_dates", "canon_checks", "canon_rules",
    "concept_mentions", "concepts", "unresolved", "refs", "weapons", "levels",
    "messages", "characters", "documents", "people",
    "facts", "fact_conflicts",
]

DERIVED_SQL = """
CREATE TABLE people (
  id          INTEGER PRIMARY KEY,
  code        TEXT UNIQUE,
  name        TEXT NOT NULL,
  has_profile INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE documents (
  file_id INTEGER PRIMARY KEY REFERENCES files(id),
  doc_no  TEXT NOT NULL UNIQUE,
  title   TEXT
);
CREATE TABLE characters (
  file_id   INTEGER PRIMARY KEY REFERENCES files(id),
  code      TEXT,
  name      TEXT NOT NULL,
  blurb     TEXT,
  person_id INTEGER REFERENCES people(id)
);
CREATE TABLE messages (
  file_id     INTEGER PRIMARY KEY REFERENCES files(id),
  series      TEXT NOT NULL,
  number      INTEGER,
  code        TEXT,
  subject     TEXT,
  sent_at     TEXT,
  from_person INTEGER REFERENCES people(id),
  to_person   INTEGER REFERENCES people(id),
  from_raw    TEXT,
  to_raw      TEXT
);
CREATE TABLE levels (
  file_id    INTEGER PRIMARY KEY REFERENCES files(id),
  level_from INTEGER NOT NULL,
  level_to   INTEGER NOT NULL
);
CREATE TABLE weapons (
  file_id     INTEGER PRIMARY KEY REFERENCES files(id),
  class       TEXT NOT NULL,
  designation TEXT NOT NULL
);
CREATE TABLE refs (
  src_file INTEGER NOT NULL REFERENCES files(id),
  dst_file INTEGER NOT NULL REFERENCES files(id),
  ref_type TEXT NOT NULL,
  count    INTEGER NOT NULL,
  sample   TEXT,
  PRIMARY KEY (src_file, dst_file, ref_type)
);
CREATE TABLE unresolved (
  src_file INTEGER NOT NULL REFERENCES files(id),
  token    TEXT NOT NULL,
  ref_type TEXT NOT NULL,
  count    INTEGER NOT NULL,
  severity TEXT NOT NULL,
  PRIMARY KEY (src_file, token, ref_type)
);
CREATE TABLE concepts (
  id       INTEGER PRIMARY KEY,
  name     TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL
);
CREATE TABLE concept_mentions (
  file_id    INTEGER NOT NULL REFERENCES files(id),
  concept_id INTEGER NOT NULL REFERENCES concepts(id),
  count      INTEGER NOT NULL,
  PRIMARY KEY (file_id, concept_id)
);
CREATE TABLE canon_rules (
  id      TEXT PRIMARY KEY,
  label   TEXT NOT NULL,
  pattern TEXT NOT NULL,
  allowed TEXT NOT NULL
);
CREATE TABLE canon_checks (
  rule_id TEXT NOT NULL REFERENCES canon_rules(id),
  file_id INTEGER NOT NULL REFERENCES files(id),
  line_no INTEGER NOT NULL,
  value   TEXT NOT NULL,
  status  TEXT NOT NULL,
  text    TEXT
);
CREATE TABLE msg_dates (
  file_id INTEGER PRIMARY KEY REFERENCES files(id),
  cycle   INTEGER NOT NULL,
  quarter INTEGER,
  day     INTEGER,
  clock   TEXT,
  raw     TEXT,
  source  TEXT
);
CREATE TABLE phase_mentions (
  file_id INTEGER NOT NULL REFERENCES files(id),
  phase   INTEGER NOT NULL,
  count   INTEGER NOT NULL,
  PRIMARY KEY (file_id, phase)
);
CREATE TABLE level_mentions (
  level      INTEGER NOT NULL,
  cat        TEXT NOT NULL,
  file_count INTEGER NOT NULL,
  mentions   INTEGER NOT NULL,
  PRIMARY KEY (level, cat)
);
CREATE TABLE name_issues (
  kind     TEXT NOT NULL,
  severity TEXT NOT NULL,
  subject  TEXT NOT NULL,
  detail   TEXT NOT NULL
);
CREATE TABLE lore_terms (
  term       TEXT PRIMARY KEY,
  files      INTEGER NOT NULL,
  uses       INTEGER NOT NULL,
  defined    INTEGER NOT NULL,
  first_file TEXT
);
CREATE TABLE rel_nodes (
  name     TEXT PRIMARY KEY,
  codes    TEXT,
  profile  INTEGER NOT NULL,
  sent     INTEGER NOT NULL,
  received INTEGER NOT NULL,
  files    INTEGER NOT NULL
);
CREATE TABLE rel_edges (
  a        TEXT NOT NULL REFERENCES rel_nodes(name),
  b        TEXT NOT NULL REFERENCES rel_nodes(name),
  messages INTEGER NOT NULL,
  co_files INTEGER NOT NULL,
  co_paras INTEGER NOT NULL,
  PRIMARY KEY (a, b)
);
CREATE TABLE facts (
  id        INTEGER PRIMARY KEY,
  subject   TEXT NOT NULL,
  predicate TEXT NOT NULL,
  value     TEXT NOT NULL,
  path      TEXT NOT NULL,
  line_no   INTEGER NOT NULL,
  raw       TEXT
);
CREATE TABLE fact_conflicts (
  id        INTEGER PRIMARY KEY,
  subject   TEXT NOT NULL,
  predicate TEXT NOT NULL,
  n_values  INTEGER NOT NULL,
  summary   TEXT NOT NULL
);
CREATE VIEW IF NOT EXISTS v_fact_conflicts AS
  SELECT subject, predicate, n_values, summary FROM fact_conflicts ORDER BY n_values DESC, subject, predicate;
CREATE VIEW IF NOT EXISTS v_canon_violations AS
  SELECT r.label, f.path, c.line_no, c.value, c.text
  FROM canon_checks c JOIN canon_rules r ON r.id = c.rule_id JOIN files f ON f.id = c.file_id
  WHERE c.status = 'violation' ORDER BY r.id, f.path;
CREATE VIEW IF NOT EXISTS v_message_timeline AS
  SELECT d.cycle, d.quarter, d.day, d.clock, m.code, m.subject
  FROM msg_dates d JOIN messages m ON m.file_id = d.file_id
  ORDER BY d.cycle, d.quarter, d.day, d.clock;
CREATE VIEW IF NOT EXISTS v_most_referenced AS
  SELECT f.path, f.title, COUNT(DISTINCT r.src_file) AS referenced_by, SUM(r.count) AS total_mentions
  FROM refs r JOIN files f ON f.id = r.dst_file
  GROUP BY f.id ORDER BY referenced_by DESC;
CREATE VIEW IF NOT EXISTS v_orphans AS
  SELECT f.path FROM files f
  WHERE f.status = 'present' AND f.kind NOT IN ('config')
    AND NOT EXISTS (SELECT 1 FROM refs r WHERE r.dst_file = f.id);
CREATE VIEW IF NOT EXISTS v_who_writes_to_whom AS
  SELECT pf.name AS sender, pt.name AS recipient, COUNT(*) AS messages
  FROM messages m
  LEFT JOIN people pf ON pf.id = m.from_person
  LEFT JOIN people pt ON pt.id = m.to_person
  GROUP BY m.from_person, m.to_person ORDER BY messages DESC;
"""

TABLE_DESC = {
    "scans": "One row per time the writing changed. History survives re-runs.",
    "files": "Every file under writing/ (stable ids). Deleted files stay with status='deleted'.",
    "snapshots": "sha256 of every file at each scan, used to diff scans.",
    "changes": "Added / modified / deleted / moved files per scan.",
    "people": "Anyone who appears as an E-code or a named sender/recipient.",
    "documents": "In-world documents 2.01 - 2.51.",
    "characters": "Character profile files (plus Branch Director, EOD, ...).",
    "messages": "Internal comms A / B / C / D series with parsed From / To.",
    "levels": "Facility level files (Level N.md, Levels a-b.md).",
    "weapons": "Weapon files, grouped by class folder.",
    "refs": "File -> file references (the graph). One row per (source, target, type).",
    "unresolved": "References that point at nothing (broken) or at people with no profile.",
    "concepts": "Recurring lore terms tracked across files (PTKW, SOLCRED, EIMU, ...).",
    "concept_mentions": "How often each concept appears in each file.",
    "blobs": "Compressed content of every distinct file version ever scanned (powers diffs and restore).",
    "ref_changes": "Links gained / lost in each scan.",
    "scan_metrics": "Health numbers per scan (words, broken refs, canon violations, ...) for trend lines.",
    "canon_rules": "Rules from canon_rules.json.",
    "canon_checks": "Every place a rule found a value, with ok / accepted / violation.",
    "msg_dates": "In-world dates (Cycle / Quarter / Day) parsed from message headers.",
    "phase_mentions": "How often each file talks about Phase 0-6.",
    "level_mentions": "How often each facility level is cited, by file category.",
    "name_issues": "E-code / name / spelling inconsistencies.",
    "lore_terms": "Acronyms and codes, and whether the glossary defines them.",
    "rel_nodes": "Characters and groups in the relationship graph.",
    "rel_edges": "Links between them: messages exchanged + co-mentions.",
}

ERD_LAYOUT = {
    "scans": [20, 20], "snapshots": [20, 210], "changes": [20, 370], "blobs": [20, 520],
    "ref_changes": [20, 620], "scan_metrics": [20, 790],
    "files": [330, 20], "refs": [330, 420], "unresolved": [330, 590],
    "concept_mentions": [330, 760], "concepts": [330, 900],
    "canon_checks": [330, 1010], "canon_rules": [330, 1190],
    "documents": [640, 20], "messages": [640, 140], "msg_dates": [640, 400],
    "characters": [640, 530], "levels": [640, 700], "weapons": [640, 820],
    "phase_mentions": [640, 940], "level_mentions": [640, 1050],
    "people": [950, 140],
    "rel_nodes": [950, 330], "rel_edges": [950, 500],
    "name_issues": [950, 680], "lore_terms": [950, 810],
}


def git_commit():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip() or None
    except Exception:
        return None


# --------------------------------------------------------------------------
# Main build
# --------------------------------------------------------------------------
def scan_disk():
    found = {}
    for p in sorted(WRITING.rglob("*.md")):
        if not p.is_file():
            continue
        rel = p.relative_to(WRITING)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        real = rel.as_posix()
        if real == "README.md":
            rel_s = real
        else:
            rel_s = next((new + real[len(old):] for old, new in LAYOUT if real.startswith(old)), None)
            if rel_s is None:
                continue
        REAL[rel_s] = real
        data = p.read_bytes()
        info = {"sha": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        if rel_s.lower().endswith(".md"):
            text = data.decode("utf-8", errors="replace")
            info["raw"] = data
            info["text"] = text
            info["lines"] = text.count("\n") + 1
            info["words"] = len(re.findall(r"\w+", text))
        else:
            info["text"], info["lines"], info["words"] = "", 0, 0
        found[rel_s] = info
    return found


def log(*a):
    if not QUIET:
        print(*a)


def main():
    if not WRITING.is_dir():
        sys.exit("Writing repo not found at %s (set ICS_WRITING)" % WRITING)
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    disk = scan_disk()

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys=OFF")
    con.executescript(PERSISTENT_SQL)
    # links as of the previous build, so a new scan can record which ones were gained / lost
    prev_refs = set()
    try:
        prev_refs = {
            (s, d, t) for s, d, t in con.execute(
                "SELECT s.path, d.path, r.ref_type FROM refs r JOIN files s ON s.id=r.src_file JOIN files d ON d.id=r.dst_file")
        }
    except sqlite3.Error:
        pass
    for t in DERIVED_TABLES:
        con.execute("DROP TABLE IF EXISTS " + t)
    for v in ("v_most_referenced", "v_orphans", "v_who_writes_to_whom", "v_canon_violations", "v_message_timeline"):
        con.execute("DROP VIEW IF EXISTS " + v)

    # ---------------- scan diff / history ----------------
    last = con.execute("SELECT max(id) FROM scans").fetchone()[0]
    prev = {}
    if last:
        prev = {r[0]: r[1] for r in con.execute("SELECT path, sha256 FROM snapshots WHERE scan_id=?", (last,))}
    cur = {p: i["sha"] for p, i in disk.items()}
    added = [p for p in cur if p not in prev]
    deleted = [p for p in prev if p not in cur]
    modified = [p for p in cur if p in prev and prev[p] != cur[p]]
    moved = []
    del_by_sha = defaultdict(list)
    for p in deleted:
        del_by_sha[prev[p]].append(p)
    for p in list(added):
        olds = del_by_sha.get(cur[p])
        if olds:
            moved.append((p, olds.pop(0)))
            added.remove(p)
    moved_old = {o for _, o in moved}
    deleted = [p for p in deleted if p not in moved_old]

    changed = bool(added or deleted or modified or moved) or not last
    if changed:
        cur_id = con.execute(
            "INSERT INTO scans(ts, git_commit, file_count, added, modified, deleted, moved) VALUES (?,?,?,?,?,?,?)",
            (now, git_commit(), len(cur), len(added), len(modified), len(deleted), len(moved)),
        ).lastrowid
        con.executemany(
            "INSERT INTO snapshots VALUES (?,?,?,?,?)",
            [(cur_id, p, i["sha"], i["bytes"], i["words"]) for p, i in disk.items()],
        )
        rows = [(cur_id, p, "added", None) for p in added]
        rows += [(cur_id, p, "modified", None) for p in modified]
        rows += [(cur_id, p, "deleted", None) for p in deleted]
        rows += [(cur_id, p, "moved", o) for p, o in moved]
        con.executemany("INSERT INTO changes VALUES (?,?,?,?)", rows)
    else:
        cur_id = last

    # keep a compressed copy of every distinct file version (powers History diffs / restore)
    have = {r[0] for r in con.execute("SELECT sha256 FROM blobs")}
    for p, info in disk.items():
        if "raw" in info and info["sha"] not in have:
            con.execute("INSERT INTO blobs VALUES (?,?)", (info["sha"], analysis.pack(info["raw"])))
            have.add(info["sha"])

    # ---------------- files table (stable ids) ----------------
    meta = {}
    for p, info in disk.items():
        cat, kind, code, title = classify(p)
        meta[p] = (cat, kind, code, title)
        folder = p.rsplit("/", 1)[0] if "/" in p else "(root)"
        row = con.execute("SELECT id FROM files WHERE path=?", (p,)).fetchone()
        vals = (p.rsplit("/", 1)[-1], folder, cat, kind, code, title, info["bytes"], info["lines"], info["words"], info["sha"])
        if row:
            con.execute(
                "UPDATE files SET name=?, folder=?, cat=?, kind=?, code=?, title=?, bytes=?, lines=?, words=?, sha256=?, "
                "last_scan=?, status='present' WHERE id=?",
                vals + (cur_id, row[0]),
            )
        else:
            con.execute(
                "INSERT INTO files(path,name,folder,cat,kind,code,title,bytes,lines,words,sha256,first_scan,last_scan,status) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'present')",
                (p,) + vals + (cur_id, cur_id),
            )
    con.execute(
        "UPDATE files SET status='deleted' WHERE path NOT IN (%s)" % ",".join("?" * len(disk)), list(disk)
    )
    con.commit()

    ids = {r[0]: r[1] for r in con.execute("SELECT path, id FROM files WHERE status='present'")}
    paths = {v: k for k, v in ids.items()}

    # ---------------- typed tables ----------------
    con.executescript(DERIVED_SQL)
    con.execute("PRAGMA foreign_keys=ON")

    doc_by_no, msg_by_code, char_by_code, level_by_n = {}, {}, {}, {}
    weapon_keys = []  # (id, key)
    char_alias = []   # (id, regex)
    people = {}       # key -> dict(code,name)
    alias_to_code = {}

    def first_nonempty_after_heading(text):
        seen_h = False
        for ln in text.splitlines():
            s = ln.strip()
            if not s:
                continue
            if s.startswith("#"):
                seen_h = True
                continue
            if seen_h:
                return clean_name(s.strip("*_ "))
        return ""

    for p, info in disk.items():
        fid = ids[p]
        cat, kind, code, title = meta[p]
        text = info["text"]
        if kind == "document" and code:
            doc_by_no[code] = fid
            con.execute("INSERT INTO documents VALUES (?,?,?)", (fid, code, title))
        elif kind == "message":
            msg_by_code[code] = fid if code else None
        elif kind == "character":
            m = re.match(r"^(.*?)(?:\s*\((.*)\))?$", title)
            base = clean_name(m.group(1)) if m else title
            if code:
                char_by_code[code] = fid
            aliases = {base}
            if base.startswith("The "):
                aliases.add(base[4:])
            if " " in base and code:
                aliases.add(base.split()[0])
            if base == "Previous Branch Director":
                aliases = {base}
            if base == "Branch Director":
                aliases = {"Branch Director"}
            for a in aliases:
                alias_to_code[a.lower()] = code or ("name:" + base.lower())
            key = code or ("name:" + base.lower())
            people[key] = {"code": code, "name": base, "profile": True}
            char_alias.append((fid, base, aliases))
        elif kind == "level":
            m = re.match(r"^L(\d+)(?:-(\d+))?", code)
            lo = int(m.group(1)); hi = int(m.group(2) or lo)
            for n in range(lo, hi + 1):
                level_by_n[n] = fid
            con.execute("INSERT INTO levels VALUES (?,?,?)", (fid, lo, hi))
        elif kind.startswith("weapon-"):
            weapon_keys.append((fid, code))
            con.execute("INSERT INTO weapons VALUES (?,?,?)", (fid, kind.split("-", 1)[1], code))

    # characters + people rows will be written after messages are parsed (need person ids)
    msg_rows = []
    for p, info in disk.items():
        cat, kind, code, title = meta[p]
        if kind != "message":
            continue
        text = info["text"]
        def hdr(name):
            m = re.search(r"^\*\*%s:\*\*\s*(.+)$" % name, text, re.M)
            return m.group(1).strip() if m else None
        f_raw, t_raw, subj, ts = hdr("From"), hdr("To"), hdr("Subject"), hdr("Timestamp")
        keys = []
        for raw in (f_raw, t_raw):
            if not raw:
                keys.append(None)
                continue
            c, name = parse_party(raw)
            if not c and name.lower() in alias_to_code:
                c = alias_to_code[name.lower()]
                c = c if re.match(r"^E-\d{5}$", c) else None
            key = c or ("name:" + name.lower())
            if key in alias_to_code.values() and not c:
                pass
            rec = people.setdefault(key, {"code": c, "name": name or key, "profile": False})
            if len(name) > len(rec["name"]) and not rec["profile"]:
                rec["name"] = name
            keys.append(key)
        series = code[0] if code else "?"
        num = int(code[2:]) if code else None
        msg_rows.append((ids[p], series, num, code, subj or title, ts, keys[0], keys[1], f_raw, t_raw))

    person_id = {}
    for key, rec in sorted(people.items(), key=lambda kv: (kv[1]["code"] or "~", kv[1]["name"])):
        cur_ = con.execute(
            "INSERT INTO people(code,name,has_profile) VALUES (?,?,?)",
            (rec["code"], rec["name"], 1 if (rec["profile"] and rec["code"]) else 0),
        )
        person_id[key] = cur_.lastrowid
    con.executemany(
        "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?)",
        [(f, s, n, c, sj, ts, person_id.get(fk), person_id.get(tk), fr, tr)
         for f, s, n, c, sj, ts, fk, tk, fr, tr in msg_rows],
    )
    for fid, base, _ in char_alias:
        p = paths[fid]
        cat, kind, code, title = meta[p]
        key = code or ("name:" + base.lower())
        con.execute(
            "INSERT INTO characters VALUES (?,?,?,?,?)",
            (fid, code, base, first_nonempty_after_heading(disk[p]["text"])[:240], person_id.get(key)),
        )
    # fix profile flags only for coded people with a profile
    con.execute("UPDATE people SET has_profile = 1 WHERE code IN (SELECT code FROM characters WHERE code IS NOT NULL)")

    # ---------------- reference extraction ----------------
    suffix_index = defaultdict(set)
    for p, fid in ids.items():
        for q in {p, REAL.get(p, p)}:   # old layout and real repo path both resolve
            segs = q.lower().split("/")
            for i in range(len(segs)):
                suffix_index["/".join(segs[i:])].add(fid)

    weapon_res = []
    for fid, key in weapon_keys:
        pat = re.escape(key).replace(r"\-", r"[\s-]").replace(r"\ ", r"[\s-]")
        weapon_res.append((fid, re.compile(r"(?<![\w-])%s(?![\w-])" % pat, 0 if re.search(r"\d", key) else re.I)))
    char_res = []
    for fid, base, aliases in char_alias:
        names = sorted(aliases, key=len, reverse=True)
        body = "|".join(re.escape(a) for a in names)
        if base == "Branch Director":
            body = r"(?<!Previous )Branch Director"
        char_res.append((fid, re.compile(r"(?<![\w-])(?:%s)(?![\w'â€™-])" % body)))
    concept_res = [(n, c, re.compile(pt, fl)) for n, c, pt, fl in CONCEPTS]
    con.executemany("INSERT INTO concepts(name,category) VALUES (?,?)", [(n, c) for n, c, _, _ in CONCEPTS])
    concept_id = {r[1]: r[0] for r in con.execute("SELECT id, name FROM concepts")}

    refs = {}          # (src,dst,type) -> [count, sample]
    unresolved = {}    # (src,token,type) -> [count, sev]
    cm_rows = []

    def add(src, dst, typ, sample, n=1):
        if src == dst or dst is None:
            return
        e = refs.setdefault((src, dst, typ), [0, sample])
        e[0] += n

    def unres(src, token, typ, sev):
        e = unresolved.setdefault((src, token, typ), [0, sev])
        e[0] += 1

    def resolve_path(cand, src_path):
        words = cand.strip().split(" ")
        for i in range(len(words)):
            tok = " ".join(words[i:]).strip("`").lower()
            if not tok:
                continue
            hit = suffix_index.get(tok)
            if hit:
                if len(hit) == 1:
                    return next(iter(hit)), None
                # ambiguous: prefer same folder as source
                src_dir = src_path.rsplit("/", 1)[0] if "/" in src_path else ""
                for h in hit:
                    hp = paths[h]
                    if (hp.rsplit("/", 1)[0] if "/" in hp else "") == src_dir:
                        return h, None
                return None, "ambiguous"
        # unresolved: report from first word containing '/' else trailing words
        for i, w in enumerate(words):
            if "/" in w:
                return None, " ".join(words[i:]).strip("`")
        return None, " ".join(words[-3:]).strip("`")

    for p, info in disk.items():
        if not info["text"]:
            continue
        src = ids[p]
        text = info["text"]
        cat, kind, code, title = meta[p]
        # concepts (whole-text counts)
        for name, _, rx in concept_res:
            n = len(rx.findall(text))
            if n:
                cm_rows.append((src, concept_id[name], n))
        # character name mentions (whole-text counts)
        for fid, rx in char_res:
            if fid == src:
                continue
            n = len(rx.findall(text))
            if n:
                e = refs.setdefault((src, fid, "mention"), [0, ""])
                e[0] += n
        # weapons (whole-text counts + first sample)
        for fid, rx in weapon_res:
            if fid == src:
                continue
            ms = list(rx.finditer(text))
            if ms:
                a = text.rfind("\n", 0, ms[0].start()) + 1
                b = text.find("\n", ms[0].end())
                e = refs.setdefault((src, fid, "weapon"), [0, short(text[a: b if b > 0 else None])])
                e[0] += len(ms)
        # line-based references
        for line in text.splitlines():
            if not line.strip():
                continue
            if "2." in line:
                seen = set()
                for m in DOC_PREFIXED.finditer(line):
                    nums = re.findall(r"(?:2\.)?(\d{1,2})\b", m.group(1))
                    first = re.match(r"2\.(\d{1,2})", m.group(1))
                    toks = ["2.%02d" % int(first.group(1))] if first else []
                    # remaining numbers after separators
                    rest = m.group(1)[first.end():] if first else ""
                    sep_re = re.finditer(r"(,|and|&|â€“|â€”|-|/|to)\s*(?:2\.)?(\d{1,2})\b", rest)
                    prev_n = int(first.group(1)) if first else None
                    for sm in sep_re:
                        n2 = int(sm.group(2))
                        if sm.group(1) in ("â€“", "â€”", "-", "to") and prev_n and 0 < n2 - prev_n < 8 and "2." in rest:
                            toks.extend("2.%02d" % k for k in range(prev_n + 1, n2 + 1))
                        else:
                            toks.append("2.%02d" % n2)
                        prev_n = n2
                    for t in toks:
                        seen.add((t, True))
                for m in DOC_BARE.finditer(line):
                    seen.add(("2.%s" % m.group(1), False))
                for t, strict in seen:
                    if t in doc_by_no:
                        add(src, doc_by_no[t], "document", short(line))
                    elif strict:
                        unres(src, "Document " + t, "document", "broken")
            if "-" in line:
                for m in MSG_RE.finditer(line):
                    c = "%s-%s" % (m.group(1), m.group(2))
                    if c in msg_by_code and msg_by_code[c]:
                        add(src, msg_by_code[c], "message", short(line))
                for m in ECODE_RE.finditer(line):
                    c = "E-" + m.group(1)
                    if c in char_by_code:
                        add(src, char_by_code[c], "character", short(line))
                    elif p != "" and meta[p][1] != "message":
                        unres(src, c + " (no profile file)", "character", "info")
            if "Level" in line:
                for m in LEVEL_RE.finditer(line):
                    a = int(m.group(1))
                    lv = [a]
                    if m.group(3):
                        b = int(m.group(3))
                        if m.group(2) in ("-", "â€“", "â€”", "to") and a < b <= 14:
                            lv = list(range(a, b + 1))
                        elif b <= 14:
                            lv = [a, b]
                    for n in lv:
                        if n in level_by_n:
                            add(src, level_by_n[n], "level", "")
            if ".md" in line:
                for m in PATH_RE.finditer(line):
                    cand = m.group(1)
                    if "http" in cand:
                        continue
                    dst, err = resolve_path(cand, p)
                    if dst:
                        add(src, dst, "path", short(line))
                    elif err and err != "ambiguous":
                        unres(src, err, "path", "broken")

    con.executemany(
        "INSERT INTO refs VALUES (?,?,?,?,?)",
        [(s, d, t, v[0], v[1] if t not in ("mention", "level") else "") for (s, d, t), v in refs.items()],
    )
    con.executemany(
        "INSERT INTO unresolved VALUES (?,?,?,?,?)",
        [(s, tk, t, v[0], v[1]) for (s, tk, t), v in unresolved.items()],
    )
    con.executemany("INSERT INTO concept_mentions VALUES (?,?,?)", cm_rows)
    con.commit()

    extra = run_analysis(con, disk, ids, paths, meta, doc_by_no, level_by_n, refs, prev_refs,
                         cur_id, changed and bool(last))
    export_html(con, now, cur_id, extra)
    try:  # ICS-OS (build_os.py, one folder up): Hearth, ICS Cloud Drive and Folio; never block the map build
        sys.path.insert(0, str(OS_ROOT))
        import build_os
        build_os.build(now)
        log("ics-os -> ", build_os.OUT_PATH)
    except Exception as e:  # noqa: BLE001
        print("WARNING: ICS-OS not rebuilt:", e)
    summarize(con, changed, added, modified, deleted, moved)
    con.close()


def run_analysis(con, disk, ids, paths, meta, doc_by_no, level_by_n, refs, prev_refs, cur_id, record_ref_changes):
    """Second-stage passes (canon, timeline, coverage, names, terms, relationships, exports)."""
    corpus = []
    for p, info in disk.items():
        if info["text"]:
            cat_, kind_, code_, title_ = meta[p]
            corpus.append({"id": ids[p], "p": p, "cat": cat_, "kind": kind_, "code": code_, "title": title_, "text": info["text"]})
    cfg = json.loads(CANON_PATH.read_text(encoding="utf-8"))
    ins = lambda sql, rows: con.executemany(sql, rows)

    # canon rules
    canon, rule_rows, check_rows = analysis.canon_check(corpus, cfg, len(doc_by_no))
    ins("INSERT INTO canon_rules VALUES (?,?,?,?)", rule_rows)
    ins("INSERT INTO canon_checks VALUES (?,?,?,?,?,?)", check_rows)

    # message dates + timeline
    dates = {f["id"]: analysis.parse_msg_date(f["text"]) for f in corpus if f["kind"] == "message"}
    dates = {k: v for k, v in dates.items() if v}
    ins("INSERT INTO msg_dates VALUES (?,?,?,?,?,?,?)",
        [(k, d["cycle"], d["q"] or None, d["day"], d["clock"], d["raw"], d["src"]) for k, d in dates.items()])
    msg_list = [{"f": r[0], "code": r[1], "series": r[2]} for r in con.execute("SELECT file_id, code, series FROM messages")]
    tl = analysis.timeline(corpus, msg_list, dates)

    # phase + level coverage
    ph_rows = analysis.phase_counts(corpus)
    ins("INSERT INTO phase_mentions VALUES (?,?,?)", ph_rows)
    level_files = {n: (fid, paths[fid], disk[paths[fid]]["words"]) for n, fid in level_by_n.items()}
    lv_out, lv_rows = analysis.level_stats(corpus, level_files, LEVEL_RE)
    ins("INSERT INTO level_mentions VALUES (?,?,?,?)", lv_rows)

    # names, terms
    issues = analysis.name_issues(corpus, cfg.get("accepted_names", []))
    ins("INSERT INTO name_issues VALUES (?,?,?,?)", [(i["kind"], i["sev"], i["subject"], i["detail"]) for i in issues])
    for i in issues:
        i["ids"] = [ids[p] for p in i.pop("paths") if p in ids]
    terms = analysis.lore_terms(corpus)
    ins("INSERT INTO lore_terms VALUES (?,?,?,?,?)", [(t["term"], t["files"], t["uses"], int(t["defined"]), t["first"]) for t in terms])
    for t in terms:
        t["first"] = ids.get(t["first"])

    # relationships
    people_rows = con.execute("SELECT id, code, name, has_profile FROM people").fetchall()
    msg_rows = con.execute("SELECT file_id, from_person, to_person FROM messages").fetchall()
    prof = {r[0] for r in con.execute("SELECT name FROM characters")}
    prof |= {n[4:] for n in prof if n.startswith("The ")}
    rel_view, node_rows, edge_rows = analysis.relationships(corpus, people_rows, msg_rows, prof)
    ins("INSERT INTO rel_nodes VALUES (?,?,?,?,?,?)", node_rows)
    ins("INSERT INTO rel_edges VALUES (?,?,?,?,?)", edge_rows)

    # fact extraction â€” cross-file claim consistency
    raw_facts, raw_conflicts = analysis.fact_extract(corpus)
    ins("INSERT INTO facts (subject,predicate,value,path,line_no,raw) VALUES (?,?,?,?,?,?)",
        [(f["subject"], f["predicate"], f["value"], f["path"], f["line_no"], f["raw"]) for f in raw_facts])
    ins("INSERT INTO fact_conflicts (subject,predicate,n_values,summary) VALUES (?,?,?,?)",
        [(c["subject"], c["predicate"], len({e["value"] for e in c["entries"]}),
          " | ".join("%s (%s:%d)" % (e["value"], e["path"].split("/")[-1], e["line_no"])
                     for e in c["entries"][:8])) for c in raw_conflicts])
    con.commit()

    # links gained / lost since the previous scan
    cur_refs = {(paths[s], paths[d], t) for (s, d, t) in refs if t in EXPLICIT}
    old_refs = {r for r in prev_refs if r[2] in EXPLICIT}
    if record_ref_changes:
        rc = [(cur_id, s, d, t, "added") for s, d, t in sorted(cur_refs - old_refs)]
        rc += [(cur_id, s, d, t, "removed") for s, d, t in sorted(old_refs - cur_refs)]
        con.executemany("INSERT OR REPLACE INTO ref_changes VALUES (?,?,?,?,?)", rc)

    # trend metrics (latest build overwrites its own scan's numbers)
    n = lambda sql: con.execute(sql).fetchone()[0]
    metrics = {
        "files": len(disk),
        "words": sum(i["words"] for i in disk.values()),
        "links": n("SELECT count(*) FROM refs WHERE ref_type IN ('document','message','character','path','weapon')"),
        "broken_refs": n("SELECT count(*) FROM unresolved WHERE severity='broken'"),
        "orphans": n("SELECT count(*) FROM v_orphans"),
        "canon_violations": sum(r["n_flagged"] for r in canon),
        "name_issues": len(issues),
        "undated_messages": len(tl["undated"]),
    }
    con.executemany("INSERT OR REPLACE INTO scan_metrics VALUES (?,?,?)", [(cur_id, k, v) for k, v in metrics.items()])
    con.commit()

    # exports
    file_cat = {ids[p]: meta[p][0] for p in ids if p in meta}
    flow = defaultdict(set)
    for (s, d, t) in refs:
        if t in EXPLICIT and file_cat.get(s) != file_cat.get(d):
            flow[(file_cat[s], file_cat[d])].add((s, d))
    cat_flow = sorted(((a, b, len(v)) for (a, b), v in flow.items() if len(v) >= 5), key=lambda x: -x[2])
    doc_no = {fid: no for no, fid in doc_by_no.items()}
    doc_edges = sorted({(doc_no[s], doc_no[d]) for (s, d, t) in refs if t == "document" and s in doc_no and d in doc_no})
    schema = schema_json(con)
    exports = analysis.build_exports(schema, {k: {"label": v[0]} for k, v in CATS.items()}, cat_flow, rel_view, doc_edges)

    return {
        "canon": canon,
        "timeline": tl,
        "phases": [list(r) for r in ph_rows],
        "levels_cov": lv_out,
        "name_issues": issues,
        "terms": terms[:400],
        "rel": rel_view,
        "exports": exports,
        "metrics": [list(r) for r in con.execute("SELECT scan_id, metric, value FROM scan_metrics ORDER BY scan_id")],
        "ref_changes": [list(r) for r in con.execute(
            "SELECT scan_id, src_path, dst_path, ref_type, change FROM ref_changes ORDER BY scan_id DESC LIMIT 1500")],
        "diffs": history_diffs(con),
        "schema": schema,
        "facts": raw_facts,
        "fact_conflicts": raw_conflicts,
    }


def history_diffs(con, max_scans=15, cap_total=400):
    out = {}
    for (sid,) in con.execute("SELECT id FROM scans ORDER BY id DESC LIMIT ?", (max_scans,)).fetchall():
        prev = con.execute("SELECT max(id) FROM scans WHERE id < ?", (sid,)).fetchone()[0]
        if not prev:
            continue
        for (path,) in con.execute("SELECT path FROM changes WHERE scan_id=? AND change='modified'", (sid,)).fetchall():
            if len(out) >= cap_total:
                return out
            a = con.execute("SELECT sha256 FROM snapshots WHERE scan_id=? AND path=?", (prev, path)).fetchone()
            b = con.execute("SELECT sha256 FROM snapshots WHERE scan_id=? AND path=?", (sid, path)).fetchone()
            if not a or not b:
                continue
            ba = con.execute("SELECT content FROM blobs WHERE sha256=?", (a[0],)).fetchone()
            bb = con.execute("SELECT content FROM blobs WHERE sha256=?", (b[0],)).fetchone()
            if ba and bb:
                old = analysis.unpack(ba[0]).decode("utf-8", errors="replace")
                new = analysis.unpack(bb[0]).decode("utf-8", errors="replace")
                out["%d|%s" % (sid, path)] = analysis.unified(old, new, path.rsplit("/", 1)[-1])
    return out


def cat_version(scan_id, path):
    """Print the stored text of `path` as it was in scan `scan_id`."""
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT b.content FROM snapshots s JOIN blobs b ON b.sha256 = s.sha256 WHERE s.scan_id=? AND s.path=?",
        (scan_id, path)).fetchone()
    if not row:
        sys.exit("No stored copy of %s in scan %s (blobs are kept from the first run of this version onward)." % (path, scan_id))
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(analysis.unpack(row[0]).decode("utf-8", errors="replace"))


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------
def schema_json(con):
    out = []
    for (name,) in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ):
        fks = {r[3]: "%s.%s" % (r[2], r[4] or "id") for r in con.execute("PRAGMA foreign_key_list(%s)" % name)}
        cols = [
            {"n": r[1], "t": r[2] or "", "pk": bool(r[5]), "fk": fks.get(r[1]), "nn": bool(r[3])}
            for r in con.execute("PRAGMA table_info(%s)" % name)
        ]
        rows = con.execute("SELECT count(*) FROM %s" % name).fetchone()[0]
        out.append({"name": name, "desc": TABLE_DESC.get(name, ""), "rows": rows, "cols": cols})
    return out


def export_html(con, now, scan_id, extra):
    q = lambda sql, *a: con.execute(sql, a).fetchall()
    files = q("SELECT id,path,name,cat,kind,code,title,bytes,words,lines FROM files WHERE status='present' ORDER BY path")
    data = {
        "meta": {
            "generated": now,
            "scan_id": scan_id,
            "commit": q("SELECT git_commit FROM scans WHERE id=?", scan_id)[0][0],
            "writing_root": WRITING.as_posix(),
        },
        "cats": {k: {"label": v[0], "color": v[1]} for k, v in CATS.items()},
        "files": [
            {"id": r[0], "p": r[1], "r": REAL.get(r[1], r[1]), "n": r[2], "cat": r[3], "k": r[4], "c": r[5], "t": r[6], "b": r[7], "w": r[8], "l": r[9]}
            for r in files
        ],
        "refs": [list(r) for r in q("SELECT src_file,dst_file,ref_type,count,sample FROM refs")],
        "unresolved": [list(r) for r in q("SELECT src_file,token,ref_type,count,severity FROM unresolved")],
        "concepts": [{"id": r[0], "name": r[1], "cat": r[2]} for r in q("SELECT id,name,category FROM concepts")],
        "cm": [list(r) for r in q("SELECT file_id,concept_id,count FROM concept_mentions")],
        "people": [{"id": r[0], "code": r[1], "name": r[2], "prof": r[3]} for r in q("SELECT id,code,name,has_profile FROM people")],
        "msgs": [
            {"f": r[0], "series": r[1], "code": r[2], "subj": r[3], "ts": r[4], "from": r[5], "to": r[6]}
            for r in q("SELECT file_id,series,code,subject,sent_at,from_person,to_person FROM messages")
        ],
        "chars": [{"f": r[0], "person": r[1], "blurb": r[2]} for r in q("SELECT file_id,person_id,blurb FROM characters")],
        "schema": schema_json(con),
        "erd": ERD_LAYOUT,
        "sql": "\n".join(r[0] for r in q("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type DESC, name")),
        "scans": [
            {"id": r[0], "ts": r[1], "commit": r[2], "count": r[3], "added": r[4], "modified": r[5], "deleted": r[6], "moved": r[7]}
            for r in q("SELECT id,ts,git_commit,file_count,added,modified,deleted,moved FROM scans ORDER BY id DESC")
        ],
        "changes": [list(r) for r in q("SELECT scan_id,path,change,old_path FROM changes ORDER BY scan_id DESC, change, path")],
    }
    data.update(extra)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE_PATH.read_text(encoding="utf-8").replace("/*__DATA__*/null", payload)
    HTML_PATH.write_text(html, encoding="utf-8")


def summarize(con, changed, added, modified, deleted, moved):
    q = lambda sql: con.execute(sql).fetchall()
    n = lambda sql: con.execute(sql).fetchone()[0]
    log("=== Writing Map built ===")
    log("files present      :", n("SELECT count(*) FROM files WHERE status='present'"))
    log("documents / msgs   :", n("SELECT count(*) FROM documents"), "/", n("SELECT count(*) FROM messages"))
    log("characters / people:", n("SELECT count(*) FROM characters"), "/", n("SELECT count(*) FROM people"))
    log("levels / weapons   :", n("SELECT count(*) FROM levels"), "/", n("SELECT count(*) FROM weapons"))
    log("refs by type       :", dict(q("SELECT ref_type, count(*) FROM refs GROUP BY ref_type")))
    log("unresolved (broken):", n("SELECT count(*) FROM unresolved WHERE severity='broken'"),
        "| (no profile):", n("SELECT count(*) FROM unresolved WHERE severity='info'"))
    log("canon violations   :", n("SELECT count(*) FROM canon_checks WHERE status='violation'"),
        "| name issues:", n("SELECT count(*) FROM name_issues"),
        "| undated messages:", n("SELECT count(*) FROM messages WHERE file_id NOT IN (SELECT file_id FROM msg_dates)"))
    if changed:
        log("scan recorded      : +%d added, ~%d modified, -%d deleted, >%d moved" % (len(added), len(modified), len(deleted), len(moved)))
    else:
        log("scan               : no changes since last scan (history untouched)")
    log("db   ->", DB_PATH)
    log("html ->", HTML_PATH)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Rebuild the ICS Rigged Sphere writing map.")
    ap.add_argument("--quiet", action="store_true", help="print nothing unless something fails (for hooks / watchers)")
    ap.add_argument("--cat", nargs=2, metavar=("SCAN_ID", "PATH"),
                    help="print the stored text of PATH as it was in that scan, e.g. --cat 3 STORY.md")
    args = ap.parse_args()
    QUIET = args.quiet
    if args.cat:
        cat_version(int(args.cat[0]), args.cat[1])
    else:
        main()
