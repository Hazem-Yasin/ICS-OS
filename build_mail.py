#!/usr/bin/env python3
"""
build_mail.py - the message half of ICS-OS: data for Hearth, the ICS Earth Branch mail app.

Reads every message the map already tracks (writing_map.db) plus the message
files themselves, parses them, decides who may open each one, and returns plain
data. build_os.py (same folder) calls collect() and writes the ICS-OS page.

Also holds render() / inline(), the small markdown-to-HTML helpers that
build_os.py reuses for documents.

Python 3 standard library only.
"""
import html
import json
import re
import sqlite3
import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WRITING = ROOT / "writing"
DB_PATH = ROOT / "writing-map" / "writing_map.db"

SYSTEM_NAME = "Hearth"  # [PROPOSAL] the in-world name; change here and in writing/HEARTH.md

SERIES = {
    "A": "Staff",
    "B": "PTKW",
    "C": "Branch Director and HQ",
    "D": "Design Team",
}

# Visibility is decided per message by access() below and stored in each message's "roles".
# The sign-in roles themselves live in build_os.py (they govern mail and documents).

KEY_RE = re.compile(r"^\*\*([^*:]+?):\*\*\s*(.*)$")
ADDR_RE = re.compile(r"^\*\*(?:From|To|Cc):\*\*\s*(.*)$", re.M)
CODE_RE = re.compile(r"\b([ABCD]-\d{2})\b")
META_RE = re.compile(r"^\s*\*?\s*(\[PROPOSAL\]|→ See:|\[End of|\[Note)")


# ---------------------------------------------------------------- markdown ----

def inline(text, known):
    t = html.escape(text, quote=False)
    spans = []

    def stash(m):
        spans.append("<code>%s</code>" % m.group(1))
        return "\x00%d\x00" % (len(spans) - 1)

    t = re.sub(r"`([^`]+)`", stash, t)
    t = CODE_RE.sub(lambda m: '<a href="#%s" class="mref">%s</a>' % (m.group(1), m.group(1))
                    if m.group(1) in known else m.group(1), t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", t)
    return re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], t)


def render(lines, known):
    out, para, i, n = [], [], 0, len(lines)

    def flush():
        if para:
            out.append("<p>%s</p>" % "<br>".join(inline(p, known) for p in para))
            para.clear()

    while i < n:
        ln = lines[i].rstrip()
        s = ln.strip()
        if not s:
            flush(); i += 1; continue
        if re.fullmatch(r"-{3,}", s):
            flush(); out.append("<hr>"); i += 1; continue
        if s.startswith(">"):
            flush()
            block = []
            while i < n and lines[i].strip().startswith(">"):
                block.append(re.sub(r"^\s*> ?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % render(block, known))
            continue
        if s.startswith("|"):
            flush()
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                head, body = rows[0], rows[1:]
                out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
                    "".join("<th>%s</th>" % inline(c, known) for c in head),
                    "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c, known) for c in r) for r in body)))
            continue
        m = re.match(r"^#{1,6}\s+(.*)", s)
        if m:
            flush()
            lvl = len(re.match(r"^#+", s).group(0))
            out.append('<h4 class="h%d">%s</h4>' % (lvl, inline(m.group(1), known))); i += 1; continue
        if re.match(r"^[-*]\s+\S", s) and not s.startswith("**"):
            flush(); items = []
            while i < n and re.match(r"^\s*[-*]\s+\S", lines[i]) and not lines[i].strip().startswith("**"):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i].rstrip())); i += 1
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline(x, known) for x in items))
            continue
        if re.match(r"^\d+\.\s+\S", s):
            flush(); items = []
            while i < n and re.match(r"^\s*\d+\.\s+\S", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i].rstrip())); i += 1
            out.append("<ol>%s</ol>" % "".join("<li>%s</li>" % inline(x, known) for x in items))
            continue
        para.append(ln)
        i += 1
    flush()
    return "".join(out)


def plain(htm):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", htm))).strip()


# ------------------------------------------------------------ message files ----

