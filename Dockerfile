# Multi-stage build: compila dependencias en una etapa separada para reducir la imagen final.
FROM python:3.13-slim-bookworm AS builder

WORKDIR /build

# Dependencias de build necesarias para compilar extensiones nativas de geopandas/pyogrio.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir=/build/wheels -r requirements.txt

# ------------------------------------------------------------------------------
FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=UTC \
    PORT=8075 \
    APP_USER=geoapi

# Runtime libraries para GDAL/PROJ (usadas por geopandas/pyogrio).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal32 \
    libproj25 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Usuario no-root para ejecutar la aplicacion.
RUN groupadd --gid 10101 ${APP_USER} && \
    useradd --home-dir /home/${APP_USER} --uid 10100 --gid 10101 \
    --create-home --shell /bin/bash ${APP_USER}

WORKDIR /home/${APP_USER}/app

# Copia e instala las wheels generadas en la etapa de build.
COPY --from=builder --chown=10100:10101 /build/wheels /tmp/wheels
COPY --chown=10100:10101 requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels -r requirements.txt && \
    rm -rf /tmp/wheels

# Copia el codigo fuente.
COPY --chown=10100:10101 ./app .

USER ${APP_USER}

EXPOSE ${PORT}

# Gunicorn es un WSGI server productivo adecuado para clusters.
# - workers/threads se pueden sobreescribir con variables de entorno si se desea.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fs http://localhost:${PORT}/health || exit 1

CMD exec gunicorn \
    --bind 0.0.0.0:${PORT} \
    --workers ${GUNICORN_WORKERS:-2} \
    --threads ${GUNICORN_THREADS:-4} \
    --timeout ${GUNICORN_TIMEOUT:-60} \
    --access-logfile - \
    --error-logfile - \
    main:app
