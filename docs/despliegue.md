# Fase 5: opciones para usarlo desde claude.ai (propuesta, sin implementar)

claude.ai solo acepta conectores MCP **remotos**: una URL pública HTTPS que hable MCP por *Streamable HTTP*.
El servidor ya lo soporta sin cambios de lógica (`mcp.run("streamable-http")`). La pregunta es dónde vive la base.

## Tamaño de la base (dump 2026-09-20)

| parte | tamaño aprox. |
|---|---|
| `wikitext` crudo | 420 MB |
| `plain_text` | 230 MB |
| `fields` (JSON de infobox) | 90 MB |
| índice FTS5 + tablas + índices | ~380 MB |
| **total `dcdb.sqlite`** | **1,12 GB** |

El `wikitext` solo se usa en el servidor para una cosa (buscar `{{co|...}}` en las notas de un número). Guardando
esa lista en una tabla durante la ingesta, una **base "slim" sin `wikitext`** quedaría en ~0,7 GB.

## Opciones

| | A. VPS chico con SQLite (recomendada) | B. Vercel + Turso/libSQL | C. Vercel + Postgres |
|---|---|---|---|
| Cambios de código | casi nada: transporte HTTP + proxy | capa de datos async remota; FTS5 depende del soporte de Turso (verificar) | reescribir búsqueda a `tsvector` y migrar esquema |
| ¿Entra la base? | sí (disco local) | como base externa, sí; dentro de la función, no (límite de tamaño del bundle, ~250 MB) | según el plan: los planes gratis suelen quedar cortos para 0,7–1,1 GB |
| Latencia | baja (SQLite local) | + red por consulta, arranques en frío | + red por consulta, arranques en frío |
| Costo | ~US$ 4–6/mes (1–2 GB RAM, 20–40 GB disco) | gratis/bajo, según límites vigentes | gratis/bajo, según límites vigentes |
| Actualizar | `actualizar.sh` en el VPS o subir `dcdb.sqlite` con `scp` | re-subir la base al servicio | re-migrar |
| Mantenimiento | vos (parches del SO, TLS automático con Caddy) | del proveedor | del proveedor |

(Precios y límites de los proveedores cambian: confirmarlos antes de elegir.)

Variante de A con menos mantenimiento: un contenedor en Fly.io/Railway con un volumen persistente para la SQLite.
Es la misma arquitectura, gestionada por ellos.

## Propuesta concreta (A)

1. `dcdb/server.py`: flag `--http` para correr `mcp.run("streamable-http")` en `127.0.0.1:8000`.
2. **Caddy** delante: HTTPS automático, `rate_limit` por IP (p. ej. 60 pedidos/min) y logs mínimos
   (fecha, IP truncada, herramienta, duración; sin cuerpos).
3. Base slim, que ya incluye la tabla de reimpresiones mencionadas en notas.
4. Sin OAuth: el conector no expone nada privado (contenido CC-BY-SA, solo lectura). El rate limit evita el abuso.
   Si más adelante lo querés privado, se agrega auth del SDK de MCP.
5. En claude.ai: *Settings → Connectors → Add custom connector* con la URL `https://tu-dominio/mcp`.

Decime qué opción preferís (y si tenés VPS o dominio) y la implemento.
