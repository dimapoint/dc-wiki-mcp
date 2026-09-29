# AGENTS.md

Guidance for coding agents (Codex, Claude Code, etc.) working in this repository. `CLAUDE.md` holds the same project
guide; this file adds how the live deployment is run and verified.

Local, queryable copy of the DC Database wiki (dc.fandom.com) built from its official XML dump into SQLite, exposed as a
read-only MCP server. `dc-wiki-mcp-plan.md` is the original spec (phases 0–6); README.md and docs are in Spanish, and so
are the tool names and output keys (`buscar`, `numero`, `tomo`, `fuentes`...). The repo is public on GitHub
(`dimapoint/dc-wiki-mcp`).

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

`data/` is gitignored. In a fresh checkout, get the dump from the GitHub release `data-dump-2026-09-20`
(`gh release download data-dump-2026-09-20 -D data/raw`, then `7z e -odata/raw data/raw/*.7z`) and run the ingest. In
Claude Code on the web, `.claude/hooks/session-start.sh` does all of this. `tests/test_fase4.py` is skipped without
`data/dcdb.sqlite`; `test_wiki.py` and `test_pipeline.py` (synthetic mini-dump) need neither the DB nor network.
`DCDB_PATH` points the server at another DB. Tell the user before running the ingest (it takes minutes).

## Project rules

- Only official channels: the dump and `api.php` with an honest user agent (project + contact) and ≥1 s between
  requests. On HTTP 402/403/429: stop and tell the user; never retry in a loop, fake user agents, or work around it.
  The wiki's web pages return 402 to automated requests; `api.php` works.
- Content is CC BY-SA: every tool response carries the source page `url` plus the `licencia` note.
- Look at real dump samples before writing parsing code; don't assume template/param names. `docs/muestras.md` has the
  samples and findings that shaped the schema.
- User prefers minimal code, no over-engineering.
- Git: work, commit and push directly on `main`. No feature branches, no pull requests. A local checkout can lag
  `origin/main`: `git pull --ff-only` before starting.
- Don't add authentication, rate limits or other access policies without asking the user.

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
  (must match exactly what was inserted, or the index corrupts), then `insert_row()` + `link()`. Edits, new
  pages, redirects, deletions, restores and moves (delete/move logs, refetched by title; missing = removed).
- `dcdb/server.py` — `MCPServer` tools, each opening a read-only SQLite connection. Title lookups go through
  `resolve()` (redirects, case-insensitive fallback). `--http` wraps the SDK's stateless Streamable HTTP app (JSON
  responses) in `Guard` (per-IP rate limit, 60/min by default; one log line per request with truncated IP and tool
  name, never arguments). With `DCDB_ALLOWED_HOSTS` set, the SDK rejects other `Host` headers (421) and other
  `Origin`s (403); localhost stays allowed.

Event membership (`event_membership.source`) comes from several signals, and results report which: `issue_event_param`,
`event_issues_list`, `story_title_link` (kept only if the link resolves to an event page), `crossover_template`,
`category` (`[[Category:X Crossover]]`), `collection_storyarcs`. Most categories are generated at render time and are not
in the dump. Schema changes require re-running the ingest (refresh needs the `transclusions`/`crossover_templates`
tables).

## Deployment (Docker Desktop + ngrok, on the user's Windows PC)

Phase 5 is live this way; the VPS option in `docs/despliegue.md` (systemd, Caddy, cron) is not deployed.
`deploy/docker-compose.yml` runs:

- `dcdb` — `dcdb.server --http` on port 8000, **not published on the host**. `FORWARDED_ALLOW_IPS=*` so the real client
  IP comes from ngrok's `X-Forwarded-For`.
- `refresh` — `dcdb.refresh` at start, then every 24 h. On 402/403/429 it exits and sleeps a day (no retry loop).
- `tunnel` — `ngrok/ngrok`, `http --url=$DCDB_HOST dcdb:8000`. The only thing exposed to the internet.
- All share the bind mount `../data:/app/data` (the SQLite file on the Windows host).

Rules and facts for agents:

- `deploy/.env` (gitignored) holds `NGROK_AUTHTOKEN` and `DCDB_HOST`. The user writes it. Never ask for, print, copy
  or commit the token; check it's set without printing it (e.g. print only its length). Don't commit the user's ngrok
  domain either: the repo is public, docs use `algo.ngrok-free.dev` as placeholder.
- Bring up / stop: `docker compose -f deploy/docker-compose.yml up -d --build` / `... down`. After editing
  `deploy/.env`, `up -d` recreates what changed. Stop the containers before `actualizar.sh` (they hold the DB open;
  on Windows replacing `dcdb.sqlite` fails).
- Verify with MCP requests, never a `GET /` (it's 404). Local: `docker compose exec -T dcdb python -c ...` with
  `urllib` (the port isn't published and the image has no curl; README has the exact command). Public: curl
  `initialize` and a `tools/call` of `buscar` (e.g. "Zur-En-Arrh") against `https://$DCDB_HOST/mcp`; results must carry
  `url` and `licencia`. The server is stateless, so `tools/call` works without a prior `initialize`.
- Logs: `logs dcdb` (one line per request), `logs refresh` (progress, final counts). `logs tunnel` is empty by design
  (no `--log stdout`); ngrok errors show up in the public response instead.
- `ERR_NGROK_15013`: the domain isn't claimed in the user's account. `ERR_NGROK_8012`: the tunnel can't reach `dcdb` —
  check `ps` and `logs dcdb` before touching the tunnel. `421`/`403` from the server: `DCDB_HOST` doesn't match the
  ngrok domain exactly.
- The Dockerfile base must be `ghcr.io/astral-sh/uv:python3.14-trixie-slim`: the `bookworm` tag is frozen at uv 0.9.30
  / Python 3.14.2 and `uv sync` fails with `No interpreter found for Python 3.14.7`.
- Windows / Docker Desktop: the bind mount needs the repo's `data` folder in *Settings → Resources → File sharing*
  (error: `is not shared from the host`). On the first mount Docker shows a Yes/No dialog; if nobody answers, it fails
  after ~1 min and doesn't ask again, so add the folder in Settings. If Docker Desktop hangs in "starting"
  (`docker desktop status`), `docker desktop restart` fixed it.
- No auth on purpose (public CC BY-SA content, read-only) plus the rate limit. claude.ai custom connectors only support
  authless or OAuth servers, so ngrok Basic Auth or a static bearer token would break the connector; an ngrok IP
  restriction to Anthropic's published egress ranges is compatible. Offer, don't apply without the user's OK.
- Not in GitHub (lost if the folder is deleted): `data/dcdb.sqlite` (regenerate: release dump + ingest; refresh
  catches up), `deploy/.env`, `.venv`, `.claude/settings.local.json`.
