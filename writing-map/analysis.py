"""
Analysis passes for writing-map.

Pure functions: they take the scanned corpus and return plain data. build_map.py
stores the results in SQLite and hands them to the HTML viewer.

  canon_check      regex rules from canon_rules.json  -> violations
  parse_msg_date   Cycle / Quarter / Day / clock of a message
  timeline         placed + undated messages, reply-order warnings
  phase_counts     "Phase N" mentions per file
  level_stats      who cites each facility level
  name_issues      E-code / name / spelling consistency
  lore_terms       acronyms and codes, defined or not
  relationships    character graph from messages + co-mentions
  exports          Mermaid + Graphviz text
"""
import difflib
import json
import re
import zlib
from collections import Counter, defaultdict
from itertools import combinations

AGGREGATES = set()   # big files that duplicate other files (none now; the master file lives outside writing/)


def short(line, n=150):
    line = re.sub(r"\s+", " ", line).strip()
    return line if len(line) <= n else line[: n - 1] + "…"


def _norm(v):
    return re.sub(r"\s+", " ", str(v).replace("&", "and")).strip().lower()


def counted(corpus):
    """Corpus without the aggregate duplicates (use for statistics)."""
    return [f for f in corpus if f["p"] not in AGGREGATES]


# ---------------------------------------------------------------------------
# Canon rules
# ---------------------------------------------------------------------------
def canon_check(corpus, cfg, doc_count):
    computed = {"@doc_count": str(doc_count)}
    accepted = cfg.get("accepted", [])
    results, rule_rows, check_rows = [], [], []
    files = counted(corpus)
    for rule in cfg["rules"]:
        rx = re.compile(rule["pattern"], re.I if "i" in rule.get("flags", "") else 0)
        lf = re.compile(rule["line_filter"]) if rule.get("line_filter") else None
        lx = re.compile(rule["line_exclude"]) if rule.get("line_exclude") else None
        allowed = [computed.get(a, a) for a in rule["allowed"]]
        allowed_n = {_norm(a) for a in allowed}
        ignore = rule.get("ignore_files", [])
        ok = acc = 0
        flagged = []
        for f in files:
            if any(s in f["p"] for s in ignore):
                continue
            seen = set()
            for ln, line in enumerate(f["text"].splitlines(), 1):
                if lf and not lf.search(line):
                    continue
                if lx and lx.search(line):
                    continue
                for m in rx.finditer(line):
                    val = next((g for g in m.groups() if g), None)
                    if val is None or (ln, _norm(val)) in seen:
                        continue
                    seen.add((ln, _norm(val)))
                    if _norm(val) in allowed_n:
                        ok += 1
                        status = "ok"
                    elif any(a.get("rule") == rule["id"] and _norm(a.get("value", "")) == _norm(val)
                             and a.get("path", "") in f["p"] for a in accepted):
                        acc += 1
                        status = "accepted"
                    else:
                        status = "violation"
                        flagged.append({"f": f["id"], "line": ln, "value": val, "text": short(line, 220)})
                    check_rows.append((rule["id"], f["id"], ln, val, status, short(line, 220)))
        rule_rows.append((rule["id"], rule["label"], rule["pattern"], json.dumps(rule["allowed"])))
        results.append({
            "id": rule["id"], "label": rule["label"], "allowed": allowed, "ok": ok, "accepted": acc,
            "n_flagged": len(flagged), "flagged": flagged[:200],
            "accepted_list": [a for a in accepted if a.get("rule") == rule["id"]],
        })
    return results, rule_rows, check_rows


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------
KEYLINE = re.compile(r"^\*\*(Date|Timestamp|Sent|Action date|Status|Subject)[^*]*\*\*\s*(.*)$")
PRIORITY = {"Date": 0, "Timestamp": 0, "Sent": 0, "Action date": 1, "Status": 2, "Subject": 3}
CYCLE_RX = re.compile(r"Cycle\s+(\d{3})(?:\s*,?\s*Q([1-4]))?(?:[\s,\-—–]*Day\s+(\d+)(\s*post-[\w -]+)?)?")
CLOCK_RX = re.compile(r"\b(\d{1,2}:\d{2})\b")


