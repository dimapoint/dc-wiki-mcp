"""Refresh pages edited after the dump through the MediaWiki API (honest user agent, >= 1 s between requests).

    uv run python -m dcdb.refresh [--db data/dcdb.sqlite] [--since 2026-09-20T00:00:00Z]

By default it starts where the last refresh (or the dump) ended. On HTTP 402/403/429 it stops without
retrying (project rule). Handles edits, new pages and redirects; deletions and moves wait for the next full
dump (actualizar.sh). MediaWiki keeps recent changes for ~90 days: for older gaps, rebuild from a new dump.
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


def fetch_changes(since, pause=1.0):
    """[{pageid, title, timestamp, content}] of ns-0 pages whose latest revision is at or after `since`."""
    params = {"action": "query", "format": "json", "formatversion": "2", "generator": "recentchanges",
              "grcnamespace": "0", "grcdir": "newer", "grcstart": since, "grctoponly": "1",
              "grctype": "edit|new", "grclimit": "50", "prop": "revisions", "rvprop": "content|timestamp",
              "rvslots": "main"}
    pages, cont, n = {}, {}, 0
    while True:
        if n:
            time.sleep(pause)
        n += 1
        req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params | cont),
                                     headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (402, 403, 429):
                raise Blocked(f"HTTP {e.code} de la API: frenado sin reintentar (regla del proyecto).") from None
            raise
        if "error" in data:
            raise RuntimeError(f"API: {data['error']}")
        for p in data.get("query", {}).get("pages", []):
            rev = (p.get("revisions") or [{}])[0]
            content = rev.get("slots", {}).get("main", {}).get("content")
            if content is not None:
                pages[p["pageid"]] = {"pageid": p["pageid"], "title": p["title"], "timestamp": rev["timestamp"],
                                      "content": content}
        if "continue" not in data or n % 50 == 0:
            print(f"  {n} pedidos a la API, {len(pages)} páginas cambiadas", flush=True)
        if "continue" not in data:
            return list(pages.values())
        cont = data["continue"]


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
    """Replace the given pages (API shape) in the database. Returns (pages updated, redirects updated)."""
    updated = redirects = 0
    for p in pages:
        title = norm_title(p["title"])
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
    return updated, redirects


def refresh(con, since=None, fetch=fetch_changes):
    meta = dict(con.execute("SELECT key, value FROM meta"))
    since = since or meta.get("refreshed_until") or meta["dump_date"]
    pages = fetch(since)
    updated, redirects = apply_pages(con, pages)
    link(con)
    until = max([p["timestamp"] for p in pages], default=since)
    con.execute("INSERT OR REPLACE INTO meta VALUES ('refreshed_until', ?)", (until,))
    con.commit()
    return since, until, updated, redirects


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=ROOT / "data" / "dcdb.sqlite")
    ap.add_argument("--since", help="ISO 8601 (por defecto: fin del último refresco o fecha del dump)")
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    try:
        since, until, updated, redirects = refresh(con, a.since)
    except Blocked as e:
        sys.exit(str(e))
    print(f"{updated} páginas y {redirects} redirecciones actualizadas ({since} → {until})")


if __name__ == "__main__":
    main()
