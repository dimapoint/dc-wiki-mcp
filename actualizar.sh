#!/usr/bin/env bash
# Baja un dump nuevo del DC Database (o usa uno ya bajado) y reindexa data/dcdb.sqlite.
#
#   DUMP_URL="https://…/endcdatabase_pages_current.xml.7z" DCDB_CONTACT="tu@mail" ./actualizar.sh
#   ./actualizar.sh ruta/al/endcdatabase_pages_current.xml.7z    # o .gz / .xml bajado a mano
#
# Reglas del proyecto: user agent honesto (proyecto + contacto) y, ante 402/403/429, frenar sin reintentar.
set -euo pipefail
cd "$(dirname "$0")"
RAW=data/raw
XML="$RAW/endcdatabase_pages_current.xml"
mkdir -p "$RAW"

src="${1:-}"
if [ -z "$src" ]; then
  : "${DUMP_URL:?Definí DUMP_URL (link del dump en Special:Statistics) o pasá la ruta de un dump ya bajado}"
  : "${DCDB_CONTACT:?Definí DCDB_CONTACT (mail o URL) para identificarte en el user agent}"
  src="$RAW/$(basename "${DUMP_URL%%\?*}")"
  code=$(curl -sS -L -A "dc-wiki-mcp/0.1 (+${DCDB_CONTACT})" -o "$src.part" -w '%{http_code}' "$DUMP_URL")
  case "$code" in
    200) mv "$src.part" "$src" ;;
    402|403|429) rm -f "$src.part"; echo "HTTP $code: frenado, no se reintenta (bajalo a mano desde el navegador)." >&2; exit 2 ;;
    *) rm -f "$src.part"; echo "HTTP $code al bajar $DUMP_URL" >&2; exit 1 ;;
  esac
fi

case "$src" in
  *.7z)
    SEVENZ=$(command -v 7z || echo "/c/Program Files/7-Zip/7z.exe")
    "$SEVENZ" e -y -o"$RAW" "$src" >/dev/null ;;
  *.gz) gzip -dc "$src" > "$XML" ;;
  *.xml) [ "$src" -ef "$XML" ] || cp "$src" "$XML" ;;
  *) echo "Formato no reconocido: $src" >&2; exit 1 ;;
esac

uv run python -m dcdb.ingest --dump "$XML"
uv run pytest -q
uv run python -c "import json; from dcdb.server import info_dump; print(json.dumps(info_dump(), ensure_ascii=False, indent=1))"