def parse_msg_date(text):
    """Header date if there is one; otherwise (marked 'Body (inferred)') the latest
    'Cycle NNN QN' found in the first 60 lines."""
    lines = text.splitlines()
    cands = []
    for ln in lines[:16]:
        m = KEYLINE.match(ln)
        if m:
            cands.append((PRIORITY[m.group(1)], m.group(1), m.group(2)))
        elif re.match(r"^Cycle\s+\d{3}", ln.strip()):
            cands.append((1, "Line", ln.strip()))
    for _, src, s in sorted(cands, key=lambda c: c[0]):
        m = CYCLE_RX.search(s)
        if m:
            clock = CLOCK_RX.search(s)
            return {
                "cycle": int(m.group(1)), "q": int(m.group(2) or 0),
                "day": int(m.group(3)) if m.group(3) else None,
                "clock": clock.group(1) if clock else None,
                "raw": s.strip()[:90], "src": src, "rel": bool(m.group(4)),
            }
    best = None
    for ln in lines[:60]:
        for m in re.finditer(r"Cycle\s+(\d{3})\s*,?\s*Q([1-4])", ln):
            k = (int(m.group(1)), int(m.group(2)))
            if best is None or k > best[0]:
                best = (k, ln.strip())
    if best:
        return {"cycle": best[0][0], "q": best[0][1], "day": None, "clock": None,
                "raw": best[1][:90], "src": "Body (inferred)", "rel": False}
    return None


def timeline(corpus, msgs, dates):
    """msgs: list of dicts (f, code, series); dates: file_id -> parsed date or None."""
    by_f = {m["f"]: m for m in msgs}
    placed, undated = [], []
    for m in msgs:
        d = dates.get(m["f"])
        if d:
            placed.append(dict(m, **d))
        else:
            undated.append(m["f"])
    key = lambda d: (d["cycle"], d["q"], d["day"] or 0)
    warnings = []
    code_f = {m["code"]: m["f"] for m in msgs if m["code"]}
    for f in corpus:
        if f["id"] not in by_f or not dates.get(f["id"]):
            continue
        for line in f["text"].splitlines()[:20]:
            if "Original message" not in line:
                continue
            for c in re.findall(r"(?<![\w-])([ABC]-\d{2})(?![\w-])", line):
                other = code_f.get(c)
                if other and dates.get(other) and key(dates[f["id"]])[:2] < key(dates[other])[:2]:
                    warnings.append({"f": f["id"], "other": other, "text": "%s is dated before the message it quotes (%s)" % (f["p"].rsplit("/", 1)[-1], c)})
    return {"placed": placed, "undated": undated, "warnings": warnings}


# ---------------------------------------------------------------------------
# Phases and levels
# ---------------------------------------------------------------------------
PHASE_NUM = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
_PN = r"(\d|Zero|One|Two|Three|Four|Five|Six)"
PHASE_RX = re.compile(
    r"(?<!Construction )(?<!Fit-Out )(?<!Design )(?<!Opening )\bPhases?\s+" + _PN
    + r"\b(?:\s*(?:through|to|-|–|—)\s*" + _PN + r"\b)?", re.I)


def _pn(s):
    return int(s) if s.isdigit() else PHASE_NUM[s.lower()]


def phase_counts(corpus):
    rows = []
    for f in corpus:
        c = Counter()
        for m in PHASE_RX.finditer(f["text"]):
            a = _pn(m.group(1))
            b = _pn(m.group(2)) if m.group(2) else a
            for n in (range(a, b + 1) if a < b <= 6 else [a]):
                if 0 <= n <= 6:
                    c[n] += 1
        rows += [(f["id"], ph, n) for ph, n in sorted(c.items())]
    return rows


def level_stats(corpus, level_files, level_rx):
    """level_files: {n: (file_id, path, words)}"""
    mentions = defaultdict(Counter)
    files = defaultdict(lambda: defaultdict(set))
    for f in counted(corpus):
        if f["kind"] == "level":
            continue
        for m in level_rx.finditer(f["text"]):
            a = int(m.group(1))
            lv = [a]
            if m.group(3):
                b = int(m.group(3))
                if m.group(2) in ("-", "–", "—", "to") and a < b <= 14:
                    lv = list(range(a, b + 1))
                elif b <= 14:
                    lv = [a, b]
            for n in lv:
                if 0 <= n <= 14:
                    mentions[n][f["cat"]] += 1
                    files[n][f["cat"]].add(f["id"])
    rows, out = [], []
    for n in range(0, 15):
        own = level_files.get(n)
        allf = set().union(*files[n].values()) if files[n] else set()
        out.append({
            "level": n, "own_file": own[0] if own else None, "own_words": own[2] if own else 0,
            "mentions": dict(mentions[n]), "files": len(allf), "total": sum(mentions[n].values()),
        })
        rows += [(n, cat, len(files[n][cat]), cnt) for cat, cnt in mentions[n].items()]
    return out, rows


