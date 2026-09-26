"""MCP server over data/dcdb.sqlite: read-only queries of the DC Database dump.

    uv run python -m dcdb.server                                   # stdio (Claude Desktop / Claude Code)
    uv run python -m dcdb.server --http [--port 8000] [--rate 60]  # Streamable HTTP at /mcp (claude.ai)

In HTTP mode, behind an HTTPS proxy, set DCDB_ALLOWED_HOSTS=your.domain (Host header check of the MCP SDK).
"""
import argparse
import ipaddress
import json
import logging
import os
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from .wiki import _int, fmt_date, norm_title, parse_month

DB = Path(os.environ.get("DCDB_PATH", Path(__file__).resolve().parent.parent / "data" / "dcdb.sqlite"))
LICENCIA = ("Contenido del DC Database (https://dc.fandom.com), licencia CC BY-SA 3.0. "
            "Al reutilizarlo, atribuí con la url de cada página.")
RO = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False)
FUENTE_FECHA = {
    "day": "día de salida (Day) con mes = mes de tapa − 2 (regla de la plantilla del wiki)",
    "pub_fields": "campos Pubmonth/Pubyear del wiki",
    "release_date": "campo ReleaseDate del wiki",
    "digital": "fecha de salida digital",
    "estimated": "estimada: mes de tapa − 2 (el wiki no da el día)",
}
ROLES = {
    "guion": "writer", "guionista": "writer", "escritor": "writer", "lapiz": "penciler", "lápiz": "penciler",
    "dibujante": "penciler", "penciller": "penciler", "tinta": "inker", "entintador": "inker",
    "color": "colorist", "colorista": "colorist", "colourist": "colorist", "rotulacion": "letterer",
    "rotulación": "letterer", "rotulista": "letterer", "portada": "cover_artist", "tapa": "cover_artist",
}
KINDS = ("issue", "collection", "event", "series", "character", "staff", "other")

mcp = MCPServer(
    "dc-database",
    instructions=(
        "Copia local del DC Database (dc.fandom.com) a partir de su dump oficial. Usá estas herramientas para "
        "números, créditos, fechas, tomos recopilatorios y eventos. Todas las respuestas traen la url de origen: "
        "citala al usar los datos (licencia CC BY-SA). Consultá info_dump() para saber la fecha del dump."
    ),
)


def connect():
    if not DB.exists():
        raise RuntimeError(f"No existe {DB}. Generala con: uv run python -m dcdb.ingest")
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def resolve(con, title):
    """Title -> (page row, redirected_from). Follows redirects; case-insensitive fallback."""
    orig = t = norm_title(title)
    for nocase in ("", " COLLATE NOCASE"):
        t = orig
        for _ in range(5):
            row = con.execute(f"SELECT * FROM pages WHERE title = ?{nocase}", (t,)).fetchone()
            if row:
                return row, (orig if orig != row["title"] else None)
            r = con.execute(f"SELECT to_title FROM redirects WHERE from_title = ?{nocase}", (t,)).fetchone()
            if not r:
                break
            t = r[0]
    return None, None


def not_found(con, what, query, kind=None):
    return {"error": f"No encontré {what}: {query!r}", "sugerencias": _search(con, query, kind, 5)[0]}


def fts_query(query):
    terms = re.findall(r'"[^"]+"|\S+', query)
    return " ".join('"' + t.strip('"').replace('"', '""') + '"' for t in terms if t.strip('"'))


