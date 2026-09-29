"""Refresh pages edited after the dump through the MediaWiki API (honest user agent, >= 1 s between requests).

    uv run python -m dcdb.refresh [--db data/dcdb.sqlite] [--since 2026-09-20T00:00:00Z]

By default it starts where the last refresh (or the dump) ended. On HTTP 402/403/429 it stops without
retrying (project rule). Handles edits, new pages, redirects, deletions, restores and moves (via the delete/move
logs). MediaWiki keeps recent changes for ~90 days: for older gaps, rebuild from a new dump (actualizar.sh).
"""
import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from .ingest import IN_FTS, ROOT, insert_row, link
from .wiki import norm_title, process_page

API = "https://dc.fandom.com/api.php"
USER_AGENT = "dc-wiki-mcp/0.1 (+https://github.com/dimapoint/dc-wiki-mcp)"
REDIRECT_RE = re.compile(r"^\s*#REDIRECT\s*:?\s*\[\[([^\]|#]+)", re.I)


class Blocked(Exception):
    pass


def api_get(params, pause=1.0):
    """One API call, `pause` seconds after the previous one. Raises Blocked on 402/403/429 (no retries)."""
    time.sleep(pause)
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (402, 403, 429):
            raise Blocked(f"HTTP {e.code} de la API: frenado sin reintentar (regla del proyecto).") from None
        raise
    if "error" in data:
        raise RuntimeError(f"API: {data['error']}")
    return data


def add_revisions(pages, data):
    """Collect revisions from a query result into `pages` (keyed by title); missing pages get {"missing": True}."""
    for p in data.get("query", {}).get("pages", []):
        rev = (p.get("revisions") or [{}])[0]
        content = rev.get("slots", {}).get("main", {}).get("content")
        if p.get("missing"):
            pages[p["title"]] = {"title": p["title"], "missing": True}
        elif content is not None:
            pages[p["title"]] = {"pageid": p["pageid"], "title": p["title"], "timestamp": rev["timestamp"],
                                 "content": content}


def fetch_changes(since):
    """[{pageid, title, timestamp, content}] of ns-0 pages changed at or after `since`: edits and new pages
    (recentchanges), plus titles touched by deletes, restores and moves (fetched again by title; a page that no
    longer exists comes back as {"title", "missing": True})."""
    params = {"action": "query", "format": "json", "formatversion": "2", "generator": "recentchanges",
              "grcnamespace": "0", "grcdir": "newer", "grcstart": since, "grctoponly": "1",
              "grctype": "edit|new", "grclimit": "50", "prop": "revisions", "rvprop": "content|timestamp",
              "rvslots": "main"}
    pages, cont, n = {}, {}, 0
    while True:
        n += 1
        data = api_get(params | cont)
        add_revisions(pages, data)
        if "continue" not in data or n % 50 == 0:
            print(f"  {n} pedidos a la API, {len(pages)} páginas cambiadas", flush=True)
        if "continue" not in data:
            break
        cont = data["continue"]
    touched = set()
    for letype in ("delete", "move"):  # logevents takes one type at a time
        cont = {}
        while True:
            data = api_get({"action": "query", "format": "json", "formatversion": "2", "list": "logevents",
                            "letype": letype, "lenamespace": "0", "ledir": "newer", "lestart": since, "lelimit": "500",
                            "leprop": "title|type|details|timestamp"} | cont)
            for e in data["query"]["logevents"]:
                touched.add(e["title"])
                target = (e.get("params") or {}).get("target_title")
                if letype == "move" and target and e["params"].get("target_ns") == 0:
                    touched.add(target)
            if "continue" not in data:
                break
            cont = data["continue"]
    touched = sorted(touched)
    for i in range(0, len(touched), 50):
        add_revisions(pages, api_get({"action": "query", "format": "json", "formatversion": "2",
                                      "titles": "|".join(touched[i:i + 50]), "prop": "revisions",
                                      "rvprop": "content|timestamp", "rvslots": "main"}))
    print(f"  {n} pedidos de cambios, {len(touched)} títulos por borrados/traslados", flush=True)
    return list(pages.values())


def delete_page(con, pid):
    """Remove a page and every row derived from it (FTS included)."""
    title, headline, text, in_fts = con.execute(
        f"SELECT title, headline, plain_text, {IN_FTS} FROM pages WHERE id = ?", (pid,)).fetchone()
    if in_fts:
        con.execute("INSERT INTO pages_fts(pages_fts, rowid, title, headline, plain_text) "
                    "VALUES ('delete', ?, ?, ?, ?)", (pid, title, headline, text))
    for table, col in (("issues", "page_id"), ("credits", "page_id"), ("collection_contents", "collection_page_id"),
                       ("categories", "page_id"), ("transclusions", "page_id")):
        con.execute(f"DELETE FROM {table} WHERE {col} = ?", (pid,))
    con.execute("DELETE FROM event_membership WHERE (member_title = ? AND source != 'event_issues_list') "
                "OR (event_title = ? AND source = 'event_issues_list')", (title, title))
    con.execute("DELETE FROM pages WHERE id = ?", (pid,))


def apply_pages(con, pages):
    """Replace the given pages (API shape) in the database; pages flagged "missing" are removed.
    Returns (pages updated, redirects updated, pages removed)."""
    updated = redirects = removed = 0
    for p in pages:
        title = norm_title(p["title"])
        if p.get("missing"):
            gone = con.execute("SELECT id FROM pages WHERE title = ?", (title,)).fetchall()
            for (old,) in gone:
                delete_page(con, old)
            removed += len(gone) + con.execute("DELETE FROM redirects WHERE from_title = ?", (title,)).rowcount
            continue
        for (old,) in con.execute("SELECT id FROM pages WHERE id = ? OR title = ?", (p["pageid"], title)).fetchall():
            delete_page(con, old)
        m = REDIRECT_RE.match(p["content"])
        if m:
            con.execute("INSERT OR REPLACE INTO redirects VALUES (?, ?)", (title, norm_title(m.group(1))))
            redirects += 1
            continue
        con.execute("DELETE FROM redirects WHERE from_title = ?", (title,))
        insert_row(con, process_page((p["pageid"], title, p["content"], p["timestamp"])))
        con.execute(f"INSERT INTO pages_fts(rowid, title, headline, plain_text) SELECT id, title, headline, "
                    f"plain_text FROM pages WHERE id = ? AND {IN_FTS}", (p["pageid"],))
        updated += 1
    return updated, redirects, removed


def refresh(con, since=None, fetch=fetch_changes):
    meta = dict(con.execute("SELECT key, value FROM meta"))
    since = since or meta.get("refreshed_until") or meta["dump_date"]
    pages = fetch(since)
    updated, redirects, removed = apply_pages(con, pages)
    link(con)
    until = max([p["timestamp"] for p in pages if "timestamp" in p], default=since)
    con.execute("INSERT OR REPLACE INTO meta VALUES ('refreshed_until', ?)", (until,))
    con.commit()
    return since, until, updated, redirects, removed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=ROOT / "data" / "dcdb.sqlite")
    ap.add_argument("--since", help="ISO 8601 (por defecto: fin del último refresco o fecha del dump)")
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    try:
        since, until, updated, redirects, removed = refresh(con, a.since)
    except Blocked as e:
        sys.exit(str(e))
    print(f"{updated} páginas y {redirects} redirecciones actualizadas, {removed} eliminadas ({since} → {until})")


if __name__ == "__main__":
    main()