# ---------------------------------------------------------------------------
# Names and IDs
# ---------------------------------------------------------------------------
CODE_PAREN = re.compile(r"E-(\d{5})\s*\(([^)\n]{1,140})\)")
CODE_DASH = re.compile(r"E-(\d{5})\s*[—–-]\s*([A-Z][a-z]+(?: [A-Z][a-z]+)?)")
NAME_OK = re.compile(r"^[A-Z][a-z]+(?: [A-Z][a-z]+)?$")
NOT_NAMES = {"Level", "Night", "Senior", "Cleaning", "Branch", "Analyst", "Unknown", "Player", "Work", "Duty", "Regional"}


def _vocab(corpus):
    lower, caps = Counter(), Counter()
    where = defaultdict(set)
    for f in counted(corpus):
        for w in re.findall(r"\b[A-Za-z][a-z]{2,}\b", f["text"]):
            if w[0].islower():
                lower[w] += 1
        for w in re.findall(r"\b[A-Z][a-z]{3,}\b", f["text"]):
            caps[w] += 1
            where[w].add(f["p"])
    return lower, caps, where


def name_issues(corpus, accepted=()):
    code_names, name_codes, name_levels = defaultdict(Counter), defaultdict(set), defaultdict(Counter)
    code_files, name_files = defaultdict(set), defaultdict(set)
    for f in counted(corpus):
        for m in CODE_PAREN.finditer(f["text"]):
            code = "E-" + m.group(1)
            inner = m.group(2)
            nm = re.split(r"\s*[,;—–]\s*|\s+-\s+", inner, maxsplit=1)[0].strip()
            if not NAME_OK.match(nm) or nm.split()[0] in NOT_NAMES:
                continue
            code_names[code][nm] += 1
            name_codes[nm].add(code)
            code_files[code].add(f["p"])
            name_files[nm].add(f["p"])
            lv = re.search(r"Level\s+(\d+)", inner)
            if lv:
                name_levels[nm][lv.group(1)] += 1
        for m in CODE_DASH.finditer(f["text"]):
            code, nm = "E-" + m.group(1), m.group(2)
            if nm.split()[0] in NOT_NAMES:
                continue
            code_names[code][nm] += 1
            name_codes[nm].add(code)
            code_files[code].add(f["p"])
            name_files[nm].add(f["p"])
    issues = []

    def add(kind, sev, subject, detail, paths):
        if subject in accepted or kind + ":" + subject in accepted:
            return
        issues.append({"kind": kind, "sev": sev, "subject": subject, "detail": detail, "paths": sorted(paths)[:40]})

    for code, names in code_names.items():
        ns = list(names)
        bad = False
        for a, b in combinations(ns, 2):
            fa, fb = a.split(), b.split()
            if fa[0] != fb[0] or (len(fa) > 1 and len(fb) > 1 and fa[1] != fb[1]):
                bad = True
        if bad:
            add("code-conflict", "error", code, "%s is used for different people: %s" % (code, ", ".join("%s (%d)" % kv for kv in names.most_common())), code_files[code])
    for nm, codes in name_codes.items():
        if len(nm.split()) == 2 and len(codes) > 1:
            add("name-multi-code", "warn", nm, "%s appears under %d E-codes: %s" % (nm, len(codes), ", ".join(sorted(codes))),
                set().union(*[code_files[c] for c in codes]))
    firsts = defaultdict(set)
    for nm, codes in name_codes.items():
        if len(nm.split()) == 2:
            firsts[nm.split()[0]].add(nm)
    for first, full in firsts.items():
        if len(full) > 1:
            add("first-name-clash", "warn", first, "Same first name, different surnames: " + ", ".join(sorted(full)),
                set().union(*[name_files[n] for n in full]))
    for nm, lv in name_levels.items():
        if len(lv) > 1:
            add("level-drift", "info", nm, "%s is placed on different levels: %s" % (nm, ", ".join("Level %s (%d)" % kv for kv in sorted(lv.items()))), name_files[nm])
    # near-miss spellings of known names
    lower, caps, where = _vocab(corpus)
    known = set()
    for nm in list(name_codes):
        known.update(nm.split())
    for f in corpus:
        if f["kind"] == "character":
            known.update(w for w in re.findall(r"[A-Z][a-z]{3,}", f["title"] or ""))
    known = {k for k in known if caps.get(k, 0) >= 5}
    seen = set()
    for tok, n in caps.items():
        if n > 3 or tok in known or lower.get(tok.lower(), 0) >= 1:
            continue
        for k in known:
            if tok[0] == k[0] and abs(len(tok) - len(k)) <= 2 and difflib.SequenceMatcher(None, tok, k).ratio() >= 0.84 \
                    and caps[k] >= 3 * n and (tok, k) not in seen:
                seen.add((tok, k))
                add("spelling", "warn", tok, "'%s' (%d×) looks like a misspelling of '%s' (%d×)" % (tok, n, k, caps[k]), where[tok])
    order = {"error": 0, "warn": 1, "info": 2}
    issues.sort(key=lambda i: (order[i["sev"]], i["kind"], i["subject"]))
    return issues


