"""Build data/dcdb.sqlite from the DC Database XML dump (streaming, multiprocess).

    uv run python -m dcdb.ingest [--dump data/raw/endcdatabase_pages_current.xml] [--db data/dcdb.sqlite]
"""
import argparse
import json
import os
import re
import sqlite3
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

from .wiki import crossover_candidates, norm_title, process_page

ROOT = Path(__file__).resolve().parent.parent
NS = "{http://www.mediawiki.org/xml/export-0.11/}"

SCHEMA = """
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE pages(
    id INTEGER PRIMARY KEY, title TEXT NOT NULL UNIQUE, url TEXT NOT NULL, namespace INTEGER NOT NULL,
    kind TEXT NOT NULL, template TEXT, wikitext TEXT, plain_text TEXT, updated_at TEXT, fields TEXT,
    headline TEXT);
CREATE TABLE issues(
    page_id INTEGER PRIMARY KEY REFERENCES pages(id), series TEXT, volume INTEGER, number TEXT,
    series_page TEXT, cover_date TEXT, pub_date TEXT, pub_date_source TEXT, num_sort REAL, story_titles TEXT);
CREATE TABLE credits(
    page_id INTEGER NOT NULL REFERENCES pages(id), story_index INTEGER NOT NULL, role TEXT NOT NULL,
    order_index INTEGER, raw TEXT, person TEXT NOT NULL);
CREATE TABLE collection_contents(
    collection_page_id INTEGER NOT NULL REFERENCES pages(id), issue_title TEXT NOT NULL, story_title TEXT,
    section TEXT, order_index INTEGER NOT NULL, issue_page_id INTEGER REFERENCES pages(id));
CREATE TABLE event_membership(
    event_title TEXT NOT NULL, member_title TEXT NOT NULL, source TEXT NOT NULL, order_index INTEGER,
    section TEXT, event_page_id INTEGER REFERENCES pages(id), page_id INTEGER REFERENCES pages(id));
CREATE TABLE categories(page_id INTEGER NOT NULL REFERENCES pages(id), category TEXT NOT NULL);
CREATE TABLE redirects(from_title TEXT PRIMARY KEY, to_title TEXT NOT NULL);
CREATE TABLE staff_aliases(alias TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE transclusions(page_id INTEGER NOT NULL REFERENCES pages(id), template TEXT NOT NULL);
CREATE TABLE crossover_templates(template TEXT PRIMARY KEY, event_title TEXT NOT NULL);
"""

# Gallery subpages ("X/Gallery") are image captions only: kept in pages, left out of search.
IN_FTS = "template IS NOT 'Gallery Template'"

INDEXES = f"""
CREATE INDEX pages_kind ON pages(kind);
CREATE INDEX pages_title_nocase ON pages(title COLLATE NOCASE);
CREATE INDEX issues_key ON issues(series COLLATE NOCASE, volume, number);
CREATE INDEX issues_series_page ON issues(series_page COLLATE NOCASE);
CREATE INDEX credits_page ON credits(page_id);
CREATE INDEX credits_person ON credits(person COLLATE NOCASE, role);
CREATE INDEX contents_coll ON collection_contents(collection_page_id, order_index);
CREATE INDEX contents_issue ON collection_contents(issue_page_id);
CREATE INDEX members_event ON event_membership(event_page_id);
CREATE INDEX members_page ON event_membership(page_id);
CREATE INDEX members_member_title ON event_membership(member_title);
CREATE INDEX members_event_title ON event_membership(event_title);
CREATE INDEX categories_page ON categories(page_id);
CREATE INDEX categories_cat ON categories(category);
CREATE INDEX transclusions_page ON transclusions(page_id);
CREATE INDEX redirects_nocase ON redirects(from_title COLLATE NOCASE);
CREATE VIRTUAL TABLE pages_fts USING fts5(title, headline, plain_text, content='pages', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2');
INSERT INTO pages_fts(rowid, title, headline, plain_text)
    SELECT id, title, headline, plain_text FROM pages WHERE {IN_FTS};
"""


