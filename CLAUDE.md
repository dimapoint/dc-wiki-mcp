# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Local, queryable copy of the DC Database wiki (dc.fandom.com) built from its official XML dump into SQLite, exposed as a
read-only MCP server. `dc-wiki-mcp-plan.md` is the original spec (phases 0–6); README.md and docs are in Spanish, and so
are the tool names and output keys (`buscar`, `numero`, `tomo`, `fuentes`...).

## Commands

Always use `uv` (never pip). Python is pinned to 3.14.7 in `.python-version`; old uv (0.8) can't install it — update uv.

```bash
uv sync
uv run python -m dcdb.ingest            # data/raw/endcdatabase_pages_current.xml -> data/dcdb.sqlite (2–9 min)
uv run python -m dcdb.refresh           # pages edited after the dump, via MediaWiki API
uv run python -m dcdb.server            # MCP over stdio
uv run python -m dcdb.server --http     # Streamable HTTP at 127.0.0.1:8000/mcp (DCDB_ALLOWED_HOSTS behind a proxy)
uv run pytest                           # all tests
uv run pytest tests/test_pipeline.py::test_refresh   # single test
```

`data/` is gitignored. In a fresh (e.g. cloud) checkout, get the dump from the repo's GitHub release
`data-dump-2026-09-20` (`.7z`, extract with `7z e -odata/raw ...`), then run the ingest. `tests/test_fase4.py` is skipped
without `data/dcdb.sqlite`; `test_wiki.py` and `test_pipeline.py` (synthetic mini-dump) need neither the DB nor network.
`DCDB_PATH` points the server at another DB.

## Project rules (from the plan)

- Only official channels: the dump and `api.php` with an honest user agent (project + contact) and ≥1 s between
  requests. On HTTP 402/403/429: stop and tell the user; never retry in a loop, fake user agents, or work around it.
  The wiki's web pages return 402 to automated requests; `api.php` works.
- Content is CC BY-SA: every tool response carries the source page `url` plus the `licencia` note.
- Look at real dump samples before writing parsing code; don't assume template/param names. `docs/muestras.md` has the
  samples and findings that shaped the schema.
- User prefers minimal code, no over-engineering.

## Architecture

- `dcdb/wiki.py` — pure wikitext → rows (no I/O). `process_page()` maps one ns-0 page to a dict of rows. It mirrors the
  wiki's own logic: infobox is the first top-level `{{DC Database:X Template}}` (X decides `kind` via `KINDS`);
  `c_ref()` replicates `Template:C` (`Batman #676` → `Batman Vol 1 676`); credits come from infobox params
  `Role{story}_{n}` (collections: `Role{n}`); publication date follows the Comic Template rule (cover month − 2 unless
  `ReleaseDate`/`Pubmonth` exist); `crossover_candidates()` reads navbox templates.
- `dcdb/ingest.py` — streaming `iterparse` + multiprocessing `Pool` over `process_page`, writes to `*.tmp` then renames.
  Side data collected while streaming: ns-0 redirects, ns-10 templates, `Module:StaffCorrection/data`. Then
  `crossover_map()` and `link()`. **`link()` is idempotent over the whole DB** (resolves titles→ids through redirects,
  derives crossover/category event memberships, canonicalizes credit names via StaffCorrection + redirects); both
  ingest and refresh call it. FTS5 (`pages_fts`) is an external-content table on `pages`, filled at the end;
  `/Gallery` pages (`IN_FTS`) are excluded.
- `dcdb/refresh.py` — `generator=recentchanges` + revisions from `meta.refreshed_until` (or `dump_date`);
  `delete_page()` removes a page and everything derived from it, including the FTS row via the `'delete'` command
  (must match exactly what was inserted, or the index corrupts), then `insert_row()` + `link()`. Edits/new
  pages/redirects only; deletions and moves wait for a new dump.
- `dcdb/server.py` — `MCPServer` tools, each opening a read-only SQLite connection. Title lookups go through
  `resolve()` (redirects, case-insensitive fallback). `--http` wraps the SDK's stateless Streamable HTTP app in
  `Guard` (per-IP rate limit, one log line per request with truncated IP and tool name, never arguments).

Event membership (`event_membership.source`) comes from several signals, and results report which: `issue_event_param`,
`event_issues_list`, `story_title_link` (kept only if the link resolves to an event page), `crossover_template`,
`category` (`[[Category:X Crossover]]`), `collection_storyarcs`. Most categories are generated at render time and are not
in the dump.

Schema changes require re-running the ingest (refresh needs the `transclusions`/`crossover_templates` tables).
Phase 5 (public hosting for claude.ai) is ready in code but deliberately not deployed; options are in `docs/despliegue.md`.
