"""End to end on a tiny synthetic dump: ingest -> server tools -> refresh (fake API) -> HTTP mode.
Needs neither data/dcdb.sqlite nor the network."""
import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import anyio
import pytest

from dcdb import ingest, refresh, server

ROOT = Path(__file__).resolve().parent.parent


def issue(n, writer, story, extra=""):
    return (f"{{{{DC Database:Comic Template\n| Title = Alpha\n| Volume = 1\n| Issue = {n}\n| Day = 6\n"
            f"| Month = {4 + n}\n| Year = 2020\n| Writer1_1 = {writer}\n| StoryTitle1 = {story}\n}}}}\n{extra}")


PAGES = [  # (ns, id, title, text, redirect target)
    (0, 1, "Big Event", "{{DC Database:Event Template\n| Title = Big Event\n| Issues =\n* {{c|Alpha #1}}\n}}", None),
    (0, 2, "Alpha Vol 1 1", issue(1, "Joe Writer", "The First Story", "{{XO}}"), None),
    (0, 3, "Alpha Vol 1 2", issue(2, "[[Joe Q. Writer]]", "Second", "[[Category:Big Event Crossover]]"), None),
    (0, 4, "Alpha Omnibus (Collected)",
     "{{DC Database:Collected Template\n| IssueList =\n* {{c|Alpha #1}}\n* {{c|Alpha #2}}\n}}", None),
    (0, 5, "Joe Q. Writer", "{{DC Database:Staff Template\n| Name = Joe Q. Writer\n}}", None),
    (0, 7, "Old Event", "#REDIRECT [[Big Event]]", "Big Event"),
    (10, 8, "Template:XO", "'''[[Big Event]] Crossover'''\n{{Crossover|title=Core|body={{c|Alpha #1}}}}", None),
    (828, 9, "Module:StaffCorrection/data", 'return {\n  ["joe writer"] = "Joe Q. Writer",\n}', None),
]


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    d = tmp_path_factory.mktemp("mini")
    xml = ['<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">']
    for ns, pid, title, text, target in PAGES:
        red = f"<redirect title={quoteattr(target)} />" if target else ""
        xml.append(f"<page><title>{escape(title)}</title><ns>{ns}</ns><id>{pid}</id>{red}<revision><id>{pid}0</id>"
                   f"<timestamp>2026-01-0{pid}T00:00:00Z</timestamp><text>{escape(text)}</text></revision></page>")
    (d / "dump.xml").write_text("\n".join(xml + ["</mediawiki>"]), encoding="utf-8")
    ingest.build(d / "dump.xml", d / "mini.sqlite", 1)
    old = server.DB
    server.DB = d / "mini.sqlite"
    yield server.DB
    server.DB = old


def titles(res, key="numeros"):
    return [x["titulo"] for x in res[key]]


def test_ingest(db):
    assert server.creditos("Alpha", 1, "1")["historias"][0]["creditos"]["writer"] == ["Joe Q. Writer"]  # StaffCorrection
    ev = server.evento("Old Event")  # redirect
    assert ev["titulo"] == "Big Event" and titles(ev) == ["Alpha Vol 1 1", "Alpha Vol 1 2"]
    fuentes = {x["titulo"]: x["fuentes"] for x in ev["numeros"]}
    assert set(fuentes["Alpha Vol 1 1"]) == {"event_issues_list", "crossover_template"}
    assert fuentes["Alpha Vol 1 2"] == ["category"]
    assert [x["numero"] for x in server.tomo("Alpha Omnibus")["contenido"]] == ["Alpha Vol 1 1", "Alpha Vol 1 2"]
    assert titles(server.buscar("First Story"), "resultados") == ["Alpha Vol 1 1"]


