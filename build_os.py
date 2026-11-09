#!/usr/bin/env python3
"""
build_os.py - builds ICS-OS (version 0.1), the in-world operating system of the
ICS Earth Branch personal device and terminals.

It gathers the data for three apps and writes one self-contained offline page:

    ICS-OS/ics-os.html          (generated - do not edit by hand)

  Hearth           internal mail     messages from writing/internal-communications
                                     (parsed by build_mail.py in this folder)
  ICS Cloud Drive  file explorer     the documents in writing/documents
  Folio            document viewer   the same documents, gated by clearance

The page itself lives in os_template.html, os.css and os.js (same folder), which
this script inlines. build_map.py calls build() at the end of every run, so the
watcher and the git hook keep ICS-OS up to date.
Standalone: python ICS-OS/build_os.py

Python 3 standard library only.
"""
import datetime
import json
import re
import sqlite3
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_mail as bm  # noqa: E402

WRITING = bm.WRITING
DOC_DIR = WRITING / "documents"
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
}
# Files that sit outside the tier ladder: only the listed accounts may open them.
SPECIAL = {
    35: ["all"],                                 # "Not an ICS document." A paper notebook.
    39: ["all"],                                 # "It does not exist in the ICS system. It was found by you."
    42: ["access", "all"],                       # "The three-tier system does not apply."
    49: ["research", "director", "access", "all"],  # SEALED. Readers: Research Team, Branch Manager, EOD.
    51: ["research", "director", "access", "all"],  # Form GOV-PDR-002-BM. Readers: Research Team (authors), Branch Director, Board.
}
FOLDER_ORDER = [F_REC, F_HND, F_OPS, F_GOV, F_RES, F_BRD, F_OUT]

# [PROPOSAL] Layered documents. A marker line moves the reader into a section of that tier.
#   persist: stays until the next marker (or `reset`).   block: covers just the marked block.
#   until_rule: a persisted tier ends at the next horizontal rule.
RULE_RE = re.compile(r"^>?\s*-{3,}\s*$")
LAYERS = {
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


def segment(no, lines):
    """Split a document into [(tier, [lines])] following LAYERS[no]."""
    cfg = LAYERS.get(no)
    if not cfg:
        return [(OPEN, lines)]
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
    for p in sorted(DOC_DIR.glob("2.*.md")):
        m = re.match(r"2\.(\d{1,2})\s*[\u2014\u2013-]\s*(.+)\.md$", p.name)
        if not m:
            continue
        no = int(m.group(1))
        if no not in DOCS:
            continue  # [PROPOSAL] a new document needs a tier and folder in DOCS above
        tier, folder = DOCS[no]
        text = p.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff").replace("\r\n", "\n")
        segs = []
        for t, ls in segment(no, text.split("\n")):
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
            "outside": no in (35, 39, 42, 49), "roles": roles, "segs": segs,
            "size": st.st_size, "mtime": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "path": "documents/" + p.name,
        })
    return out


def mirror_info(msg):
    """[PROPOSAL] Staff (A) and PTKW (B) mail reaches the Branch Director as a retained copy.
    `views` is how many times the copy was opened before the Director first did. Fixed per
    message so a rebuild never changes it."""
    if msg["series"] not in ("A", "B"):
        return None
    return {"views": 1 + zlib.crc32(msg["code"].encode()) % 6}


def build(con=None, now=None, scan_id=None, out_path=OUT_PATH):
    own = con is None
    if own:
        con = sqlite3.connect(str(bm.DB_PATH))
    now = now or datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    if scan_id is None:
        scan_id = con.execute("SELECT max(id) FROM scans").fetchone()[0]

    people, msgs = bm.collect(con)
    known = {m["code"] for m in msgs}
    for m in msgs:
        m["mirror"] = mirror_info(m)
    for m in msgs:
        m["body"] = link_docs(m["body"])
    docs = collect_docs(known)

    payload = json.dumps({
        "os": {"name": OS_NAME, "version": OS_VERSION, "cloud": CLOUD_NAME, "docs": DOCS_NAME, "mail": bm.SYSTEM_NAME},
        "generated": now, "scan": scan_id, "tiers": TIER_NAMES,
        "series": bm.SERIES, "roles": ROLES, "people": people, "msgs": msgs,
        "docs": docs, "folders": FOLDER_ORDER,
    }, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    page = (HERE / "os_template.html").read_text(encoding="utf-8")
    page = page.replace("/*__CSS__*/", (HERE / "os.css").read_text(encoding="utf-8"))
    js = (HERE / "os.js").read_text(encoding="utf-8").replace("/*__DATA__*/null", payload)
    page = page.replace("/*__JS__*/", js.replace("</script", "<\\/script"))
    out_path.write_text(page, encoding="utf-8")
    if own:
        con.close()
    return len(msgs), len(docs)


if __name__ == "__main__":
    nm, nd = build()
    print("ICS-OS %s built: %d messages, %d documents -> %s" % (OS_VERSION, nm, nd, OUT_PATH))
