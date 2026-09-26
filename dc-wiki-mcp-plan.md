# Proyecto: DC Database local + servidor MCP

Pegá este archivo en Claude Code (o guardalo como `PLAN.md` en la raíz del repo y pedile que lo siga).

---

## Objetivo

Construir una copia local y consultable del DC Database (https://dc.fandom.com) a partir de su **dump oficial**, y exponerla como **servidor MCP** para que Claude pueda consultar números, créditos, fechas, tomos recopilatorios y eventos sin depender de leer el sitio en vivo.

## Reglas no negociables

- **Solo canales oficiales.** Usar el dump que publica Fandom y, opcionalmente, la API de MediaWiki (`api.php`). No usar user agents falsos, proxies, navegadores headless disfrazados ni ninguna técnica para esquivar bloqueos. Si un endpoint responde 402, 403 o 429, **frenar y avisarme**; no reintentar en loop ni buscar rodeos.
- **Licencia.** El contenido es CC-BY-SA. Guardar la URL de origen de cada página y devolverla en las respuestas del servidor para poder atribuir.
- **Antes de escribir código de parsing, mirar datos reales.** No asumir nombres de plantillas o campos: sacar muestras del dump y confirmarlos.

## Fase 0: verificar el dump (frenar y reportar antes de seguir)

1. Averiguar dónde está el dump actual del DC Database (normalmente enlazado desde `Special:Statistics`, archivo `*_pages_current.xml.7z` o `.gz`).
2. Reportarme: URL, fecha del dump, tamaño comprimido. **Esperar mi OK** antes de descargar si pesa más de 2 GB.
3. Si no hay dump disponible o es muy viejo (más de 6 meses), frenar y preguntarme cómo seguir.

## Fase 1: ingesta

1. Descargar y descomprimir el dump en `data/raw/` (ignorado por git).
2. Parsear en streaming (el XML es grande; no cargarlo entero en memoria). Sugerido: Python con `mwxml` o `lxml.iterparse` + `mwparserfromhell` para el wikitext.
3. Tomar 20 páginas de muestra de cada tipo y mostrarme cómo vienen sus plantillas antes de definir el esquema:
   - Números sueltos (ej. `Batman Vol 1 676`, `Final Crisis Vol 1 1`, `Batman Vol 4 13`)
   - Tomos recopilatorios (`... (Collected)`)
   - Eventos / arcos (`Final Crisis`, `Batman R.I.P.`, `Batman: Bad Seeds`)
   - Series / volúmenes (`Batman Vol 3`)
   - Personajes (`Bruce Wayne (Prime Earth)`)
4. Resolver redirecciones y guardar el mapa `alias → página canónica`.

## Fase 2: esquema SQLite

Base en `data/dcdb.sqlite`. Ajustar según lo que muestren las muestras, pero como mínimo:

- `pages(id, title, url, namespace, kind, wikitext, plain_text, updated_at)` donde `kind` ∈ {issue, collection, event, series, character, other}
- `issues(page_id, series, volume, number, cover_date, pub_date, story_titles)`
- `credits(page_id, story_index, role, person)` con roles tipo writer, penciler, inker, colorist, letterer, editor, cover_artist
- `collection_contents(collection_page_id, issue_page_id, story_title, order_index)`
- `event_membership(event_page_id, page_id)` (a partir de categorías y plantillas de crossover)
- `categories(page_id, category)`
- `redirects(from_title, to_title)`
- Tabla FTS5 sobre `title` + `plain_text` para búsqueda de texto completo.

Importante: los créditos que en la web aparecen en el recuadro lateral vienen de parámetros de plantilla en el wikitext. Extraerlos de ahí, que es justamente lo que se pierde al leer la página renderizada.

## Fase 3: servidor MCP

Herramientas (todas de solo lectura, todas devuelven `url` de origen):

- `buscar(query, kind?, limit?)` → búsqueda FTS con título, tipo, fragmento y URL
- `leer_pagina(title)` → texto limpio + campos estructurados (resuelve redirecciones)
- `numero(series, volume, number)` → fechas, títulos de historias, créditos, tomos donde se reimprime, eventos a los que pertenece
- `creditos(series, volume, number)` → créditos por historia
- `tomo(title)` → lista ordenada de números que recopila
- `evento(title)` → números del evento/crossover ordenados por fecha de publicación
- `run_de_autor(person, role="writer", series?)` → números ordenados por fecha
- `info_dump()` → fecha del dump y cantidad de páginas (para saber qué tan actualizado está)

Primero correrlo **local** (transporte stdio) y probarlo con Claude Code / Claude Desktop.

## Fase 4: pruebas

Casos que tienen que andar (respuesta esperada entre paréntesis, verificarlos contra el dump):

1. `creditos("Batman", 1, 676)` → guion Grant Morrison, lápiz Tony S. Daniel
2. `creditos("Batman", 1, 670)` → guion Grant Morrison
3. `tomo("Final Crisis New Edition (Collected)")` → incluye Batman #682-683 entre Final Crisis #5 y #6
4. `tomo("Green Lantern: The Sinestro Corps War (Collected)")` → del Sinestro Corps Special #1 a Green Lantern Corps #19, en orden
5. `run_de_autor("Chip Zdarsky", "writer", "Batman Vol 3")` → empieza en #125
6. `buscar("Zur-En-Arrh")` → aparecen páginas de Batman R.I.P. y de la etapa de Zdarsky

## Fase 5 (opcional): uso desde claude.ai

Para usarlo como conector en claude.ai tiene que estar online (transporte HTTP). Evaluar y proponerme opciones antes de implementar, teniendo en cuenta el tamaño de la base:

- Vercel + base externa (Turso/libSQL o Postgres) si la SQLite no entra en los límites de una función serverless.
- Un VPS chico con la SQLite local.
- Rate limit por IP y logs mínimos.

## Fase 6 (opcional): actualizaciones

- Script `actualizar.sh` que baja el dump nuevo y reindexa.
- Si la API de MediaWiki responde normalmente con un user agent honesto (nombre del proyecto + contacto) y pausas de al menos 1 segundo entre pedidos, usarla para refrescar páginas sueltas recientes. Si responde 402/403, no usarla.

## Entregables

- Repo con `README.md` (cómo bajar el dump, indexar, correr el servidor, conectarlo a Claude Desktop y a Claude Code).
- Tests de la Fase 4 automatizados.
- Nota de atribución CC-BY-SA en el README.