# ---------------------------------------------------------------------------
# Lore terms
# ---------------------------------------------------------------------------
TERM_RX = re.compile(r"(?<![\w-])([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+|[A-Z]{2,5})(?![\w-])")
TERM_STOP = {"OK", "TV", "ID", "HR", "AM", "PM", "US", "UK", "AI", "PC", "II", "III", "IV", "VI", "VII", "DC", "MD", "PDF", "FAQ", "NPC", "HUD", "UI", "FBI", "CEO", "USB",
             "TO", "FWD", "RE", "FYI", "ASAP", "NOT", "AND", "THE", "FOR", "ALL", "NO", "YES", "WHO", "WHY", "HOW", "NOW", "ONE", "TWO", "VS", "ETC", "PS", "NB"}


def lore_terms(corpus):
    lower, _, _ = _vocab(corpus)
    glossary = "\n".join(f["text"] for f in corpus if f["code"] in ("2.02", "2.29"))
    files, uses, first = defaultdict(set), Counter(), {}
    for f in counted(corpus):
        for m in TERM_RX.finditer(f["text"]):
            t = m.group(1)
            if t in TERM_STOP or re.match(r"^[A-Z]-\d+$", t) or re.match(r"^Q\d$", t):
                continue
            if "-" not in t and lower.get(t.lower(), 0) >= 2:
                continue
            files[t].add(f["p"])
            uses[t] += 1
            first.setdefault(t, f["p"])
    out = []
    for t, fs in files.items():
        defined = bool(re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(t), glossary))
        out.append({"term": t, "files": len(fs), "uses": uses[t], "defined": defined, "first": first[t]})
    out.sort(key=lambda r: (-r["files"], -r["uses"], r["term"]))
    return out


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------
CODENAME_NODE = re.compile(r"\b(K-\d+|VAH-3|TOR-\d+|ICS-OP-7)\b")
SURNAME_NODES = {"Akar": r"\bAkar\b", "Ohm": r"\bOhm\b", "Vance": r"\bVance\b", "Castile": r"\bCastile\b", "Brant": r"\bBrant\b"}


GENERIC_NAMES = {"colleague", "unknown", "unknown employee", "his colleague"}


def node_for(name, code):
    if code:
        return code if name.strip().lower() in GENERIC_NAMES or len(name.strip()) < 2 else name
    if "Previous Branch Director" in name:
        return None
    if "Branch Director" in name or "Maren Voss" in name:
        return "Branch Director"
    if re.search(r"Subjugator|\bEOD\b|Executioner of Despair|Envoy of Devotion", name):
        return "EOD"
    for k in SURNAME_NODES:
        if re.search(r"\b%s\b" % k, name):
            return k
    m = CODENAME_NODE.search(name)
    if m:
        return m.group(1)
    return None


