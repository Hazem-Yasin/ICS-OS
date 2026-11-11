#!/usr/bin/env python3
"""
build_os.py - builds ICS-OS (version 0.1), the in-world operating system of the
ICS Earth Branch personal device and terminals.

It gathers the data for four apps and writes one self-contained offline page:

    ics-os.html          (generated - do not edit by hand)

  Hearth           internal mail     the messages in ICS-Writing/canon/internal-communications
                                     (parsed by build_mail.py in this folder)
  ICS Cloud Drive  file explorer     the documents in ICS-Writing/canon/documents
  Folio            document viewer   the same documents, gated by clearance
  Timeline         story tracks      ICS-Writing/tools/timeline.json, checked against the messages and documents

The page itself lives in os_template.html, os.css and os.js (same folder), which
this script inlines. It reads the writing repo directly: a sibling folder called
ICS-Writing, or the folder named in the ICS_WRITING environment variable.

    python build_os.py

Python 3 standard library only.
"""
import datetime
import json
import re
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_mail as bm  # noqa: E402

WRITING = bm.WRITING
DOC_DIR = WRITING / "canon" / "documents"
OUT_PATH = HERE / "ics-os.html"

OS_NAME = "ICS-OS"          # [PROPOSAL] names; change here and in writing/ICS_OS.md
OS_VERSION = "0.1"
CLOUD_NAME = "ICS Cloud Drive"
DOCS_NAME = "Folio"

OPEN, PTKW, DIRECTOR, BOARD = 0, 1, 2, 3
TIER_NAMES = ["Open", "PTKW", "Branch Director", "Board"]

# [PROPOSAL] Sign-in accounts. `level` is how high up the document tiers the account reads.
# The same account governs mail (build_mail.access) and documents (below).
ROLES = [
    {"id": "staff", "label": "Standard employee", "level": OPEN,
     "blurb": "Floor staff. Delivered personal mail, Global Access notices and the all-staff documents."},
    {"id": "ptkw", "label": "PTKW employee", "level": PTKW,
     "blurb": "Placement, Transit, Knowledge and Welfare. Everything a standard employee sees, plus the PTKW channel, held and recovered mail, and PTKW documents."},
    {"id": "director", "label": "Branch Director", "level": DIRECTOR,
     "blurb": "Earth Branch. HQ directives, the Branch Director channel, PTKW documents and the copies the office receives of staff and PTKW mail. Not the Board."},
    {"id": "research", "label": "EOD Research Team", "level": PTKW,
     "blurb": "Interplanetary Research Division. Open mail and documents, the Research Team's own files and its sealed readerships."},
    {"id": "design", "label": "Design Team", "level": OPEN,
     "blurb": "Interface and brand design. The Design Team's working files, plus open mail and documents."},
    {"id": "access", "label": "All access", "level": BOARD,
     "blurb": "Board clearance. Every message and document as it exists in the world, sealed files included. No author notes."},
    {"id": "all", "label": "All files", "level": BOARD,
     "blurb": "Every file in the writing folder as the author sees it: proposals, writer's notes, file paths, files outside the ICS system."},
]

