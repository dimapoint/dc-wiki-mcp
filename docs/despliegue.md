# Fase 5: usarlo desde claude.ai

claude.ai solo acepta conectores MCP **remotos**: una URL pública HTTPS que hable MCP por *Streamable HTTP*.

## Lo que ya está implementado (independiente del hosting)

```bash
DCDB_ALLOWED_HOSTS=dc.tu-dominio.com uv run python -m dcdb.server --http --port 8000 --rate 60
```

- **Transporte**: Streamable HTTP en `/mcp`, sin estado (`stateless_http`) y con respuestas JSON: cada pedido es
  independiente, no hay sesiones que crezcan en memoria.
- **Rate limit por IP**: ventana deslizante de 1 minuto (`--rate`, 60 por defecto); al pasarse responde `429` con
  `Retry-After: 60`. Está en la app (`Guard` en `dcdb/server.py`), así que no depende del proxy.
- **Logs mínimos**, una línea por pedido a stderr: fecha, IP truncada (/24 en IPv4, /48 en IPv6), método HTTP,
  método MCP y herramienta, status, duración. Nunca argumentos ni cuerpos:
  `2026-09-26T21:05:12 203.0.113.0 POST tools/call:creditos 200 14ms`
- **Host permitido**: el SDK de MCP rechaza pedidos con un `Host` que no sea localhost (protección contra DNS
  rebinding). Detrás de un proxy HTTPS hay que declarar el dominio público en `DCDB_ALLOWED_HOSTS` (separado por comas).
- **IP real detrás del proxy**: uvicorn toma `X-Forwarded-For` solo si el proxy es local (`127.0.0.1`).
- **Sin OAuth**: el conector no expone nada privado (contenido CC-BY-SA, solo lectura); el rate limit evita el abuso.
  Si más adelante lo querés privado, se agrega la autenticación del SDK de MCP.

Probado en `tests/test_pipeline.py` (cliente MCP real por HTTP, rechazo de `Host` ajeno, 429, formato de log).

## Lo que falta: dónde vive (decisión tuya)

### Tamaño de la base (dump 2026-09-20)

| parte | tamaño aprox. |
|---|---|
| `wikitext` crudo | 420 MB |
| `plain_text` | 230 MB |
| `fields` (JSON de infobox) | 90 MB |
| índice FTS5 + tablas + índices | ~380 MB |
| **total `dcdb.sqlite`** | **1,12 GB** |

El `wikitext` solo se usa en el servidor para buscar `{{co|...}}` en las notas de un número. Guardando esa lista en una
tabla durante la ingesta, una base "slim" sin `wikitext` quedaría en ~0,7 GB.

### Opciones

| | A. VPS chico con SQLite (recomendada) | B. Vercel + Turso/libSQL | C. Vercel + Postgres |
|---|---|---|---|
| Cambios de código | ninguno: lo de arriba + un proxy HTTPS | capa de datos remota; FTS5 depende del soporte de Turso (verificar) | reescribir búsqueda a `tsvector` y migrar esquema |
| ¿Entra la base? | sí (disco local) | como base externa, sí; dentro de la función, no (límite del bundle, ~250 MB) | según el plan: los gratis suelen quedar cortos para 0,7–1,1 GB |
| Latencia | baja (SQLite local) | + red por consulta, arranques en frío | + red por consulta, arranques en frío |
| Costo | ~US$ 4–6/mes (1–2 GB RAM, 20–40 GB disco) | gratis/bajo, según límites vigentes | gratis/bajo, según límites vigentes |
| Actualizar | `actualizar.sh` o `python -m dcdb.refresh` (cron) en el VPS | re-subir la base | re-migrar |
| Mantenimiento | vos (parches del SO; TLS automático con Caddy) | del proveedor | del proveedor |

(Precios y límites cambian: confirmarlos antes de elegir.) Variante de A con menos mantenimiento: un contenedor en
Fly.io/Railway con un volumen persistente para la SQLite; misma arquitectura, gestionada por ellos.

### Pasos con A

Los archivos listos están en `deploy/`: `dcdb.service` (systemd), `Caddyfile` (TLS), `cron` (refresco diario) y
`Dockerfile` (alternativa con contenedor / Fly.io / Railway y un volumen para `data/`).

1. Copiar el repo y `data/dcdb.sqlite` a `/opt/dc-wiki-mcp` en el VPS (`scp`), crear el usuario `dcdb`, `uv sync`.
2. `deploy/dcdb.service` → `/etc/systemd/system/` (cambiar `DCDB_ALLOWED_HOSTS`), `systemctl enable --now dcdb`.
3. `deploy/Caddyfile` → `/etc/caddy/Caddyfile` (cambiar el dominio).
4. `deploy/cron` → `/etc/cron.d/dcdb`. Toma ediciones, páginas nuevas, redirecciones, borrados y traslados; cuando
   salga un dump nuevo, `./actualizar.sh`.
5. En claude.ai: *Settings → Connectors → Add custom connector* con `https://dc.tu-dominio.com/mcp`.

### Variante gratis: Docker Desktop en tu PC

`deploy/docker-compose.yml` levanta el servidor, un refresco diario y un túnel de ngrok (plan gratis, con un dominio
estático `*.ngrok-free.app`), así que no se abre ningún puerto del router ni se paga nada. La PC y Docker Desktop
tienen que estar prendidos: si se apaga, el conector deja de responder hasta que vuelva. Los pedidos llegan por el
túnel, con la IP real en `X-Forwarded-For`, así que el rate limit por IP sigue funcionando. El plan gratis de ngrok
tiene topes de transferencia y pedidos por mes (confirmar los vigentes). Alternativa gratis sin tope declarado:
Tailscale Funnel (URL `*.ts.net`).

**Estado (2026-09-29): el código y los archivos de despliegue están listos; falta el VPS y el dominio**, que
dependen de tu cuenta. Mientras tanto se usa local (Claude Desktop / Claude Code por stdio).