def _search(con, query, kind, limit, per_series=3):
    """FTS ranked by bm25 (title > headline > text). Without a kind filter, at most `per_series` issues of the
    same series are shown so one long run doesn't bury everything else; the rest are counted, not hidden."""
    q = fts_query(query)
    if not q:
        return [], {}
    sql = ("SELECT p.title, p.kind, p.url, i.series_page, snippet(pages_fts, 2, '«', '»', '…', 24) AS fragmento "
           "FROM pages_fts JOIN pages p ON p.id = pages_fts.rowid LEFT JOIN issues i ON i.page_id = p.id "
           "WHERE pages_fts MATCH ?")
    args = [q]
    if kind:
        sql += " AND p.kind = ?"
        args.append(kind)
    sql += " ORDER BY bm25(pages_fts, 10.0, 5.0, 1.0) LIMIT ?"
    # ponytail: diversity window is 10x limit; a series with more hits beyond it just isn't counted.
    rows = con.execute(sql, (*args, limit if kind else limit * 10)).fetchall()
    out, seen, omitted = [], {}, {}
    for r in rows:
        s = r["series_page"]
        if s and not kind:
            seen[s] = seen.get(s, 0) + 1
            if seen[s] > per_series:
                omitted[s] = omitted.get(s, 0) + 1
                continue
        if len(out) < limit:
            out.append({"titulo": r["title"], "tipo": r["kind"], "fragmento": r["fragmento"], "url": r["url"]})
    return out, omitted


def find_issue(con, series, volume, number):
    series = series.strip()
    m = re.match(r"^(.*) Vol (\d+)$", series)
    if m and not volume:
        series, volume = m.group(1), int(m.group(2))
    volume = int(volume or 1)
    number = str(number).strip().lstrip("#").strip()
    row = con.execute(
        "SELECT p.*, i.* FROM issues i JOIN pages p ON p.id = i.page_id "
        "WHERE i.series = ? COLLATE NOCASE AND i.volume = ? AND i.number = ? COLLATE NOCASE "
        "ORDER BY p.title LIKE '%(Digital)'", (series, volume, number)).fetchone()
    if row:
        return row
    page, _ = resolve(con, f"{series} Vol {volume} {number}")
    if page and page["kind"] == "issue":
        return con.execute("SELECT p.*, i.* FROM issues i JOIN pages p ON p.id = i.page_id WHERE p.id = ?",
                           (page["id"],)).fetchone()
    return None


def _credits(con, issue):
    """Credits grouped by story; story 0 = cover / whole issue."""
    titles = {s["index"]: s["title"] for s in json.loads(issue["story_titles"] or "[]")}
    stories = {i: {} for i in titles}
    general = {}
    for r in con.execute("SELECT story_index, role, person FROM credits WHERE page_id = ? "
                         "ORDER BY story_index, order_index", (issue["page_id"],)):
        target = general if r["story_index"] == 0 else stories.setdefault(r["story_index"], {})
        people = target.setdefault(r["role"], [])
        if r["person"] not in people:
            people.append(r["person"])
    return {
        "historias": [{"indice": i, "titulo": titles.get(i), "creditos": stories[i]} for i in sorted(stories)],
        "portada_y_generales": general,
    }


def _issue_header(issue):
    return {
        "titulo": issue["title"], "url": issue["url"], "serie": issue["series"], "volumen": issue["volume"],
        "numero": issue["number"], "fecha_tapa": issue["cover_date"], "fecha_publicacion": issue["pub_date"],
        "fuente_fecha": FUENTE_FECHA.get(issue["pub_date_source"]),
    }


def _issue_detail(con, issue):
    out = _issue_header(issue) | _credits(con, issue)
    tomos = {r["title"]: {"titulo": r["title"], "url": r["url"], "fuente": "lista de contenido del tomo"}
             for r in con.execute(
                 "SELECT DISTINCT p.title, p.url FROM collection_contents c JOIN pages p "
                 "ON p.id = c.collection_page_id WHERE c.issue_page_id = ? ORDER BY p.title", (issue["page_id"],))}
    for ref in re.findall(r"\{\{\s*[Cc]o\s*\|\s*([^|}]+)", issue["wikitext"] or ""):
        page, _ = resolve(con, ref)
        if page and page["kind"] == "collection" and page["title"] not in tomos:
            tomos[page["title"]] = {"titulo": page["title"], "url": page["url"], "fuente": "notas del número"}
    out["reimpreso_en"] = list(tomos.values())
    eventos = {}
    for r in con.execute(
            "SELECT m.event_title, m.source, p.title, p.url FROM event_membership m "
            "LEFT JOIN pages p ON p.id = m.event_page_id WHERE m.page_id = ?", (issue["page_id"],)):
        key = r["title"] or r["event_title"]
        e = eventos.setdefault(key, {"titulo": key, "url": r["url"], "fuentes": []})
        if r["source"] not in e["fuentes"]:
            e["fuentes"].append(r["source"])
    out["eventos"] = list(eventos.values())
    return out