# [PROPOSAL] Per document: (tier needed to open it, Cloud Drive folder).
# Read from each file's own classification line. Layered documents (below) are
# gated section by section as well. Numbers are the document numbers 2.NN.
F_REC, F_HND, F_GOV = "Recruitment and Public", "Handbook and Forms", "Governance and Policy"
F_RES, F_BRD, F_OPS = "Research and Assessment", "Brand and Communications", "Operations and Commerce"
F_OUT = "Outside the ICS System"
DOCS = {
    1: (PTKW, F_OPS), 2: (PTKW, F_OPS), 3: (PTKW, F_HND), 4: (OPEN, F_REC), 5: (OPEN, F_REC),
    6: (OPEN, F_HND), 7: (OPEN, F_HND), 8: (PTKW, F_OPS), 9: (PTKW, F_OPS), 10: (OPEN, F_HND),
    11: (PTKW, F_OPS), 12: (PTKW, F_GOV), 13: (PTKW, F_OPS), 14: (BOARD, F_GOV), 15: (BOARD, F_RES),
    16: (BOARD, F_RES), 17: (BOARD, F_RES), 18: (PTKW, F_RES), 19: (OPEN, F_REC), 20: (OPEN, F_HND),
    21: (PTKW, F_GOV), 22: (DIRECTOR, F_GOV), 23: (BOARD, F_GOV), 24: (OPEN, F_REC), 25: (PTKW, F_RES),
    26: (OPEN, F_REC), 27: (PTKW, F_RES), 28: (PTKW, F_OPS), 29: (OPEN, F_HND), 30: (OPEN, F_HND),
    31: (OPEN, F_BRD), 32: (OPEN, F_BRD), 33: (OPEN, F_HND), 34: (OPEN, F_BRD), 35: (BOARD, F_OUT),
    36: (OPEN, F_OPS), 37: (OPEN, F_BRD), 38: (BOARD, F_GOV), 39: (BOARD, F_OUT), 40: (OPEN, F_OPS),
    41: (BOARD, F_RES), 42: (BOARD, F_OUT), 43: (PTKW, F_OPS), 44: (BOARD, F_GOV), 45: (OPEN, F_OPS),
    46: (PTKW, F_OPS), 47: (PTKW, F_RES), 48: (PTKW, F_RES), 49: (BOARD, F_RES), 50: (BOARD, F_GOV),
    51: (DIRECTOR, F_GOV),
    # Plan System documents (2.52-2.62), [PROPOSAL]. Whole-file tier = the lowest layer anyone can open.
    # 2.52, 2.55-2.58 and 2.62 open with a sheet that staff are handed; 2.53, 2.54, 2.59 and 2.61 open PTKW;
    # 2.60 opens above the Branch Director.
    52: (OPEN, F_OPS), 53: (PTKW, F_OPS), 54: (PTKW, F_OPS), 55: (OPEN, F_OPS), 56: (OPEN, F_OPS),
    57: (OPEN, F_OPS), 58: (OPEN, F_OPS), 59: (PTKW, F_OPS), 60: (BOARD, F_OPS), 61: (PTKW, F_OPS),
    62: (OPEN, F_OPS),
    # 2.63 is sealed with 2.49: two readers (Research Team, Branch Manager). See SPECIAL.
    63: (BOARD, F_RES),
    # 2.64 is not an ICS document: a sheet found in his quarters. No access level (as 2.35 and 2.39). See SPECIAL.
    64: (BOARD, F_OUT),
}
# Files that sit outside the tier ladder: only the listed accounts may open them.
SPECIAL = {
    35: ["all"],                                 # "Not an ICS document." A paper notebook.
    39: ["all"],                                 # "It does not exist in the ICS system. It was found by you."
    42: ["access", "all"],                       # "The three-tier system does not apply."
    49: ["research", "director", "access", "all"],  # SEALED. Readers: Research Team, Branch Manager, EOD.
    63: ["research", "director", "access", "all"],  # SEALED. EOD's pencil sheet; readers: Research Team, Branch Manager.
    64: ["all"],                                 # "It does not exist in the ICS system." EOD's note in the drawer.
    51: ["research", "director", "access", "all"],  # Form GOV-PDR-002-BM. Readers: Research Team (authors), Branch Director, Board.
}
FOLDER_ORDER = [F_REC, F_HND, F_OPS, F_GOV, F_RES, F_BRD, F_OUT]