def split_message(text):
    """Return (banner_lines, headers[(key, value)], body_lines, meta_lines)."""
    lines = text.lstrip("\ufeff").replace("\r\n", "\n").split("\n")
    sep = next((k for k, l in enumerate(lines[:20]) if re.fullmatch(r"\s*-{3,}\s*", l)), None)
    if sep is None:
        sep = 0
        while sep < len(lines) and (KEY_RE.match(lines[sep].strip()) or not lines[sep].strip()):
            sep += 1
        head, body = lines[:sep], lines[sep:]
    else:
        head, body = lines[:sep], lines[sep + 1:]
    banner, headers = [], []
    for l in head:
        m = KEY_RE.match(l.strip())
        if m:
            headers.append((m.group(1).strip(), m.group(2).strip()))
        elif l.strip():
            banner.append(l.strip())
    meta, k = [], len(body)
    while k > 0 and (not body[k - 1].strip() or re.fullmatch(r"\s*-{3,}\s*", body[k - 1])
                     or META_RE.match(body[k - 1])):
        k -= 1
    meta, body = body[k:], body[:k]
    return banner, headers, body, meta


def classify(status, name, headers):
    s = (status or "").upper()
    keys = {k.lower() for k, _ in headers}
    if s.startswith("NOT A MESSAGE"):
        return "notes"
    if (re.search(r"\b(DRAFT|UNSENT|NOT SENT|NEVER SENT)\b", s) and not s.startswith(("SENT", "CCN SENT"))) \
            or "(unsent)" in name.lower():
        return "drafts"
    if "SEALED" in s or "BOARD ACCESS" in s:
        return "sealed"
    if "INTERCEPT" in s or "intercept thread" in name.lower() or "redacted by" in keys:
        return "held"
    return "delivered"


DESIGNATOR_RE = re.compile(r"\b(K-\d+|VAH-\d+|TOR-\d+|ICS-OP-\d+)\b")
ECODE_RE = re.compile(r"\b(E-\d{5})\b")
NAME_AFTER_RE = re.compile(r"^\s*(?:\(\s*([^,()\u2014]+?)\s*(?:[,)\u2014]|$)|\u2014\s*([A-Z][A-Za-z.' ]+?)\s*(?:[,(;]|$))")
GROUPS = [  # (needle in upper-cased header, mailbox id, label, role it signs in as)
    ("BRANCH DIRECTOR", "grp:director", "Branch Director", "director"),
    ("BRANCH MANAGER", "grp:manager", "Earth Branch Manager", "director"),
    ("RESEARCH TEAM", "grp:research", "EOD Research Team", "research"),
    ("INTERPLANETARY HQ", "grp:hq", "Interplanetary HQ", "director"),
]


def mailboxes(frm, to, cc, people):
    """[PROPOSAL] Named mailboxes a message belongs to. Fills `people` {id: {label, role}}."""
    text = " ; ".join([frm or "", to or "", cc or ""])
    up = text.upper()
    ids = []
    for m in ECODE_RE.finditer(text):
        nm = NAME_AFTER_RE.match(text[m.end():])
        name = (nm.group(1) or nm.group(2)).strip() if nm else ""
        if len(name) < 3 or name.islower():
            name = ""
        label = "%s \u00b7 %s" % (name, m.group(1)) if name else m.group(1)
        people.setdefault(m.group(1), {"label": label, "role": "staff"})
        ids.append(m.group(1))
    for m in DESIGNATOR_RE.finditer(text):
        people.setdefault(m.group(1), {"label": "PTKW " + m.group(1), "role": "ptkw"})
        ids.append(m.group(1))
    for needle, gid, label, role in GROUPS:
        if needle in up:
            people.setdefault(gid, {"label": label, "role": role})
            ids.append(gid)
    return sorted(set(ids))


