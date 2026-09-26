"""Fase 4: acceptance cases from the plan, against the built data/dcdb.sqlite."""
import json
import sys
from pathlib import Path

import anyio
import pytest

from dcdb import server

pytestmark = pytest.mark.skipif(not server.DB.exists(), reason="run `uv run python -m dcdb.ingest` first")


def story(res, i=1):
    return next(h for h in res["historias"] if h["indice"] == i)


def test_creditos_batman_676():
    c = story(server.creditos("Batman", 1, "676"))["creditos"]
    assert c["writer"] == ["Grant Morrison"]
    assert c["penciler"] == ["Tony S. Daniel"]


def test_creditos_batman_670():
    res = server.creditos("Batman", 1, "670")
    assert story(res)["creditos"]["writer"] == ["Grant Morrison"]
    assert res["url"] == "https://dc.fandom.com/wiki/Batman_Vol_1_670"


def test_tomo_final_crisis_new_edition():
    titles = [x["numero"] for x in server.tomo("Final Crisis New Edition (Collected)")["contenido"]]
    i = titles.index("Final Crisis Vol 1 5")
    assert titles[i:i + 4] == ["Final Crisis Vol 1 5", "Batman Vol 1 682", "Batman Vol 1 683", "Final Crisis Vol 1 6"]


def test_tomo_sinestro_corps_war():
    res = server.tomo("Green Lantern: The Sinestro Corps War (Collected)")
    assert [x["numero"] for x in res["contenido"]] == [
        "Green Lantern: Sinestro Corps Special Vol 1 1",
        "Green Lantern Vol 4 21", "Green Lantern Corps Vol 2 14", "Green Lantern Vol 4 22",
        "Green Lantern Corps Vol 2 15", "Green Lantern Vol 4 23", "Green Lantern Corps Vol 2 16",
        "Green Lantern Vol 4 24", "Green Lantern Corps Vol 2 17", "Green Lantern Corps Vol 2 18",
        "Green Lantern Vol 4 25", "Green Lantern Corps Vol 2 19"]
    assert all(x["url"] for x in res["contenido"])


def test_run_zdarsky_batman_vol_3_starts_at_125():
    res = server.run_de_autor("Chip Zdarsky", "writer", "Batman Vol 3")
    assert res["numeros"][0]["numero"] == "125"
    dates = [x["fecha_publicacion"] for x in res["numeros"]]
    assert dates == sorted(dates)


def test_buscar_zur_en_arrh():
    titles = [x["titulo"] for x in server.buscar("Zur-En-Arrh")["resultados"]]
    rip = [f"Batman Vol 1 {n}" for n in range(676, 682)] + ["Batman R.I.P.", "Batman R.I.P. (Collected)"]
    zdarsky = [f"Batman Vol 3 {n}" for n in range(125, 158)]
    assert any(t in rip for t in titles), titles
    assert any(t in zdarsky for t in titles), titles


def test_numero_links_collections_and_events():
    res = server.numero("Batman", 1, "676")
    assert res["fecha_tapa"] == "2008-06"
    assert "Batman R.I.P. (Collected)" in [t["titulo"] for t in res["reimpreso_en"]]
    assert "Batman R.I.P." in [e["titulo"] for e in res["eventos"]]


def test_evento_final_crisis_sorted_and_includes_batman_682():
    res = server.evento("Final Crisis")
    titles = [x["titulo"] for x in res["numeros"]]
    assert "Final Crisis Vol 1 1" in titles and "Batman Vol 1 682" in titles
    dated = [x["fecha_publicacion"] for x in res["numeros"] if x["fecha_publicacion"]]
    assert dated == sorted(dated)


def test_leer_pagina_resolves_redirects():
    res = server.leer_pagina("Bruce Wayne (Prime Earth)", max_chars=500)
    assert res["titulo"] == "Batman (Bruce Wayne)" and res["redirigido_desde"] == "Bruce Wayne (Prime Earth)"
    assert res["url"].startswith("https://dc.fandom.com/wiki/")


def test_info_dump():
    res = server.info_dump()
    assert res["dump_date"].startswith("20") and int(res["content_pages"]) > 100_000


def test_stdio_protocol():
    """The real server process answers over MCP stdio (what Claude Desktop / Claude Code use)."""
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    async def run():
        params = StdioServerParameters(command=sys.executable, args=["-m", "dcdb.server"],
                                       cwd=Path(__file__).resolve().parent.parent)
        async with stdio_client(params) as (r, w), ClientSession(r, w) as session:
            await session.initialize()
            names = {t.name for t in (await session.list_tools()).tools}
            res = await session.call_tool("creditos", {"series": "Batman", "volume": 1, "number": "676"})
            return names, json.loads(res.content[0].text)

    names, res = anyio.run(run)
    assert names == {"buscar", "leer_pagina", "numero", "creditos", "tomo", "evento", "run_de_autor", "info_dump"}
    assert story(res)["creditos"]["writer"] == ["Grant Morrison"]
