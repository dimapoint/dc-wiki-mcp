# dc-wiki-mcp

Copia local y consultable del [DC Database](https://dc.fandom.com) a partir de su **dump oficial**, expuesta como
**servidor MCP** (stdio) para que Claude consulte números, créditos, fechas, tomos recopilatorios y eventos sin leer
el sitio en vivo.

- `dcdb/wiki.py`: parseo del wikitext (plantillas `DC Database:* Template`, reglas de `Template:C` y `Module:StaffCorrection`).
- `dcdb/ingest.py`: dump XML → `data/dcdb.sqlite` (streaming, multiproceso, ~2–3 min).
- `dcdb/server.py`: servidor MCP de solo lectura.
- `docs/muestras.md`: muestras reales de cada plantilla y los hallazgos que definieron el esquema.
- `docs/despliegue.md`: opciones para publicarlo como conector de claude.ai (Fase 5, pendiente de decisión).

Requisitos: [uv](https://docs.astral.sh/uv/). El proyecto usa Python 3.14.7 (`.python-version`); uv lo instala solo.
No hace falta compilador: `mwparserfromhell` se instala con su tokenizador en Python puro (ver `[tool.uv]` en
`pyproject.toml`), porque no publica wheel de 3.14 para Windows.

## 1. Bajar el dump

1. Abrir `https://dc.fandom.com/wiki/Special:Statistics` **en el navegador** y bajar el dump
   `endcdatabase_pages_current.xml` (viene comprimido, `.7z` o `.gz`).
2. Descomprimirlo en `data/raw/endcdatabase_pages_current.xml` (`data/` está ignorado por git).

El dump usado para esta base es del **2026-09-20** (681.361 páginas, 1,1 GB descomprimido). Al armar el proyecto,
`dc.fandom.com` respondió **HTTP 402** a pedidos automáticos, así que ni el código ni `actualizar.sh` hacen scraping:
la descarga es manual o con una URL directa que le pases al script.

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

`tests/test_wiki.py` prueba el parser. `tests/test_fase4.py` prueba los casos de aceptación contra la base (créditos de
Batman #676 y #670, tomos de Final Crisis y Sinestro Corps War, run de Zdarsky, búsqueda de Zur-En-Arrh) y levanta el
servidor real por stdio.

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

## Herramientas

Todas son de solo lectura y devuelven la `url` de origen de cada página más una nota de licencia.

| herramienta | qué devuelve |
|---|---|
| `buscar(query, kind?, limit=10)` | búsqueda de texto completo (FTS5): título, tipo, fragmento, url. `kind`: issue, collection, event, series, character, staff, other |
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
- **Eventos**: un número pertenece a un evento por su parámetro `Event`/`Event2`..., por aparecer en la lista `Issues`
  de la página del evento o arco, o porque el título de su historia enlaza a esa página. Cada resultado dice cuál.
- **Categorías**: casi todas las generan las plantillas al renderizar, así que no están en el dump; solo se guardan las
  `[[Category:...]]` escritas a mano.

## Esquema (`data/dcdb.sqlite`)

`pages` (id, title, url, namespace, kind, template, wikitext, plain_text, updated_at, fields, headline) ·
`issues` (page_id, series, volume, number, series_page, cover_date, pub_date, pub_date_source, num_sort, story_titles) ·
`credits` (page_id, story_index, role, order_index, raw, person) ·
`collection_contents` (collection_page_id, issue_title, story_title, section, order_index, issue_page_id) ·
`event_membership` (event_title, member_title, source, order_index, section, event_page_id, page_id) ·
`categories` · `redirects` · `staff_aliases` · `meta` · `pages_fts` (FTS5 sobre title, headline, plain_text).

## Actualizar

```bash
DUMP_URL="https://…/endcdatabase_pages_current.xml.7z" DCDB_CONTACT="tu@mail" ./actualizar.sh
./actualizar.sh ruta/al/dump-bajado-a-mano.xml.7z
```

Baja el dump con un user agent honesto (`dc-wiki-mcp` + tu contacto), frena si recibe 402/403/429, descomprime y
reindexa. No usa la API de MediaWiki: el sitio respondió 402 a pedidos automáticos.

## Atribución y licencia del contenido

El contenido proviene del **DC Database** (https://dc.fandom.com), de sus colaboradores, bajo licencia
[CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Cada respuesta del servidor incluye la URL de la
página de origen: al reutilizar el contenido hay que atribuirlo con esa URL y compartir las obras derivadas bajo la
misma licencia. Este proyecto no está afiliado a Fandom ni a DC Comics.