@mcp.tool(annotations=RO)
def buscar(query: str, kind: str | None = None, limit: int = 20) -> dict:
    """Búsqueda de texto completo (título, títulos de historias/alias y texto) en el DC Database local.
    kind opcional: issue, collection, event, series, character, staff, other.
    Devuelve título, tipo, fragmento y url de cada resultado. Sin kind, muestra hasta 3 números por serie y
    cuenta el resto en `mas_numeros_de_la_serie` (para verlos todos: kind="issue")."""
    if kind and kind not in KINDS:
        return {"error": f"kind inválido: {kind!r}", "kinds_validos": list(KINDS)}
    with closing(connect()) as con:
        res, omitted = _search(con, query, kind, max(1, min(limit, 100)))
        out = {"resultados": res}
        if omitted:
            out["mas_numeros_de_la_serie"] = omitted
        return out | {"licencia": LICENCIA}


@mcp.tool(annotations=RO)
def leer_pagina(title: str, max_chars: int = 20000) -> dict:
    """Lee una página por título (resuelve redirecciones): texto limpio + campos estructurados
    (para números: fechas, créditos, tomos y eventos; para tomos: contenido; para eventos: números)."""
    with closing(connect()) as con:
        page, redirected = resolve(con, title)
        if not page:
            return not_found(con, "la página", title)
        text, max_chars = page["plain_text"] or "", max(0, max_chars)
        out = {"titulo": page["title"], "url": page["url"], "tipo": page["kind"], "plantilla": page["template"],
               "redirigido_desde": redirected, "campos": json.loads(page["fields"] or "{}")}
        if page["kind"] == "issue":
            issue = con.execute("SELECT p.*, i.* FROM issues i JOIN pages p ON p.id = i.page_id WHERE p.id = ?",
                                (page["id"],)).fetchone()
            out["numero"] = _issue_detail(con, issue)
        elif page["kind"] == "collection":
            out["contenido"] = _collection(con, page)["contenido"]
        elif page["kind"] == "event":
            out["numeros"] = _event(con, page, 200)["numeros"]
        out |= {"texto": text[:max_chars], "truncado": len(text) > max_chars, "licencia": LICENCIA}
        return out


@mcp.tool(annotations=RO)
def numero(series: str, volume: int, number: str) -> dict:
    """Un número suelto, p. ej. numero("Batman", 1, "676"): fechas de tapa y de publicación, títulos de las
    historias, créditos por historia, tomos donde se reimprime y eventos a los que pertenece."""
    with closing(connect()) as con:
        issue = find_issue(con, series, volume, number)
        if not issue:
            return not_found(con, "el número", f"{series} Vol {volume} {number}")
        return _issue_detail(con, issue) | {"licencia": LICENCIA}


@mcp.tool(annotations=RO)
def creditos(series: str, volume: int, number: str) -> dict:
    """Créditos de un número por historia (writer, penciler, inker, colorist, letterer, editor) más
    portada/variantes y editor ejecutivo. Ej.: creditos("Batman", 1, "676")."""
    with closing(connect()) as con:
        issue = find_issue(con, series, volume, number)
        if not issue:
            return not_found(con, "el número", f"{series} Vol {volume} {number}")
        return ({"titulo": issue["title"], "url": issue["url"]} | _credits(con, issue) | {"licencia": LICENCIA})