def relationships(corpus, people_rows, msg_rows, profile_names):
    """people_rows: (id, code, name, has_profile); msg_rows: (file_id, from_person, to_person)"""
    pmap = {p[0]: p for p in people_rows}
    node_of = {pid: node_for(p[2], p[1]) for pid, p in pmap.items()}
    nodes = {}
    for pid, n in node_of.items():
        if not n:
            continue
        r = nodes.setdefault(n, {"name": n, "codes": set(), "prof": False, "sent": 0, "recv": 0, "files": set()})
        if pmap[pid][1]:
            r["codes"].add(pmap[pid][1])
        r["prof"] = r["prof"] or bool(pmap[pid][3])
    for n in nodes:
        if n in profile_names:
            nodes[n]["prof"] = True
    edges = defaultdict(lambda: {"msgs": 0, "files": set(), "paras": 0, "msg_files": []})
    for fid, a, b in msg_rows:
        na, nb = node_of.get(a), node_of.get(b)
        if na:
            nodes[na]["sent"] += 1
        if nb:
            nodes[nb]["recv"] += 1
        if na and nb and na != nb:
            e = edges[tuple(sorted((na, nb)))]
            e["msgs"] += 1
            e["msg_files"].append(fid)
    # name patterns
    firsts = Counter(n.split()[0] for n in nodes if " " in n and nodes[n]["codes"])
    pats = {}
    for n, r in nodes.items():
        if n == "Branch Director":
            pats[n] = re.compile(r"(?<!Previous )Branch Director|Maren Voss")
        elif n == "EOD":
            pats[n] = re.compile(r"\bEOD\b|Executioner of Despair|Envoy of Devotion|Subjugator")
        elif n in SURNAME_NODES:
            pats[n] = re.compile(SURNAME_NODES[n])
        elif CODENAME_NODE.fullmatch(n):
            pats[n] = re.compile(r"(?<![\w-])%s(?![\w-])" % re.escape(n))
        else:
            parts = [re.escape(n)]
            if " " in n and firsts[n.split()[0]] == 1:
                parts.append(re.escape(n.split()[0]))
            pats[n] = re.compile(r"(?<![\w-])(?:%s)(?![\w'’-])" % "|".join(parts))
    for f in counted(corpus):
        for para in re.split(r"\n\s*\n", f["text"]):
            hit = sorted(n for n, rx in pats.items() if rx.search(para))
            for n in hit:
                nodes[n]["files"].add(f["id"])
            for a, b in combinations(hit, 2):
                e = edges[(a, b)]
                e["paras"] += 1
                e["files"].add(f["id"])
    node_rows = [(n, ", ".join(sorted(r["codes"])), 1 if r["prof"] else 0, r["sent"], r["recv"], len(r["files"])) for n, r in nodes.items()]
    edge_rows = [(a, b, e["msgs"], len(e["files"]), e["paras"]) for (a, b), e in edges.items() if e["msgs"] or e["paras"] >= 2]
    view = {
        "nodes": [{"name": n, "codes": sorted(r["codes"]), "prof": r["prof"], "sent": r["sent"], "recv": r["recv"], "files": len(r["files"])} for n, r in nodes.items()],
        "edges": [{"a": a, "b": b, "msgs": m, "co_files": cf, "paras": p} for a, b, m, cf, p in edge_rows],
    }
    return view, node_rows, edge_rows


# ---------------------------------------------------------------------------
# Exports (Mermaid + Graphviz)
# ---------------------------------------------------------------------------
def _q(s):
    return str(s).replace('"', "'")


def mermaid_er(schema):
    out = ["erDiagram"]
    for t in schema:
        out.append("  %s {" % t["name"])
        for c in t["cols"]:
            key = " PK, FK" if c["pk"] and c["fk"] else " PK" if c["pk"] else " FK" if c["fk"] else ""
            out.append("    %s %s%s" % ((c["t"] or "text").lower(), c["n"], key))
        out.append("  }")
    for t in schema:
        for c in t["cols"]:
            if c["fk"]:
                out.append('  %s }o--|| %s : "%s"' % (t["name"], c["fk"].split(".")[0], c["n"]))
    return "\n".join(out)


def dot_er(schema):
    out = ["digraph ERD {", "  rankdir=LR; node [shape=plaintext fontname=Helvetica];"]
    for t in schema:
        rows = "".join('<TR><TD ALIGN="LEFT">%s%s</TD><TD ALIGN="LEFT"><I>%s</I></TD></TR>' % (
            "PK " if c["pk"] else "FK " if c["fk"] else "", c["n"], (c["t"] or "").lower()) for c in t["cols"])
        out.append('  %s [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0"><TR><TD COLSPAN="2" BGCOLOR="#cfd8ea"><B>%s</B></TD></TR>%s</TABLE>>];' % (t["name"], t["name"], rows))
    for t in schema:
        for c in t["cols"]:
            if c["fk"]:
                out.append('  %s -> %s [label="%s" fontsize=9];' % (t["name"], c["fk"].split(".")[0], c["n"]))
    out.append("}")
    return "\n".join(out)


