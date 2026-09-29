# Servidor MCP por HTTP con la base montada como volumen (data/dcdb.sqlite).
#   docker build -f deploy/Dockerfile -t dcdb .
#   docker run -d -p 127.0.0.1:8000:8000 -v $PWD/data:/app/data -e DCDB_ALLOWED_HOSTS=dc.tu-dominio.com dcdb
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev
COPY dcdb ./dcdb
CMD ["uv", "run", "--no-dev", "python", "-m", "dcdb.server", "--http", "--host", "0.0.0.0", "--port", "8000"]