def _collection(con, page):
    f = json.loads(page["fields"] or "{}")
    rows = con.execute(
        "SELECT c.order_index, c.issue_title, c.story_title, c.section, p.title, p.url, i.pub_date "
        "FROM collection_contents c LEFT JOIN pages p ON p.id = c.issue_page_id "
        "LEFT JOIN issues i ON i.page_id = c.issue_page_id WHERE c.collection_page_id = ? "
        "ORDER BY c.order_index", (page["id"],)).fetchall()
    return {
        "titulo": page["title"], "url": page["url"],
        "fecha": fmt_date(_int(f.get("Year", ""), 1000, 2999), parse_month(f.get("Month", "")),
                          _int(f.get("Day", ""), 1, 31)),
        "isbn": f.get("ISBN"), "arcos": f.get("StoryArcs"),
        "contenido": [{"orden": r["order_index"], "numero": r["title"] or r["issue_title"], "url": r["url"],
                       "historia": r["story_title"], "seccion": r["section"], "fecha_publicacion": r["pub_date"]}
                      for r in rows],
    }


@mcp.tool(annotations=RO)
def tomo(title: str) -> dict:
    """Tomo recopilatorio (TPB/HC/ómnibus): lista ordenada de los números que recopila, con título de
    historia y url. Ej.: tomo("Final Crisis New Edition (Collected)"). Se puede omitir " (Collected)"."""
    with closing(connect()) as con:
        page, _ = resolve(con, title)
        if not page or page["kind"] != "collection":
            alt, _ = resolve(con, f"{title} (Collected)")
            page = alt if alt and alt["kind"] == "collection" else page
        if not page:
            return not_found(con, "el tomo", title, "collection")
        if page["kind"] != "collection":
            return not_found(con, "el tomo", title, "collection") | {
                "error": f"{page['title']!r} no es un tomo (tipo: {page['kind']})", "url": page["url"]}
        return _collection(con, page) | {"licencia": LICENCIA}


def _event(con, page, limit):
    rows = con.execute(
        "SELECT p.id, p.title, p.url, p.kind, i.pub_date, i.cover_date, i.num_sort, m.source, m.order_index, "
        "m.section FROM event_membership m JOIN pages p ON p.id = m.page_id "
        "LEFT JOIN issues i ON i.page_id = p.id WHERE m.event_page_id = ? AND p.id != ?",
        (page["id"], page["id"])).fetchall()
    items = {}
    for r in rows:
        it = items.setdefault(r["id"], {"titulo": r["title"], "url": r["url"], "tipo": r["kind"],
                                        "fecha_publicacion": r["pub_date"], "fecha_tapa": r["cover_date"],
                                        "orden_en_lista": None, "seccion": None, "fuentes": [], "_n": r["num_sort"]})
        if r["source"] not in it["fuentes"]:
            it["fuentes"].append(r["source"])
        if r["order_index"] and not it["orden_en_lista"]:
            it["orden_en_lista"], it["seccion"] = r["order_index"], r["section"]
    key = lambda x: (x["fecha_publicacion"] is None, x["fecha_publicacion"] or "", x["titulo"].split(" Vol ")[0],
                     x["_n"] or 0)
    issues = sorted((x for x in items.values() if x["tipo"] == "issue"), key=key)
    for x in items.values():
        x.pop("_n")
    others = [x for x in items.values() if x["tipo"] != "issue"]
    return {"titulo": page["title"], "url": page["url"], "total_numeros": len(issues),
            "numeros": issues[:limit], "truncado": len(issues) > limit,
            "tomos": [x for x in others if x["tipo"] == "collection"],
            "otras_paginas": [x for x in others if x["tipo"] != "collection"]}


@mcp.tool(annotations=RO)
def evento(title: str, limit: int = 500) -> dict:
    """Evento, crossover o arco (p. ej. "Final Crisis", "Batman R.I.P."): números que lo integran ordenados por
    fecha de publicación, con la fuente de cada vínculo (parámetro Event del número, lista del evento, enlace
    del título de la historia, plantilla de crossover del número, categoría "X Crossover") y tomos asociados."""
    with closing(connect()) as con:
        page, _ = resolve(con, title)
        if not page:
            return not_found(con, "el evento", title, "event")
        out = _event(con, page, max(1, limit))
        if page["kind"] != "event" and not (out["numeros"] or out["tomos"] or out["otras_paginas"]):
            return not_found(con, "el evento", title, "event") | {
                "error": f"{page['title']!r} no es un evento (tipo: {page['kind']})", "url": page["url"]}
        return out | {"licencia": LICENCIA}


