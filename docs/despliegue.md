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

1. Copiar el repo y `data/dcdb.sqlite` al VPS (`scp`), `uv sync`.
2. Servicio (systemd) con el comando de arriba.
3. Caddy delante, solo para TLS:
   ```
   dc.tu-dominio.com {
       reverse_proxy 127.0.0.1:8000
   }
   ```
4. Cron diario para las páginas editadas: `uv run python -m dcdb.refresh` (y `actualizar.sh` cuando salga un dump).
5. En claude.ai: *Settings → Connectors → Add custom connector* con `https://dc.tu-dominio.com/mcp`.

Decime qué opción preferís (y si tenés VPS o dominio) y lo dejo andando.