def access(series, folder, status, frm, to, cc):
    """[PROPOSAL] Return (tier label, [role ids that may open the message]).

    Tiers, lowest to highest: Open, PTKW, Branch Director, Above Branch Director, Sealed, Board.
    A role sees its own tier and everything below it. 'all' and 'access' see everything.
    """
    s = (status or "").upper()
    people = (frm + " " + to + " " + cc).upper()
    r = {"all", "access"}
    if folder == "sealed":
        if "BOARD ACCESS" in s:
            return "Board", sorted(r)
        readers = s.split("READERS", 1)[-1].split(". ", 1)[0]
        if "BRANCH MANAGER" in readers:
            r.add("director")
        if "RESEARCH TEAM" in readers:
            r.add("research")
        return "Sealed", sorted(r)
    if "ABOVE BRANCH DIRECTOR" in s:
        return "Above Branch Director", sorted(r)
    if series == "D":
        r.add("design")
        if "PTKW" in s or "BOARD COMMUNICATION" in s:
            r |= {"ptkw", "director"}
            return "PTKW", sorted(r)
        return "Design Team", sorted(r)
    if series == "C":
        r.add("director")
        if "RESEARCH TEAM" in people:
            r.add("research")
        return "Branch Director", sorted(r)
    if series == "B" and "GLOBAL ACCESS" not in s:
        r |= {"ptkw", "director"}
        return "PTKW", sorted(r)
    if series == "A" and folder != "delivered":
        r |= {"ptkw", "director"}  # held, unsent or found mail: only PTKW has it
        return "PTKW", sorted(r)
    return "Open", sorted(r | {"staff", "ptkw", "director", "research", "design"})


def short_date(cycle, quarter, day):
    if cycle is None:
        return ""
    out = "C%s" % cycle
    if quarter:
        out += " Q%s" % quarter
    if day is not None:
        out += " D%s" % day
    return out


def collect(con):
    """Return (people, msgs): the mailbox directory and every message, ready for JSON."""
    q = lambda sql, *a: con.execute(sql, a).fetchall()

    rows = q("""SELECT m.file_id, f.path, m.series, m.number, m.code, m.subject, m.from_raw, m.to_raw
                FROM messages m JOIN files f ON f.id = m.file_id
                WHERE f.status = 'present' ORDER BY m.series, m.number""")
    dates = {r[0]: r[1:] for r in q("SELECT file_id, cycle, quarter, day, clock, raw FROM msg_dates")}
    code_by_file = {r[0]: r[4] for r in rows}
    known = set(code_by_file.values())

    links_out, links_in = {}, {}
    for s, d in q("SELECT src_file, dst_file FROM refs WHERE ref_type IN ('message','path')"):
        if s in code_by_file and d in code_by_file and s != d:
            links_out.setdefault(code_by_file[s], set()).add(code_by_file[d])
            links_in.setdefault(code_by_file[d], set()).add(code_by_file[s])

    msgs, people = [], {}
    for fid, path, series, number, code, subject, frm, to in rows:
        text = (WRITING / path).read_text(encoding="utf-8", errors="replace")
        banner, headers, body, meta = split_message(text)
        hd = {k.lower(): v for k, v in headers}
        cycle, quarter, day, clock, raw = dates.get(fid, (None, None, None, None, None))
        status = hd.get("status", "")
        folder = classify(status, Path(path).name, headers)
        addr = " ; ".join(ADDR_RE.findall(text.replace("\r\n", "\n")))  # every From/To/Cc line, thread blocks included
        tier, roles = access(series, folder, status, addr, "", "")
        body_html = render(body, known)
        meta_html = render(meta, known)
        rest = [[k, inline(v, known)] for k, v in headers
                if k.lower() not in ("from", "to", "cc", "subject", "date", "timestamp", "status")]
        msgs.append({
            "code": code, "series": series, "folder": folder, "path": path, "tier": tier, "roles": roles,
            "box": mailboxes(addr, "", "", people),
            "subject": inline(hd.get("subject", subject or "(no subject)"), known) if False else (subject or "(no subject)"),
            "from": frm or hd.get("from", ""), "to": to or hd.get("to", ""), "cc": hd.get("cc", ""),
            "date": raw or hd.get("date", "") or hd.get("timestamp", ""),
            "ds": short_date(cycle, quarter, day), "clock": clock or "",
            "sort": [cycle if cycle is not None else 99999, quarter or 0, day if day is not None else 0, clock or "", code],
            "status": status, "banner": [html.escape(b.replace("*", "")) for b in banner],
            "details": rest, "body": body_html, "meta": meta_html,
            "proposal": "[PROPOSAL]" in text,
            "txt": plain(body_html + " " + " ".join(banner)).lower()[:12000],
            "preview": plain(body_html)[:140],
            "out": sorted(links_out.get(code, ())), "in": sorted(links_in.get(code, ())),
        })

    return people, msgs
