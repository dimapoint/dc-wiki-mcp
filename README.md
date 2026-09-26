# dc-wiki-mcp

Copia local y consultable del [DC Database](https://dc.fandom.com) a partir de su **dump oficial**, expuesta como
**servidor MCP** (stdio para Claude Desktop/Code, HTTP para claude.ai) para que Claude consulte números, créditos,
fechas, tomos recopilatorios y eventos sin leer el sitio en vivo.

- `dcdb/wiki.py`: parseo del wikitext (plantillas `DC Database:* Template`, reglas de `Template:C` y `Module:StaffCorrection`).
- `dcdb/ingest.py`: dump XML → `data/dcdb.sqlite` (streaming, multiproceso, 2–9 min según la máquina).
- `dcdb/refresh.py`: trae por la API de MediaWiki las páginas editadas después del dump.
- `dcdb/server.py`: servidor MCP de solo lectura (stdio o Streamable HTTP con rate limit y logs mínimos).
- `docs/muestras.md`: muestras reales de cada plantilla y los hallazgos que definieron el esquema.
- `docs/despliegue.md`: publicarlo como conector de claude.ai (Fase 5: el modo HTTP está listo; por ahora queda local).

Requisitos: [uv](https://docs.astral.sh/uv/). El proyecto usa Python 3.14.7 (`.python-version`); uv lo instala solo
si es reciente (uv 0.8 no conoce 3.14.7: `uv self update`, o `pip install -U uv` si no lo instalaste con el script).
No hace falta compilador: `mwparserfromhell` se instala con su tokenizador en Python puro (ver `[tool.uv]` en
`pyproject.toml`), porque no publica wheel de 3.14 para Windows.

## 1. Bajar el dump

1. Abrir `https://dc.fandom.com/wiki/Special:Statistics` **en el navegador** y bajar el dump
   `endcdatabase_pages_current.xml` (viene comprimido, `.7z` o `.gz`).
2. Descomprimirlo en `data/raw/endcdatabase_pages_current.xml` (`data/` está ignorado por git).

El dump usado para esta base es del **2026-09-20** (681.361 páginas, 1,1 GB descomprimido). Las páginas web del
sitio respondieron **HTTP 402** a pedidos automáticos, así que el código no hace scraping: el dump se baja a mano (o
con una URL directa que le pases a `actualizar.sh`). La API (`api.php`) sí responde a un user agent honesto y se usa
solo para refrescar páginas sueltas (ver *Actualizar*).

**Copia del dump en este repo** (misma licencia CC BY-SA, para máquinas sin navegador, como una sesión de Claude Code
en la nube): el release [`data-dump-2026-09-20`](https://github.com/dimapoint/dc-wiki-mcp/releases/tag/data-dump-2026-09-20)
tiene el `.7z` (154 MB).

```bash
mkdir -p data/raw
curl -L -o data/raw/dump.xml.7z https://github.com/dimapoint/dc-wiki-mcp/releases/download/data-dump-2026-09-20/endcdatabase_pages_current.xml.7z
7z e -odata/raw data/raw/dump.xml.7z && rm data/raw/dump.xml.7z    # Linux: apt install 7zip (o p7zip-full)
```

En una sesión de Claude Code en la nube el contenedor es efímero: estos pasos más la indexación se repiten en cada
sesión nueva.

## 2. Indexar

```bash
uv sync
uv run python -m dcdb.ingest
```

Genera `data/dcdb.sqlite` (~1,1 GB). Opciones: `--dump RUTA`, `--db RUTA`, `--workers N`. Escribe primero en
`dcdb.sqlite.tmp` y lo renombra al final, así una indexación cortada no rompe la base anterior.

## 3. Probar

```bash
uv run pytest
```

`tests/test_wiki.py` prueba el parser. `tests/test_pipeline.py` arma una base con un dump sintético y prueba ingesta,
refresco (con la API simulada), rate limit y el servidor HTTP con un cliente MCP real; no necesita la base ni red.
`tests/test_fase4.py` prueba los casos de aceptación contra la base (créditos de Batman #676 y #670, tomos de Final
Crisis y Sinestro Corps War, run de Zdarsky, búsqueda de Zur-En-Arrh) y levanta el servidor real por stdio.

## 4. Conectarlo a Claude

**Claude Code** (desde cualquier carpeta):

```bash
claude mcp add dc-database --scope user -- uv --directory C:\Users\dimar\dc-wiki-mcp run python -m dcdb.server
```

**Claude Desktop**: en `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dc-database": {
      "command": "uv",
      "args": ["--directory", "C:\\Users\\dimar\\dc-wiki-mcp", "run", "python", "-m", "dcdb.server"]
    }
  }
}
```

Reiniciar Claude Desktop. Para usar otra base: variable de entorno `DCDB_PATH`.

Para una prueba sin tocar la configuración (así se verificó con Claude Code):

```bash
echo '{"mcpServers":{"dc-database":{"command":"uv","args":["--directory","RUTA/dc-wiki-mcp","run","python","-m","dcdb.server"]}}}' > mcp.json
claude -p "Créditos de Batman Vol 1 #676" --mcp-config mcp.json --allowedTools "mcp__dc-database__creditos"
```

**claude.ai** (conector remoto): `uv run python -m dcdb.server --http` sirve Streamable HTTP en
`http://127.0.0.1:8000/mcp` con rate limit por IP y logs mínimos; para publicarlo hace falta un servidor con HTTPS,
ver [`docs/despliegue.md`](docs/despliegue.md).

## Herramientas

Todas son de solo lectura y devuelven la `url` de origen de cada página más una nota de licencia.

| herramienta | qué devuelve |
|---|---|
| `buscar(query, kind?, limit=20)` | búsqueda de texto completo (FTS5): título, tipo, fragmento, url. `kind`: issue, collection, event, series, character, staff, other |
| `leer_pagina(title, max_chars=20000)` | texto limpio + campos estructurados; resuelve redirecciones |
| `numero(series, volume, number)` | fechas de tapa y publicación, historias, créditos, tomos donde se reimprime, eventos |
| `creditos(series, volume, number)` | créditos por historia + portada/variantes y editor ejecutivo |
| `tomo(title)` | números que recopila, en orden, con título de historia |
| `evento(title)` | números del evento/crossover/arco ordenados por fecha de publicación, y tomos asociados |
| `run_de_autor(person, role="writer", series?)` | números de un autor por fecha; `series` = `"Batman Vol 3"` o `"Batman"`; `role="any"` para todos |
| `info_dump()` | fecha del dump, páginas por tipo, fecha de indexación |

## Cómo se interpretan los datos

- **Créditos**: salen de los parámetros de la plantilla (`Writer1_1`, `Penciler2_1`, `CoverArtist1`, `Cover3Artist2`...),
  que es lo que el sitio muestra en el recuadro lateral. El primer número es la historia, el segundo el orden.
  Los nombres se normalizan igual que el wiki (`Module:StaffCorrection/data`) y siguiendo redirecciones
  (`Tony Daniel` → `Tony S. Daniel`).
- **Fechas**: `fecha_tapa` = `Month`/`Year` del wiki. `fecha_publicacion` usa `ReleaseDate` o `Pubmonth`/`Pubyear` si
  existen; si no, la regla de la propia plantilla (mes de tapa − 2, con el `Day` de salida). Sin `Day` es una
  estimación a nivel mes, y `fuente_fecha` lo indica.
- **Eventos**: cada vínculo número → evento dice de dónde sale (`fuentes`): `issue_event_param` (parámetro
  `Event`/`Event2`... del número), `event_issues_list` (lista `Issues` de la página del evento o arco),
  `story_title_link` (el título de la historia enlaza al evento), `crossover_template` (el número incluye la plantilla
  de crossover del evento, p. ej. `{{Final Crisis}}` o `{{BatRIP}}`), `category` (`[[Category:X Crossover]]` escrita a
  mano) y, para tomos, `collection_storyarcs`.
- **Categorías**: casi todas las generan las plantillas al renderizar, así que no están en el dump; solo se guardan las
  `[[Category:...]]` escritas a mano (la de crossover se recupera por la plantilla, ver arriba).

## Esquema (`data/dcdb.sqlite`)

`pages` (id, title, url, namespace, kind, template, wikitext, plain_text, updated_at, fields, headline) ·
`issues` (page_id, series, volume, number, series_page, cover_date, pub_date, pub_date_source, num_sort, story_titles) ·
`credits` (page_id, story_index, role, order_index, raw, person) ·
`collection_contents` (collection_page_id, issue_title, story_title, section, order_index, issue_page_id) ·
`event_membership` (event_title, member_title, source, order_index, section, event_page_id, page_id) ·
`categories` · `redirects` · `staff_aliases` · `transclusions` (plantillas al pie de cada número) ·
`crossover_templates` (plantilla → evento) · `meta` · `pages_fts` (FTS5 sobre title, headline, plain_text).

## Actualizar

**Páginas editadas después del dump** (API de MediaWiki):

```bash
uv run python -m dcdb.refresh          # desde el último refresco o la fecha del dump; --since ISO para otra fecha
```

Pide `recentchanges` + el wikitext de cada página cambiada, con user agent honesto
(`dc-wiki-mcp/0.1 (+https://github.com/dimapoint/dc-wiki-mcp)`) y al menos 1 s entre pedidos; ante 402/403/429 frena
sin reintentar. Reemplaza la página y todo lo derivado (créditos, contenidos, eventos, búsqueda) y deja la fecha en
`info_dump().refreshed_until`. Toma ediciones, páginas nuevas y redirecciones; los borrados y traslados esperan al
próximo dump, y la API guarda cambios de unos 90 días. Medido el 2026-09-26: los 6 días desde el dump fueron 2.156
páginas en 44 pedidos, 2 minutos.

**Dump nuevo** (reindexa todo y después refresca):

```bash
DUMP_URL="https://…/endcdatabase_pages_current.xml.7z" DCDB_CONTACT="tu@mail" ./actualizar.sh
./actualizar.sh ruta/al/dump-bajado-a-mano.xml.7z
```

Baja el dump con un user agent honesto (`dc-wiki-mcp` + tu contacto), frena si recibe 402/403/429, descomprime,
reindexa, corre `dcdb.refresh` y los tests.

## Atribución y licencia del contenido

El contenido proviene del **DC Database** (https://dc.fandom.com), de sus colaboradores, bajo licencia
[CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Cada respuesta del servidor incluye la URL de la
página de origen: al reutilizar el contenido hay que atribuirlo con esa URL y compartir las obras derivadas bajo la
misma licencia. Este proyecto no está afiliado a Fandom ni a DC Comics.