# [PROPOSAL] Layered documents. A marker line moves the reader into a section of that tier.
#   persist: stays until the next marker (or `reset`).   block: covers just the marked block.
#   until_rule: a persisted tier ends at the next horizontal rule.
RULE_RE = re.compile(r"^>?\s*-{3,}\s*$")
LAYERS = {
    # Plan System documents: a line "*[Access: ...]*" opens the sheet that follows it (segment_access).
    # `default` is the tier of whatever comes before the first marker.
    52: {"access": True, "default": OPEN}, 53: {"access": True, "default": PTKW},
    54: {"access": True, "default": PTKW}, 55: {"access": True, "default": OPEN},
    56: {"access": True, "default": OPEN}, 57: {"access": True, "default": OPEN},
    58: {"access": True, "default": OPEN}, 59: {"access": True, "default": PTKW},
    60: {"access": True, "default": BOARD}, 61: {"access": True, "default": PTKW},
    62: {"access": True, "default": OPEN},
    24: {"block": [(r"^>\s*\*\*\[PTKW ANNOTATION", PTKW)]},
    25: {"block": [(r"^>\s*\*\*\[PTKW ANNOTATION", PTKW)]},
    29: {"reset": r"^###\s+TERM:",
         "persist": [(r"^\*\*\[GLOBAL\]\*\*", OPEN), (r"^\*\*\[PTKW\]\*\*", PTKW), (r"^\*\*\[BOARD\]\*\*", BOARD)]},
    31: {"reset": r"^##\s",
         "persist": [(r"^\*\[Access: Global", OPEN), (r"^\*\[Access: PTKW.*Branch Directors", DIRECTOR),
                     (r"^\*\[Access: PTKW", PTKW), (r"^\*\[Access: BOARD", BOARD)]},
    32: {"persist": [(r"^>\s*\*\*\[PTKW ACCESS", PTKW), (r"^>\s*\*\*\[BOARD ACCESS", BOARD)]},
    33: {"block": [(r"^\*\[PTKW Note", PTKW)]},
    34: {"block": [(r"^>\s*\*\*Programme Note.{1,3}PTKW Access", PTKW)]},
    37: {"block": [(r"^\*\[PTKW Annotation", PTKW)]},
    40: {"persist": [(r"^\*\[PTKW Access Layer", PTKW)]},
    43: {"persist": [(r"^\*\*\[GLOBAL ACCESS\]", OPEN), (r"^\*\*\[PTKW ACCESS\]", PTKW), (r"^\*\*\[BOARD ACCESS\]", BOARD)]},
    45: {"persist": [(r"^\*\[Access: PTKW", PTKW), (r"^\*\[Access: BOARD", BOARD)]},
    47: {"persist": [(r"^>\s*\*\*\[BOARD ADDENDUM", BOARD)], "until_rule": True},
    48: {"persist": [(r"^>\s*\*\*\[BOARD ADDENDUM", BOARD)], "until_rule": True},
}

DREF_RE = re.compile(r"\b(Documents?|Doc\.)(\s+)(2\.\d{1,2})\b")

# "*[Access: ABOVE BRANCH DIRECTOR - EOD Research Team.]*" and its relatives. The tier is the
# label at the start; a long cover note may mention other tiers later in its text.
ACCESS_RE = re.compile(r"^\*\[Access:\s*(.+?)\]?\*?\s*$")
ACCESS_TIERS = [("GLOBAL", OPEN), ("ABOVE BRANCH DIRECTOR", BOARD), ("BRANCH DIRECTOR", DIRECTOR),
                ("PTKW", PTKW), ("BOARD", BOARD)]
# The author's closing note, e.g. "*[PROPOSAL] New file. Proposed: ...*".
NOTE_RE = re.compile(r"^\*\[PROPOSAL\]")


def block_end(lines, i):
    """Index just past the annotation block that starts at lines[i]."""
    s, n = lines[i].strip(), len(lines)
    if len(s) > 160:  # the marker line carries its own text
        return i + 1
    j = i + 1
    if not s.startswith(">"):
        while j < n and not lines[j].strip():
            j += 1
        if j >= n or not lines[j].strip().startswith(">"):
            return i + 1
    while j < n and lines[j].strip().startswith(">") and not RULE_RE.match(lines[j].strip()):
        j += 1
    return j


def access_tier(label):
    up = label.upper()
    return next(t for key, t in ACCESS_TIERS if up.startswith(key))


def segment_access(lines, default):
    """Documents 2.52-2.62. Each `*[Access: ...]*` line opens a sheet at that tier, and the sheet
    runs to the next such line. Lines before the first marker are the sheet everyone is handed
    (or the title above a cover marker) and are read at `default`."""
    segs, cur = [], default

    def add(t, ls):
        if segs and segs[-1][0] == t:
            segs[-1][1].extend(ls)
        else:
            segs.append((t, list(ls)))

    for l in lines:
        m = ACCESS_RE.match(l.strip())
        if m:
            cur = access_tier(m.group(1))
        add(cur, [l])
    return segs


def split_notes(lines):
    """Take the author's closing [PROPOSAL] note off the end of a document. Only the trailing run
    counts (notes, blank lines and rules); a [PROPOSAL] line inside the text is left alone.
    Returns (document lines, note lines)."""
    k = len(lines)
    while k > 0 and (not lines[k - 1].strip() or RULE_RE.match(lines[k - 1].strip())
                     or NOTE_RE.match(lines[k - 1].strip())):
        k -= 1
    notes = [l for l in lines[k:] if NOTE_RE.match(l.strip())]
    return lines[:k], notes