def canonical_person(con, person):
    name = person.strip()
    alias = con.execute("SELECT name FROM staff_aliases WHERE alias = ?", (name.lower(),)).fetchone()
    name = alias[0] if alias else name
    page, _ = resolve(con, name)
    if page and con.execute("SELECT 1 FROM credits WHERE person = ? LIMIT 1", (page["title"],)).fetchone():
        return page["title"], page["url"]
    row = con.execute("SELECT person FROM credits WHERE person = ? COLLATE NOCASE LIMIT 1", (name,)).fetchone()
    return (row[0] if row else name), (page["url"] if page else None)


@mcp.tool(annotations=RO)
def run_de_autor(person: str, role: str = "writer", series: str | None = None, limit: int = 1000) -> dict:
    """Números de un autor ordenados por fecha de publicación. role: writer, penciler, inker, colorist,
    letterer, editor, cover_artist (o "any" para cualquiera). series opcional: "Batman Vol 3" (un volumen)
    o "Batman" (todos los volúmenes). Ej.: run_de_autor("Chip Zdarsky", "writer", "Batman Vol 3")."""
    if not person.strip():
        return {"error": "Falta el nombre de la persona"}
    with closing(connect()) as con:
        name, url = canonical_person(con, person)
        role = ROLES.get(role.strip().lower(), role.strip().lower()) if role else "any"
        sql = ("SELECT p.title, p.url, i.number, i.pub_date, i.cover_date, i.story_titles, "
               "group_concat(DISTINCT c.story_index) AS stories, group_concat(DISTINCT c.role) AS roles "
               "FROM credits c JOIN issues i ON i.page_id = c.page_id JOIN pages p ON p.id = c.page_id "
               "WHERE c.person = ?")
        args = [name]
        if role not in ("any", "cualquiera", "*"):
            sql += " AND c.role = ?"
            args.append(role)
        if series:
            m = re.match(r"^(.*) Vol (\d+)$", series.strip())
            sql += " AND i.series_page = ? COLLATE NOCASE" if m else " AND i.series = ? COLLATE NOCASE"
            args.append(series.strip())
        sql += (" GROUP BY c.page_id ORDER BY i.pub_date IS NULL, i.pub_date, i.series, i.volume, i.num_sort "
                "LIMIT ?")
        limit = max(1, limit)
        rows = con.execute(sql, (*args, limit + 1)).fetchall()
        out = {"persona": name, "url_persona": url, "rol": role, "serie": series, "total": min(len(rows), limit),
               "truncado": len(rows) > limit, "numeros": []}
        rows = rows[:limit]
        for r in rows:
            titles = {s["index"]: s["title"] for s in json.loads(r["story_titles"] or "[]")}
            idx = [int(x) for x in (r["stories"] or "").split(",") if x and x != "0"]
            out["numeros"].append({"titulo": r["title"], "url": r["url"], "numero": r["number"],
                                   "fecha_publicacion": r["pub_date"], "fecha_tapa": r["cover_date"],
                                   "roles": r["roles"].split(","),
                                   "historias": [titles[i] for i in idx if titles.get(i)]})
        if not rows:
            like = con.execute("SELECT DISTINCT person FROM credits WHERE person LIKE ? LIMIT 10",
                               (f"%{person.strip().split()[-1]}%",)).fetchall()
            out["sugerencias"] = [r[0] for r in like]
        return out | {"licencia": LICENCIA}


@mcp.tool(annotations=RO)
def info_dump() -> dict:
    """Fecha del dump, cantidad de páginas por tipo y fecha de indexación (para saber qué tan actualizado está)."""
    with closing(connect()) as con:
        meta = dict(con.execute("SELECT key, value FROM meta").fetchall())
        kinds = dict(con.execute("SELECT kind, count(*) FROM pages GROUP BY kind ORDER BY 2 DESC").fetchall())
        return meta | {"paginas_por_tipo": kinds, "licencia": LICENCIA}


log = logging.getLogger("dcdb.http")
MAX_BODY = 4 * 1024 * 1024