def test_refresh(db):
    changes = [
        {"pageid": 2, "title": "Alpha Vol 1 1", "timestamp": "2026-02-01T00:00:00Z",
         "content": issue(1, "Jane Doe", "The Rewritten Story", "{{XO}}")},
        {"pageid": 6, "title": "Alpha Vol 1 3", "timestamp": "2026-01-20T00:00:00Z",
         "content": issue(3, "Joe Writer", "Third", "{{XO}}")},
        {"pageid": 3, "title": "Alpha Vol 1 2", "timestamp": "2026-01-15T00:00:00Z",
         "content": "#REDIRECT [[Alpha Vol 1 3]]"},
    ]
    seen = []
    with sqlite3.connect(db) as con:
        res = refresh.refresh(con, fetch=lambda since: seen.append(since) or changes)
        con.execute("INSERT INTO pages_fts(pages_fts) VALUES ('integrity-check')")
    assert seen == ["2026-01-09T00:00:00Z"] and res[1:] == ("2026-02-01T00:00:00Z", 2, 1, 0)
    assert server.creditos("Alpha", 1, "1")["historias"][0]["creditos"]["writer"] == ["Jane Doe"]
    assert titles(server.buscar("Rewritten"), "resultados") == ["Alpha Vol 1 1"]
    assert titles(server.buscar("First Story"), "resultados") == []
    assert titles(server.evento("Big Event")) == ["Alpha Vol 1 1", "Alpha Vol 1 3"]
    assert [x["numero"] for x in server.tomo("Alpha Omnibus")["contenido"]] == ["Alpha Vol 1 1", "Alpha Vol 1 3"]
    assert [x["titulo"] for x in server.run_de_autor("Joe Writer")["numeros"]] == ["Alpha Vol 1 3"]
    assert server.info_dump()["refreshed_until"] == "2026-02-01T00:00:00Z"


def test_refresh_removals(db):
    changes = [{"title": "Alpha Vol 1 3", "missing": True}, {"title": "Alpha Vol 1 2", "missing": True},
               {"pageid": 10, "title": "Alpha Vol 1 4", "timestamp": "2026-03-01T00:00:00Z",
                "content": issue(4, "Joe Writer", "Fourth", "{{XO}}")}]
    with sqlite3.connect(db) as con:
        res = refresh.refresh(con, fetch=lambda since: changes)
        con.execute("INSERT INTO pages_fts(pages_fts) VALUES ('integrity-check')")
        assert con.execute("SELECT count(*) FROM redirects WHERE from_title = 'Alpha Vol 1 2'").fetchone() == (0,)
    assert res[1:] == ("2026-03-01T00:00:00Z", 1, 0, 2)
    assert titles(server.evento("Big Event")) == ["Alpha Vol 1 1", "Alpha Vol 1 4"]
    assert titles(server.buscar("Alpha Vol 1 3"), "resultados") == []
    assert titles(server.buscar("Fourth"), "resultados") == ["Alpha Vol 1 4"]


def test_rate_limit():
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    guard, statuses = server.Guard(app, per_minute=2), []

    async def run():
        for ip in ("1.2.3.4", "1.2.3.4", "1.2.3.4", "5.6.7.8"):
            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}

            async def send(m, ip=ip):
                if m["type"] == "http.response.start":
                    statuses.append((ip, m["status"]))
            await guard({"type": "http", "method": "POST", "client": (ip, 1)}, receive, send)

    anyio.run(run)
    assert statuses == [("1.2.3.4", 200), ("1.2.3.4", 200), ("1.2.3.4", 429), ("5.6.7.8", 200)]
    assert server.anon("203.0.113.77") == "203.0.113.0" and server.anon("2001:db8:1:2::5") == "2001:db8:1::"


def test_http_mode(db):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    env = os.environ | {"DCDB_PATH": str(db), "DCDB_ALLOWED_HOSTS": "dc.example.com"}
    proc = subprocess.Popen([sys.executable, "-m", "dcdb.server", "--http", "--port", str(port)], cwd=ROOT,
                            env=env, stderr=subprocess.PIPE, text=True)
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        for _ in range(100):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)

        from mcp.client.session import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        async def run():
            async with streamable_http_client(url) as (r, w), ClientSession(r, w) as session:
                await session.initialize()
                res = await session.call_tool("creditos", {"series": "Alpha", "volume": 1, "number": "1"})
                return json.loads(res.content[0].text)

        assert anyio.run(run)["titulo"] == "Alpha Vol 1 1"

        init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        def post(host):
            req = urllib.request.Request(url, init.encode(), {"Host": host, "Content-Type": "application/json",
                                                              "Accept": "application/json, text/event-stream"})
            try:
                return opener.open(req, timeout=10).status
            except urllib.error.HTTPError as e:
                return e.code

        assert post("dc.example.com") == 200
        assert post("evil.example") in (400, 403, 421)
    finally:
        proc.terminate()
        logs = proc.communicate(timeout=10)[1]
    assert "127.0.0.0 POST tools/call:creditos 200" in logs, logs
    assert "Alpha" not in logs  # arguments are never logged