def segment(no, lines):
    """Split a document into [(tier, [lines])] following LAYERS[no]."""
    cfg = LAYERS.get(no)
    if not cfg:
        return [(OPEN, lines)]
    if cfg.get("access"):
        return segment_access(lines, cfg["default"])
    segs, cur, until_rule, i, n = [], OPEN, False, 0, len(lines)

    def add(t, ls):
        if segs and segs[-1][0] == t:
            segs[-1][1].extend(ls)
        else:
            segs.append((t, list(ls)))

    while i < n:
        s = lines[i].strip()
        if until_rule and RULE_RE.match(s):
            cur, until_rule = OPEN, False
        if cfg.get("reset") and re.match(cfg["reset"], s):
            cur, until_rule = OPEN, False
        for pat, t in cfg.get("persist", []):
            if re.match(pat, s):
                cur, until_rule = t, bool(cfg.get("until_rule")) and t > OPEN
                break
        else:
            hit = next((t for pat, t in cfg.get("block", []) if re.match(pat, s)), None)
            if hit is not None:
                j = block_end(lines, i)
                add(hit, lines[i:j])
                i = j
                continue
        add(cur, [lines[i]])
        i += 1
    return segs


def link_docs(h):
    def f(m):
        return '%s%s<a href="#" class="dref" data-doc="2.%02d">%s</a>' % (
            m.group(1), m.group(2), int(m.group(3).split(".")[1]), m.group(3))
    return DREF_RE.sub(f, h)


def collect_docs(known):
    out = []
    missing = []
    for p in sorted(DOC_DIR.glob("2.*.md")):
        m = re.match(r"2\.(\d{1,2})\s*[\u2014\u2013-]\s*(.+)\.md$", p.name)
        if not m:
            continue
        no = int(m.group(1))
        if no not in DOCS:
            missing.append(p.name)  # a new document needs a tier and folder in DOCS above
            continue
        tier, folder = DOCS[no]
        text = p.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff").replace("\r\n", "\n")
        body_lines, note_lines = split_notes(text.split("\n"))
        segs = []
        for t, ls in segment(no, body_lines):
            h = link_docs(bm.render(ls, known))
            if not h.strip():
                continue
            segs.append({"t": t, "h": h, "n": len(bm.plain(h))})
        if no in SPECIAL:
            roles = SPECIAL[no]
        else:
            roles = [r["id"] for r in ROLES if r["level"] >= tier]
        st = p.stat()
        out.append({
            "no": "2.%02d" % no, "title": m.group(2).strip(), "folder": folder, "tier": tier,
            "outside": no in (35, 39, 42, 49, 64), "roles": roles, "segs": segs,
            "notes": link_docs(bm.render(note_lines, known)) if note_lines else "",
            "size": st.st_size, "mtime": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "path": "canon/documents/" + p.name,
        })
    return out, missing


def mirror_info(msg):
    """[PROPOSAL] Staff (A) and PTKW (B) mail reaches the Branch Director as a retained copy.
    `views` is how many times the copy was opened before the Director first did. Fixed per
    message so a rebuild never changes it."""
    if msg["series"] not in ("A", "B"):
        return None
    return {"views": 1 + zlib.crc32(msg["code"].encode()) % 6}


def source_stamp():
    """A short fingerprint of every source file, shown where the old build showed a scan number.
    It changes whenever any message or document changes."""
    h = 0
    for f in sorted(list(bm.COMMS.glob("*/*.md")) + list(DOC_DIR.glob("2.*.md"))):
        h = zlib.crc32(f.read_bytes(), h)
    return "%08x" % h

WEEKDAYS = ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Monday"]  # Day 0 is a Tuesday (TIME_MODEL 1.1)
WEEK_RE = re.compile(r"Week\s+(\d+),\s*([A-Za-z]+)")