def read_dump(path, stats):
    """Yield (id, title, text, timestamp) for ns-0 content pages; collect redirects and side data."""
    context = ET.iterparse(path, events=("start", "end"))
    _, root = next(context)
    for ev, el in context:
        if ev != "end" or el.tag != NS + "page":
            continue
        ns, title = el.findtext(NS + "ns"), el.findtext(NS + "title")
        rev = el.find(NS + "revision")
        ts, text = rev.findtext(NS + "timestamp"), rev.findtext(NS + "text") or ""
        stats["pages"] += 1
        stats["max_ts"] = max(stats["max_ts"], ts)
        redirect = el.find(NS + "redirect")
        if ns == "0":
            if redirect is not None:
                stats["redirects"].append((title, norm_title(redirect.get("title"))))
            else:
                yield int(el.findtext(NS + "id")), title, text, ts
        elif ns == "10":
            name = norm_title(title.split(":", 1)[1])
            if redirect is not None:
                stats["tpl_redirects"][name] = norm_title(redirect.get("title").split(":", 1)[-1])
            else:
                stats["templates"][name] = text
        elif title == "Module:StaffCorrection/data":
            stats["staff_module"] = text
        root.clear()


def staff_map(lua):
    """Module:StaffCorrection/data ('["tony daniel"] = "Tony S. Daniel",') -> {alias_lower: name}."""
    unq = lambda s: s.replace('\\"', '"').replace("\\\\", "\\")
    pairs = re.findall(r'\[\s*"((?:[^"\\]|\\.)*)"\s*\]\s*=\s*"((?:[^"\\]|\\.)*)"', lua or "")
    return {unq(a).lower(): unq(b) for a, b in pairs}


class Resolver:
    """Title -> (page_id, canonical title) following redirects (MediaWiki first-letter case rules)."""

    def __init__(self, con):
        self.ids = dict(con.execute("SELECT title, id FROM pages"))
        self.redir = dict(con.execute("SELECT from_title, to_title FROM redirects"))
        self.kinds = dict(con.execute("SELECT id, kind FROM pages"))
        self.lower = {}
        for t in list(self.ids) + list(self.redir):
            self.lower.setdefault(t.lower(), t)

    def __call__(self, title):
        t = norm_title(title)
        if t not in self.ids and t not in self.redir:
            t = self.lower.get(t.lower(), t)
        for _ in range(5):
            if t in self.ids:
                return self.ids[t], t
            if t not in self.redir:
                break
            t = self.redir[t]
        return None, t

    def event(self, candidates):
        """First candidate title that is an event/storyline page, or None."""
        for c in candidates:
            pid, t = self(c)
            if self.kinds.get(pid) == "event":
                return t
        return None