def mermaid_graph(nodes, edges, direction="LR"):
    """nodes: [(id, label)]; edges: [(a, b, label)]"""
    out = ["flowchart " + direction]
    for i, label in nodes:
        out.append('  %s["%s"]' % (i, _q(label)))
    for a, b, label in edges:
        out.append('  %s -- "%s" --- %s' % (a, _q(label), b) if label else "  %s --- %s" % (a, b))
    return "\n".join(out)


def dot_graph(nodes, edges, directed=False):
    op = "->" if directed else "--"
    out = ["%s G {" % ("digraph" if directed else "graph"), "  node [shape=box style=rounded fontname=Helvetica];"]
    for i, label in nodes:
        out.append('  %s [label="%s"];' % (i, _q(label)))
    for a, b, label in edges:
        out.append('  %s %s %s [label="%s"];' % (a, op, b, _q(label)))
    out.append("}")
    return "\n".join(out)


def build_exports(schema, cats, cat_flow, rel_view, doc_edges):
    ex = []
    ex.append({"name": "database-erd", "title": "Database schema (ERD)", "mermaid": mermaid_er(schema), "dot": dot_er(schema)})
    ids = {k: "c%d" % i for i, k in enumerate(cats)}
    n = [(ids[k], cats[k]["label"]) for k in cats if k in {a for a, _, _ in cat_flow} | {b for _, b, _ in cat_flow}]
    e = [(ids[a], ids[b], str(w)) for a, b, w in cat_flow]
    ex.append({"name": "category-flow", "title": "Which kind of file cites which (explicit refs, ≥5 file pairs)",
               "mermaid": mermaid_graph(n, e).replace(" --- ", " --> "), "dot": dot_graph(n, e, directed=True)})
    nid = {r["name"]: "p%d" % i for i, r in enumerate(rel_view["nodes"])}
    used = {x for ed in rel_view["edges"] for x in (ed["a"], ed["b"])}
    n = [(nid[r["name"]], r["name"] + (" ★" if r["prof"] else "")) for r in rel_view["nodes"] if r["name"] in used]
    e = [(nid[ed["a"]], nid[ed["b"]], ("%d msg" % ed["msgs"]) if ed["msgs"] else "") for ed in rel_view["edges"] if ed["msgs"] or ed["paras"] >= 4]
    ex.append({"name": "character-relationships", "title": "Character relationships (★ = has a profile file)",
               "mermaid": mermaid_graph(n, e), "dot": dot_graph(n, e)})
    dn = sorted({x for a, b in doc_edges for x in (a, b)})
    n = [("d" + x.replace(".", "_"), "Doc " + x) for x in dn]
    e = [("d" + a.replace(".", "_"), "d" + b.replace(".", "_"), "") for a, b in doc_edges]
    ex.append({"name": "document-dependencies", "title": "In-world documents citing each other (2.xx → 2.yy)",
               "mermaid": mermaid_graph(n, e).replace(" --- ", " --> "), "dot": dot_graph(n, e, directed=True)})
    return ex


# ---------------------------------------------------------------------------
# Fact extraction — cross-file claim consistency
# ---------------------------------------------------------------------------
# Each rule: (subject, predicate, pattern, norm_fn_or_None)
# The pattern must have exactly one capture group that gives the value.
# subject / predicate are plain strings used as the key.
# norm_fn is called on the raw captured string to produce a canonical form
# for comparison (e.g. strip whitespace, lowercase, collapse spaces).

def _n(s):
    """Default normaliser: strip, collapse spaces, lowercase."""
    return re.sub(r"\s+", " ", str(s)).strip().lower()