def build_timeline(msgs, docs):
    """[PROPOSAL] Tracks for the Timeline app, from ICS-Writing/tools/timeline.json.
    Each ref is checked against the real messages, documents and scenes; anything that is not
    found is reported and dropped. Dates not given in the JSON come from the message itself."""
    path = bm.WRITING / "tools" / "timeline.json"
    if not path.exists():
        print("WARNING: no timeline.json in the writing repo; the Timeline app will be empty")
        return {"tracks": []}
    src = json.loads(path.read_text(encoding="utf-8"))
    by_code = {m["code"]: m for m in msgs}
    doc_nos = {d["no"] for d in docs}
    scenes = {}
    for f in sorted((bm.WRITING / "story" / "scenes").glob("*.md")):
        mm = re.match(r"(1\.\d+)\b", f.name)
        if mm:
            first = f.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff").split("\n", 1)[0]
            scenes[mm.group(1)] = re.sub(r"^#\s*[\d.]+\s*[\u2014\u2013-]\s*", "", first).strip()

    def msg_day(m):
        mm = re.search(r"\bD(\d+)$", m["ds"])
        return int(mm.group(1)) if mm and m["sort"][0] == 300 and m["sort"][1] == 4 else None

    tracks, bad = [], []
    for tr in src["tracks"]:
        groups = []
        for it in tr["items"]:
            refs, first = [], None
            for r in it.get("refs", []):
                if r.startswith("scene:"):
                    no = r[6:]
                    if no in scenes:
                        refs.append({"t": "s", "id": no, "title": scenes[no]})
                    else:
                        bad.append(tr["id"] + ": " + r)
                elif r in by_code:
                    refs.append({"t": "m", "id": r})
                    first = first or by_code[r]
                elif r in doc_nos:
                    refs.append({"t": "d", "id": r})
                else:
                    bad.append(tr["id"] + ": " + r)
            day, time, sent = it.get("day"), it.get("time", ""), None
            if first is not None:
                md = msg_day(first)
                if day is None:
                    day = md
                    time = time or first["clock"]
                elif md is not None and md != day:
                    sent = "message dated Day %d" % md
                elif md == day:
                    time = time or first["clock"]
            if it.get("when"):
                head = it["when"]
            elif day is not None:
                head = "Day %d \u00b7 %s" % (day, WEEKDAYS[day % 7])
            elif first is not None:
                wk = WEEK_RE.search(first["date"])
                cq = re.match(r"C(\d+) Q(\d)", first["ds"])
                if wk and cq:
                    head = "Cycle %s Q%s \u00b7 Week %s, %s" % (cq.group(1), cq.group(2), wk.group(1), wk.group(2))
                    time = time or first["clock"]
                elif cq:
                    dd = re.search(r"\bD(\d+)$", first["ds"])
                    head = "Cycle %s Q%s" % (cq.group(1), cq.group(2)) + (" \u00b7 Day %s" % dd.group(1) if dd else "")
                    time = time or first["clock"]
                else:
                    head = "Undated"
            else:
                head = "Undated"
            item = {"time": time, "text": it.get("text", ""), "sent": sent, "refs": refs}
            if groups and groups[-1]["h"] == head:
                groups[-1]["items"].append(item)
            else:
                groups.append({"h": head, "items": [item]})
        tracks.append({"id": tr["id"], "label": tr["label"], "blurb": tr.get("blurb", ""), "groups": groups})
    if bad:
        print("WARNING: timeline.json refers to things that do not exist: " + ", ".join(bad))
    return {"tracks": tracks}


def build(now=None, out_path=OUT_PATH):
    now = now or datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    scan_id = source_stamp()

    people, msgs = bm.collect()
    known = {m["code"] for m in msgs}
    for m in msgs:
        m["mirror"] = mirror_info(m)
    for m in msgs:
        m["body"] = link_docs(m["body"])
    docs, missing = collect_docs(known)
    if missing:
        print("WARNING: not in the Cloud Drive until they have a line in DOCS: " + ", ".join(missing))
    timeline = build_timeline(msgs, docs)

    payload = json.dumps({
        "os": {"name": OS_NAME, "version": OS_VERSION, "cloud": CLOUD_NAME, "docs": DOCS_NAME, "mail": bm.SYSTEM_NAME},
        "generated": now, "scan": scan_id, "tiers": TIER_NAMES,
        "series": bm.SERIES, "roles": ROLES, "people": people, "msgs": msgs,
        "docs": docs, "folders": FOLDER_ORDER, "timeline": timeline,
    }, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    page = (HERE / "os_template.html").read_text(encoding="utf-8")
    page = page.replace("/*__CSS__*/", (HERE / "os.css").read_text(encoding="utf-8"))
    js = (HERE / "os.js").read_text(encoding="utf-8").replace("/*__DATA__*/null", payload)
    page = page.replace("/*__JS__*/", js.replace("</script", "<\\/script"))
    out_path.write_text(page, encoding="utf-8")
    return len(msgs), len(docs)


if __name__ == "__main__":
    nm, nd = build()
    print("ICS-OS %s built: %d messages, %d documents -> %s" % (OS_VERSION, nm, nd, OUT_PATH))