def insert_row(con, r):
    """Rows of one processed page (see wiki.process_page); FTS is filled separately."""
    pid = r["page"][0]
    con.execute("INSERT INTO pages VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (*r["page"], json.dumps(r["fields"], ensure_ascii=False), "\n".join(r["headline"])))
    if r["issue"]:
        con.execute("INSERT INTO issues VALUES (?,?,?,?,?,?,?,?,?,?)", r["issue"])
    con.executemany("INSERT INTO credits VALUES (?,?,?,?,?,?)", r["credits"])
    con.executemany("INSERT INTO collection_contents VALUES (?,?,?,?,?,NULL)", r["contents"])
    con.executemany("INSERT INTO event_membership VALUES (?,?,?,?,?,NULL,NULL)", r["members"])
    con.executemany("INSERT INTO categories VALUES (?,?)", [(pid, c) for c in r["categories"]])
    con.executemany("INSERT INTO transclusions VALUES (?,?)", [(pid, t) for t in r["templates"]])


def crossover_map(con, stats, resolve):
    """{template: event title} for the navbox templates used on issue pages that point to an event page."""
    out = {}
    for (name,) in con.execute("SELECT DISTINCT template FROM transclusions").fetchall():
        src = name
        for _ in range(3):
            src = stats["tpl_redirects"].get(src, src)
        text = stats["templates"].get(src)
        event = text and resolve.event(crossover_candidates(src, text))
        if event:
            out[name] = event
    return out


def link(con, resolve=None):
    """Derived links over the whole database; idempotent, so refresh.py reuses it after updating pages."""
    resolve = resolve or Resolver(con)

    rows = con.execute("SELECT rowid, issue_title FROM collection_contents").fetchall()
    con.executemany("UPDATE collection_contents SET issue_page_id = ? WHERE rowid = ?",
                    [(resolve(t)[0], r) for r, t in rows])

    # Crossover navboxes on issue pages and hand-written "X Crossover" categories.
    con.execute("DELETE FROM event_membership WHERE source IN ('crossover_template', 'category')")
    new = set(con.execute(
        "SELECT x.event_title, p.title, 'crossover_template' FROM transclusions t "
        "JOIN crossover_templates x ON x.template = t.template JOIN pages p ON p.id = t.page_id"))
    for title, cat in con.execute("SELECT p.title, c.category FROM categories c JOIN pages p ON p.id = c.page_id "
                                  "WHERE p.kind = 'issue' AND c.category LIKE '% Crossover%'").fetchall():
        m = re.fullmatch(r"(.+) Crossovers?", cat)
        event = m and resolve.event([m.group(1)])
        if event:
            new.add((event, title, "category"))
    con.executemany("INSERT INTO event_membership VALUES (?,?,?,NULL,NULL,NULL,NULL)", new)

    rows = con.execute("SELECT rowid, event_title, member_title, source FROM event_membership").fetchall()
    updates, drop = [], []
    for r, ev, member, source in rows:
        eid, _ = resolve(ev)
        mid, _ = resolve(member)
        # StoryTitle links point to lots of things; only links to event/storyline pages mean membership.
        if source == "story_title_link" and resolve.kinds.get(eid) != "event":
            drop.append((r,))
        else:
            updates.append((eid, mid, r))
    con.executemany("UPDATE event_membership SET event_page_id = ?, page_id = ? WHERE rowid = ?", updates)
    con.executemany("DELETE FROM event_membership WHERE rowid = ?", drop)

    # Credit names: the wiki's own StaffCorrection table, then redirects ("Tony Daniel" -> "Tony S. Daniel").
    staff = dict(con.execute("SELECT alias, name FROM staff_aliases"))
    rename = []
    for (name,) in con.execute("SELECT DISTINCT person FROM credits").fetchall():
        fixed = staff.get(name.lower(), name)
        pid, canon = resolve(fixed)
        fixed = canon if pid else fixed
        if fixed != name:
            rename.append((fixed, name))
    con.executemany("UPDATE credits SET person = ? WHERE person = ?", rename)


def build(dump, db, workers):
    t0 = time.time()
    tmp = Path(str(db) + ".tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; PRAGMA cache_size=-512000;" + SCHEMA)
    stats = {"pages": 0, "max_ts": "", "redirects": [], "templates": {}, "tpl_redirects": {}}
    n = 0
    with Pool(workers) as pool:
        for r in pool.imap(process_page, read_dump(dump, stats), chunksize=32):
            insert_row(con, r)
            n += 1
            if n % 20000 == 0:
                print(f"  {n:,} pages ({time.time() - t0:.0f}s)", flush=True)
    print(f"parsed {n:,} content pages, {len(stats['redirects']):,} redirects ({time.time() - t0:.0f}s)")
    con.executemany("INSERT OR IGNORE INTO redirects VALUES (?, ?)", stats["redirects"])
    con.executemany("INSERT INTO staff_aliases VALUES (?, ?)", staff_map(stats.get("staff_module")).items())
    resolve = Resolver(con)
    con.executemany("INSERT INTO crossover_templates VALUES (?, ?)", crossover_map(con, stats, resolve).items())
    link(con, resolve)
    con.executescript(INDEXES)
    meta = {
        "dump_file": Path(dump).name,
        "dump_date": stats["max_ts"],
        "dump_pages_total": stats["pages"],
        "content_pages": n,
        "redirects": len(stats["redirects"]),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "https://dc.fandom.com (DC Database)",
        "license": "CC BY-SA 3.0 — https://www.fandom.com/licensing",
    }
    con.executemany("INSERT INTO meta VALUES (?, ?)", [(k, str(v)) for k, v in meta.items()])
    con.execute("ANALYZE")
    con.commit()
    con.close()
    os.replace(tmp, db)
    print(f"done: {db} ({Path(db).stat().st_size / 1e9:.2f} GB, {time.time() - t0:.0f}s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dump", default=ROOT / "data" / "raw" / "endcdatabase_pages_current.xml")
    ap.add_argument("--db", default=ROOT / "data" / "dcdb.sqlite")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    a = ap.parse_args()
    build(a.dump, a.db, a.workers)


if __name__ == "__main__":
    main()