FACT_RULES = [
    # --- Characters: home cities ---
    ("Rania",        "home city",        r"Rania[^.\n|]{0,60}?\bfrom\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|;|\n|$)",  _n),
    ("Tarek",        "home city",        r"Tarek[^.\n|]{0,60}?\bfrom\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|;|\n|$)",  _n),
    ("Kai",          "home city",        r"(?:Kai|E-05682)[^.\n|]{0,60}?\bfrom\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|;|\n|$)", _n),
    ("James",        "home city",        r"James[^.\n|]{0,60}?\bfrom\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|;|\n|$)",  _n),
    # --- Characters: tenure at Branch ---
    ("Rania",        "years at branch",  r"Rania[^.\n|]{0,80}?(\d+)\s+years?\s+at\s+Branch",                 _n),
    ("Tarek",        "years at branch",  r"Tarek[^.\n|]{0,80}?(\d+)\s+years?\s+at\s+Branch",                 _n),
    ("Marcus",       "years at branch",  r"Marcus[^.\n|]{0,80}?(\d+)\s+years?\s+at\s+(?:ICS|Branch)",         _n),
    ("James",        "years at ICS",     r"James[^.\n|]{0,80}?(\d+)\s+years?\s+at\s+ICS",                    _n),
    ("Kai",          "cycles at branch", r"Time at Branch[^:\n]{0,10}:\s*(\d+\s+cycles?(?:\s*,\s*[\d\w\s]+)?)", _n),
    # --- Characters: tiers ---
    ("Rania",        "tier",             r"Rania[^.\n|]{0,80}?\|\s*Tier\s*(\d)",                              _n),
    ("Tarek",        "tier",             r"Tarek[^.\n|]{0,80}?\|\s*Tier\s*(\d)",                              _n),
    ("Marcus",       "tier",             r"(?:E-02847|Marcus)[^.\n|]{0,80}?\|\s*Tier\s*(\d)",                 _n),
    ("Kai",          "tier",             r"(?:E-05682|Kai)[^.\n|]{0,80}?Current Tier[^:\n]{0,5}:\s*Tier\s*(\d)", _n),
    ("James",        "tier",             r"(?:E-00219|James)[^.\n|]{0,80}?\|\s*Tier\s*(\d)",                  _n),
    # --- Supervisor M ---
    ("Supervisor M", "E-code",           r"\bM\b[^.\n|]{0,60}?(?:E-00088|E-04891|E-02847|is Asset )(E-\d{5})|Asset (E-\d{5})[^.\n|]{0,40}?\bM\b", _n),
    ("Supervisor M", "transition cycle", r"M[^.\n|]{0,60}?transitioned?\s+(?:in\s+)?Cycle\s+(\d{3})|Cycle\s+(\d{3})[^.\n|]{0,40}?M\s+was\s+transitioned", _n),
    ("Supervisor M", "gender",           r"M\b[^.\n|]{0,80}?\b(she|he)\b(?:\s+was\s+(?:E-|PTKW|transitioned|indeed|a\s+)|\s+(?:completed|said|went|asked|taught|always|had|made|gave))", _n),
    # --- Canon numbers ---
    ("Schedule D",   "page count",       r"Schedule D[^.\n|]{0,30}?(\d{2,3})[- ]pages?",                      _n),
    ("Facility",     "undeactivated badges", r"\b(\d{3})\s+(?:undeactivated|active\s+)?badges?",              _n),
    ("Inventory",    "slot count",        r"(\d{2}|ten)[- ]slot inventory|inventory[^.\n|]{0,20}?(\d{2}|ten)[- ]slots?", _n),
    ("Earth",        "labor source number", r"Earth[^.\n|]{0,30}?Labor Source\s*#\s*(\d{3})|Labor Source\s*#\s*(\d{3})[^.\n|]{0,20}?Earth", _n),
    ("Earth",        "stage",             r"Stage\s+(\d)\s+of\s+5",                                           _n),
    ("Earth",        "compliance index",  r"[Cc]ompliance[^.\n|%]{0,30}?(\d{2}\.\d)\s*%",                    _n),
    ("Earth",        "resistance index",  r"[Rr]esistance(?:\s+[Ii]ndex)?[^.\n|%]{0,30}?(\d\.\d)\s*%",       _n),
    ("Category Omega", "window hours",   r"Category Omega[^.\n|]{0,60}?(\d{2})[- ]hour|(\d{2})\s*hours?\s+(?:window|clock)", _n),
    ("Category Omega", "release time",   r"Category Omega[^.\n|]{0,60}?(?:release|releases|released)\s+at\s+(\d{2}:\d{2})", _n),
    ("EOD",          "active days start",r"EOD[^.\n|]{0,60}?(?:Day\s*(\d+)|appears?\s+Day\s+(\d+))\s*(?:,\s*morning|morning)?(?:\s+—\s+first)", _n),
    # --- Vantage transmissions ---
    ("Vantage",      "total transmissions", r"(\d{2,3})\s+transmissions?|all\s+(\d{2,3})\s+transmissions?",  _n),
    ("Vantage",      "transmission cadence", r"transmissions?\s+(every\s+two\s+weeks|roughly\s+monthly|monthly|bi-weekly|fortnightly)", _n),
    # --- Stairwell B / Level 0 ---
    ("Stairwell B",  "player arrival day", r"Day\s+(\d{1,2})\s+(?:at\s+)?(?:23:00|02:00)|reaches?\s+the\s+door\s+at[^.\n|]{0,30}?Day\s+(\d{1,2})", _n),
    # --- Previous Branch Director ---
    ("Previous Branch Director", "appointment cycle", r"[Aa]ppointed\s+Cycle\s+(\d{3})|Cycle\s+(\d{3})\s+through\s+\d{3}", _n),
    ("Previous Branch Director", "end cycle",         r"Cycle\s+\d{3}\s+through\s+Cycle\s+(\d{3})|through\s+(\d{3})",       _n),
    # --- In-world document count ---
    ("Documents",    "total count",       r"all\s+(\d{2,3})\s+in-world documents|\(2\.1[–-]2\.(\d{2,3})\)",  _n),
    # --- New employee badge tier ---
    ("New employee", "starting tier",     r"[Nn]ew\s+(?:employees?|arrivals?|hires?)[^.\n|]{0,60}?Tier\s+(\d)|Tier\s+(\d)[^.\n|]{0,40}?(?:new\s+employees?|onboarding|all\s+new)", _n),
    ("New employee", "onboarding badge",  r"[Yy]our\s+Tier\s+(\d)\s+employee\s+badge|badge\s+at\s+onboarding\s+\(Tier\s+(\d)\s+standard\)", _n),
]


