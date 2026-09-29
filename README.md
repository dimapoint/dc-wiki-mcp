# dc-wiki-mcp

Copia local y consultable del [DC Database](https://dc.fandom.com) a partir de su **dump oficial**, expuesta como
**servidor MCP** (stdio para Claude Desktop/Code, HTTP para claude.ai) para que Claude consulte números, créditos,
fechas, tomos recopilatorios y eventos sin leer el sitio en vivo.

- `dcdb/wiki.py`: parseo del wikitext (plantillas `DC Database:* Template`, reglas de `Template:C` y `Module:StaffCorrection`).
- `dcdb/ingest.py`: dump XML → `data/dcdb.sqlite` (streaming, multiproceso, 2–9 min según la máquina).
- `dcdb/refresh.py`: trae por la API de MediaWiki las páginas editadas después del dump.
- `dcdb/server.py`: servidor MCP de solo lectura (stdio o Streamable HTTP con rate limit y logs mínimos).
- `docs/muestras.md`: muestras reales de cada plantilla y los hallazgos que definieron el esquema.
- `deploy/`: `docker-compose.yml` (servidor + refresco diario + túnel de ngrok en Docker Desktop, ver
  [Publicarlo desde tu PC](#publicarlo-para-claudeai-desde-tu-pc-docker-desktop--ngrok)), `Dockerfile`, y para un VPS
  `dcdb.service` (systemd), `Caddyfile` (TLS) y `cron`.
- `docs/despliegue.md`: opciones para publicarlo como conector de claude.ai (Fase 5). Hoy está publicado con Docker
  Desktop + ngrok.
- `actualizar.sh`: dump nuevo → reindexa, refresca y corre los tests.
- `.claude/hooks/session-start.sh`: prepara todo al abrir una sesión de Claude Code en la nube (ver *Bajar el dump*).
- `CLAUDE.md` / `AGENTS.md`: guía del repo para agentes (Claude Code, Codex...): comandos, reglas, arquitectura y
  operación del despliegue.

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

En una sesión de Claude Code en la nube el contenedor es efímero, así que estos pasos más la indexación se repiten en
cada sesión nueva. De eso se encarga el hook `SessionStart` (`.claude/hooks/session-start.sh`, registrado en
`.claude/settings.json`): actualiza uv si no conoce Python 3.14.7, corre `uv sync`, baja el dump del release, lo
descomprime e indexa. Cada paso se saltea si su resultado ya existe, y fuera de la nube (`CLAUDE_CODE_REMOTE` distinto
de `true`) no hace nada.

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
Crisis y Sinestro Corps War, run de Zdarsky, búsqueda de Zur-En-Arrh) y levanta el servidor real por stdio; se saltea si no existe `data/dcdb.sqlite`.

```bash
uv run pytest tests/test_pipeline.py::test_refresh   # un test suelto
```

## 4. Conectarlo a Claude

**Claude Code y Claude Desktop en Windows**: ver [Uso local en Windows](#uso-local-en-windows).
Para usar otra base: variable de entorno `DCDB_PATH`.

Para una prueba sin tocar la configuración (así se verificó con Claude Code):

```bash
echo '{"mcpServers":{"dc-database":{"command":"uv","args":["--directory","RUTA/dc-wiki-mcp","run","python","-m","dcdb.server"]}}}' > mcp.json
claude -p "Créditos de Batman Vol 1 #676" --mcp-config mcp.json --allowedTools "mcp__dc-database__creditos"
```

**claude.ai** (conector remoto): `uv run python -m dcdb.server --http` sirve Streamable HTTP en
`http://127.0.0.1:8000/mcp` con rate limit por IP y logs mínimos (una línea por pedido con IP truncada y nombre de la
herramienta, nunca los argumentos). Opciones: `--host`, `--port`, `--rate N` (pedidos por minuto por IP, 60 por
defecto); detrás de un proxy, `DCDB_ALLOWED_HOSTS=dominio1,dominio2` habilita esos `Host`. Para publicarlo hace falta
una URL HTTPS: gratis desde tu PC con
[Docker Desktop + ngrok](#publicarlo-para-claudeai-desde-tu-pc-docker-desktop--ngrok), o en un VPS
([`docs/despliegue.md`](docs/despliegue.md)).

## Uso local en Windows

Se registra con el Python del entorno virtual y rutas absolutas: no hace falta `uv`, una terminal abierta ni estar
parado en el repo. `PYTHONPATH` apunta al repo para que `-m dcdb.server` encuentre el paquete; la base se busca en
`data\dcdb.sqlite` relativa a `dcdb\server.py`, no al directorio de arranque. Requisito: haber corrido `uv sync` una vez
(crea `.venv`).

**Claude Code** (alcance de usuario, disponible en cualquier proyecto):

```powershell
claude mcp add dc-database --scope user -e "PYTHONPATH=C:\Users\dimar\dc-wiki-mcp" -- "C:\Users\dimar\dc-wiki-mcp\.venv\Scripts\python.exe" -m dcdb.server
claude mcp get dc-database   # debe decir "Connected"
```

**Claude Desktop**: agregar a `%APPDATA%\Claude\claude_desktop_config.json` (si ya tiene otras claves, sumar solo
`mcpServers`):

```json
{
  "mcpServers": {
    "dc-database": {
      "command": "C:\\Users\\dimar\\dc-wiki-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "dcdb.server"],
      "env": { "PYTHONPATH": "C:\\Users\\dimar\\dc-wiki-mcp" }
    }
  }
}
```

Después cerrar Claude Desktop del todo (también desde el ícono de la bandeja) y volver a abrirlo; en Claude Code, abrir
una sesión nueva. Si movés el repo, actualizar las dos rutas en ambos lugares.

**Actualizar el dump** (desde Git Bash, en el repo; ver [Actualizar](#actualizar)):

```bash
uv run python -m dcdb.refresh                          # solo lo editado desde el dump/último refresco
./actualizar.sh ruta/al/endcdatabase_pages_current.xml.7z   # dump nuevo bajado a mano: reindexa, refresca y testea
```

El indexado arma `dcdb.sqlite.tmp` y al final la reemplaza; en Windows ese reemplazo falla si algún proceso tiene la
base abierta, así que antes de `actualizar.sh` hay que cerrar Claude Desktop y las sesiones de Claude Code (todas
levantan el servidor). `dcdb.refresh` sí puede correr con ellos abiertos. La configuración no cambia. `info_dump()` muestra la fecha del dump y del
último refresco.

## Publicarlo para claude.ai desde tu PC (Docker Desktop + ngrok)

`deploy/docker-compose.yml` levanta tres contenedores, gratis y sin abrir puertos del router:

- `dcdb`: el servidor por HTTP en el puerto 8000, **sin publicarlo en la PC** (solo lo alcanza el túnel).
- `refresh`: corre `dcdb.refresh` al arrancar y después cada 24 h (ante 402/403/429 frena y espera al día siguiente).
- `tunnel`: ngrok, reenvía únicamente a `dcdb:8000`. Es lo único expuesto a internet.

La base se monta desde `data/` (`../data:/app/data`). El conector responde mientras la PC y Docker Desktop estén
prendidos. El plan gratis de ngrok tiene topes de transferencia y pedidos por mes.

1. Cuenta gratis en [ngrok](https://ngrok.com): el
   [authtoken](https://dashboard.ngrok.com/get-started/your-authtoken) y el dominio estático gratis (sección
   *Domains*, del estilo `algo.ngrok-free.app` o `algo.ngrok-free.dev`).
2. Crear `deploy/.env` (está en `.gitignore`: no commitearlo ni pegar el token en ningún chat):
   ```
   NGROK_AUTHTOKEN=tu-token
   DCDB_HOST=algo.ngrok-free.dev
   ```
   `DCDB_HOST` es solo el dominio, sin `https://` ni `/mcp`: lo usan el túnel (`--url`) y el servidor
   (`DCDB_ALLOWED_HOSTS`).
3. **Windows**: Docker Desktop → *Settings → Resources → File sharing* → agregar la carpeta `data` del repo (por
   ejemplo `C:\Users\dimar\dc-wiki-mcp\data`) → *Apply & restart*. Sin eso el volumen falla con
   `the path ... is not shared from the host`. Queda guardado; solo hay que repetirlo si el repo cambia de ruta.
4. Levantar todo:
   ```bash
   docker compose -f deploy/docker-compose.yml up -d --build
   ```
5. Verificar con pedidos MCP (un `GET /` responde 404, no sirve como prueba). Local, desde adentro del contenedor
   porque el puerto no está publicado:
   ```bash
   docker compose -f deploy/docker-compose.yml exec -T dcdb python -c "import urllib.request as u; print(u.urlopen(u.Request('http://localhost:8000/mcp', b'{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-03-26\",\"capabilities\":{},\"clientInfo\":{\"name\":\"test\",\"version\":\"0\"}}}', {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'})).read().decode())"
   ```
   Público (`initialize` y una búsqueda real, que tiene que traer resultados con su `url`):
   ```bash
   curl -sS -m 30 -X POST https://algo.ngrok-free.dev/mcp -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}'
   curl -sS -m 30 -X POST https://algo.ngrok-free.dev/mcp -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"buscar","arguments":{"query":"Zur-En-Arrh","limit":3}}}'
   ```
6. En claude.ai: *Settings → Connectors → Add custom connector* con `https://algo.ngrok-free.dev/mcp`.

**Operación**:

```bash
docker compose -f deploy/docker-compose.yml ps            # estado de los tres contenedores
docker compose -f deploy/docker-compose.yml logs dcdb     # una línea por pedido: IP truncada, herramienta, status
docker compose -f deploy/docker-compose.yml logs refresh  # páginas actualizadas en cada pasada
docker compose -f deploy/docker-compose.yml up -d         # después de cambiar deploy/.env (p. ej. token nuevo)
docker compose -f deploy/docker-compose.yml down          # detener todo
```

El log de `tunnel` sale vacío (ngrok no escribe a stdout sin `--log stdout`); sus errores aparecen en la respuesta
pública. Antes de `actualizar.sh` hay que bajar los contenedores: tienen la base abierta y en Windows el reemplazo de
`dcdb.sqlite` falla.

**Problemas conocidos**:

| síntoma | causa / qué hacer |
|---|---|
| `ERR_NGROK_15013` | el dominio no está reclamado en la cuenta: crearlo en *Domains* y ponerlo en `DCDB_HOST` |
| `ERR_NGROK_8012` | el túnel llega pero no alcanza a `dcdb`: revisar `ps` y `logs dcdb` antes de tocar el túnel |
| `421` (o `403`) del servidor | `DCDB_HOST` no coincide exactamente con el dominio de ngrok (chequeo de `Host`/`Origin` del SDK) |
| `is not shared from the host` | falta el paso 3 (File sharing) |
| build: `No interpreter found for Python 3.14.7` | la imagen base tiene que ser `uv:python3.14-trixie-slim`; el tag `bookworm` quedó en Python 3.14.2 |
| Docker Desktop queda en "starting" | `docker desktop restart` (`docker desktop status` para ver el estado) |

**Protección**: no tiene autenticación a propósito (contenido público CC BY-SA, solo lectura), solo el rate limit de
60 pedidos por minuto por IP; la IP real llega por `X-Forwarded-For`. claude.ai solo acepta conectores sin
autenticación o con OAuth, así que un Basic Auth o un token fijo en ngrok lo cortaría. Lo compatible es restringir por
IP en ngrok (*traffic policy*) a los rangos de salida que publica Anthropic.

## Herramientas

Todas son de solo lectura y devuelven la `url` de origen de cada página más una nota de licencia.

| herramienta | qué devuelve |
|---|---|
| `buscar(query, kind?, limit=20)` | búsqueda de texto completo (FTS5): título, tipo, fragmento, url. `kind`: issue, collection, event, series, character, staff, other |
| `leer_pagina(title, max_chars=20000)` | texto limpio + campos estructurados; resuelve redirecciones |
| `numero(series, volume, number)` | fechas de tapa y publicación, historias, créditos, tomos donde se reimprime, eventos |
| `creditos(series, volume, number)` | créditos por historia + portada/variantes y editor ejecutivo |
| `tomo(title)` | números que recopila, en orden, con título de historia |
| `evento(title, limit=500)` | números del evento/crossover/arco ordenados por fecha de publicación, y tomos asociados |
| `run_de_autor(person, role="writer", series?, limit=1000)` | números de un autor por fecha; `series` = `"Batman Vol 3"` o `"Batman"`; `role="any"` para todos |
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
`info_dump().refreshed_until`. Toma ediciones, páginas nuevas, redirecciones, borrados, restauraciones y traslados (por los
registros `delete` y `move`); la API guarda cambios de unos 90 días. Medido el 2026-09-26: los 6 días desde el dump fueron 2.156
páginas en 44 pedidos, 2 minutos.

**Dump nuevo** (reindexa todo y después refresca):

```bash
DUMP_URL="https://…/endcdatabase_pages_current.xml.7z" DCDB_CONTACT="tu@mail" ./actualizar.sh
./actualizar.sh ruta/al/dump-bajado-a-mano.xml.7z
```

Baja el dump con un user agent honesto (`dc-wiki-mcp` + tu contacto), frena si recibe 402/403/429, descomprime,
reindexa, corre `dcdb.refresh` y los tests.

## Reinstalar desde cero

En GitHub están el código, `deploy/`, las docs y el dump (release `data-dump-2026-09-20`). **No están**, y se pierden si
borrás la carpeta: `data/dcdb.sqlite` (se regenera), `deploy/.env` (se vuelve a crear), `.venv` (`uv sync`) y
`.claude/settings.local.json` (permisos locales de Claude Code). Si el conector está andando, antes de borrar:
`docker compose -f deploy/docker-compose.yml down`.

```bash
git clone https://github.com/dimapoint/dc-wiki-mcp.git && cd dc-wiki-mcp
gh release download data-dump-2026-09-20 -D data/raw          # o el curl de "Bajar el dump"
7z e -odata/raw data/raw/endcdatabase_pages_current.xml.7z
uv sync && uv run python -m dcdb.ingest
```

Las ediciones posteriores al dump vuelven con la primera pasada de `dcdb.refresh` (el contenedor `refresh` la hace
solo). Para el conector: crear `deploy/.env` y `up -d --build` (File sharing solo si cambió la ruta). Para Claude
Code/Desktop: [Uso local en Windows](#uso-local-en-windows).

## Atribución y licencia del contenido

El contenido proviene del **DC Database** (https://dc.fandom.com), de sus colaboradores, bajo licencia
[CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Cada respuesta del servidor incluye la URL de la
página de origen: al reutilizar el contenido hay que atribuirlo con esa URL y compartir las obras derivadas bajo la
misma licencia. Este proyecto no está afiliado a Fandom ni a DC Comics.