def anon(ip):
    """IP truncated for the logs: /24 for IPv4, /48 for IPv6."""
    try:
        bits = 24 if ipaddress.ip_address(ip).version == 4 else 48
    except ValueError:
        return "?"
    return str(ipaddress.ip_network(f"{ip}/{bits}", strict=False).network_address)


def describe(body):
    """'tools/call:creditos', 'initialize'... from a JSON-RPC body. Arguments are never logged."""
    try:
        msgs = json.loads(body or b"null")
    except ValueError:
        return "-"
    out = []
    for m in msgs if isinstance(msgs, list) else [msgs]:
        if isinstance(m, dict) and isinstance(m.get("method"), str):
            p = m.get("params")
            name = p.get("name") if m["method"] == "tools/call" and isinstance(p, dict) else None
            out.append(f"{m['method']}:{name}" if isinstance(name, str) else m["method"])
    return ",".join(out)[:120] or "-"


async def reply(send, status, text):
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"text/plain; charset=utf-8"), (b"retry-after", b"60")]})
    await send({"type": "http.response.body", "body": text.encode()})


class Guard:
    """ASGI wrapper for the HTTP mode: per-IP rate limit (sliding minute) and one log line per request
    (time, truncated IP, method, MCP method/tool, status, duration). No arguments or bodies are logged."""

    def __init__(self, app, per_minute):
        self.app, self.per_minute, self.hits = app, per_minute, {}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        t0 = time.monotonic()
        ip = (scope.get("client") or ("?", 0))[0]
        if len(self.hits) > 10_000:
            self.hits = {k: v for k, v in self.hits.items() if v and t0 - v[-1] < 60}
        hits = [t for t in self.hits.get(ip, ()) if t0 - t < 60]
        status, what = 429, "-"
        if len(hits) >= self.per_minute:
            self.hits[ip] = hits
            await reply(send, 429, "Demasiados pedidos: esperá un minuto.\n")
        else:
            self.hits[ip] = hits + [t0]
            body, more = b"", True
            while more and len(body) <= MAX_BODY:
                m = await receive()
                body += m.get("body", b"")
                more = m.get("more_body", False) and m["type"] == "http.request"
            if len(body) > MAX_BODY:
                status = 413
                await reply(send, 413, "Pedido demasiado grande.\n")
            else:
                what, pending = describe(body), [{"type": "http.request", "body": body, "more_body": False}]

                async def replay():
                    return pending.pop() if pending else await receive()

                async def send_status(m):
                    nonlocal status
                    if m["type"] == "http.response.start":
                        status = m["status"]
                    await send(m)

                await self.app(scope, replay, send_status)
        log.info("%s %s %s %s %d %.0fms", time.strftime("%Y-%m-%dT%H:%M:%S"), anon(ip), scope["method"], what,
                 status, (time.monotonic() - t0) * 1000)


def http_app(per_minute=60, allowed_hosts=()):
    """Stateless Streamable HTTP app (JSON responses) wrapped in Guard."""
    security = TransportSecuritySettings(
        allowed_hosts=[*allowed_hosts, "127.0.0.1:*", "localhost:*"],
        allowed_origins=[f"https://{h}" for h in allowed_hosts]) if allowed_hosts else None
    app = mcp.streamable_http_app(stateless_http=True, json_response=True, transport_security=security)
    return Guard(app, per_minute)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--http", action="store_true", help="Streamable HTTP en /mcp en vez de stdio")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--rate", type=int, default=60, help="pedidos por minuto por IP (modo HTTP)")
    a = ap.parse_args()
    if not a.http:
        return mcp.run()
    import uvicorn

    logging.basicConfig(format="%(message)s")
    log.setLevel(logging.INFO)
    hosts = [h.strip() for h in os.environ.get("DCDB_ALLOWED_HOSTS", "").split(",") if h.strip()]
    # uvicorn's own access log is off (it has full IPs); behind a local proxy it takes the IP from X-Forwarded-For.
    uvicorn.run(http_app(a.rate, hosts), host=a.host, port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