def fact_extract(corpus):
    """
    Extract (subject, predicate, value, file_path, line_no) for all FACT_RULES.
    Returns:
      facts:     list of dicts {subject, predicate, value, path, line_no, raw}
      conflicts: list of dicts {subject, predicate, values: [{value, path, line_no}]}
    """
    facts = []
    compiled = []
    for subject, predicate, pattern, norm in FACT_RULES:
        try:
            rx = re.compile(pattern, re.I)
        except re.error:
            continue
        compiled.append((subject, predicate, rx, norm))

    for f in counted(corpus):
        for line_no, line in enumerate(f["text"].splitlines(), 1):
            line_s = line.strip()
            if not line_s:
                continue
            for subject, predicate, rx, norm_fn in compiled:
                for m in rx.finditer(line_s):
                    raw = next((g for g in m.groups() if g is not None), None)
                    if raw is None:
                        continue
                    value = norm_fn(raw.strip()) if norm_fn else raw.strip().lower()
                    # de-duplicate exact same (subject, predicate, value, path, line_no)
                    facts.append({
                        "subject": subject,
                        "predicate": predicate,
                        "value": value,
                        "path": f["p"],
                        "line_no": line_no,
                        "raw": short(line_s, 180),
                    })

    # Group by (subject, predicate) and find conflicts
    from collections import defaultdict as _dd
    groups = _dd(list)
    for fc in facts:
        groups[(fc["subject"], fc["predicate"])].append(fc)

    conflicts = []
    for (subj, pred), entries in sorted(groups.items()):
        # collect distinct values per file (one per file to avoid noise from repetition)
        by_file = _dd(set)
        for e in entries:
            by_file[e["path"]].add(e["value"])
        # flatten: one representative entry per (file, value) pair
        reps = {}
        for e in entries:
            key = (e["path"], e["value"])
            if key not in reps:
                reps[key] = e
        distinct_vals = {e["value"] for e in reps.values()}
        if len(distinct_vals) > 1:
            conflicts.append({
                "subject": subj,
                "predicate": pred,
                "entries": sorted(reps.values(), key=lambda x: (x["value"], x["path"])),
            })

    return facts, conflicts


# ---------------------------------------------------------------------------
# History helpers
# ---------------------------------------------------------------------------
def unified(old, new, name, context=2, cap=220):
    d = list(difflib.unified_diff(old.splitlines(), new.splitlines(), "before/" + name, "after/" + name, n=context, lineterm=""))
    if len(d) > cap:
        d = d[:cap] + ["… (%d more diff lines)" % (len(d) - cap)]
    return "\n".join(d)


def pack(data):
    return zlib.compress(data, 6)


def unpack(blob):
    return zlib.decompress(blob)
