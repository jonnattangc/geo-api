# Geo API

API Flask que permite consultar si un punto geografico (latitud/longitud) esta dentro de una **Region**, **Provincia** o **Comuna** de Chile. Tambien soporta verificacion a nivel de **Pais** y realiza geocodificacion de direcciones mediante [Nominatim](https://nominatim.openstreetmap.org/).

La API esta pensada para ejecutarse en contenedores y clusters, usando **Gunicorn** como WSGI server productivo y cargando los shapefiles en memoria bajo demanda.

---

## Arquitectura

El proyecto esta organizado en **2 capas** bajo `app/`:

- **`controllers/geo_controller.py`** — Flask Blueprint que recibe las peticiones HTTP, valida el header `x-api-key`, y delega a los servicios.
- **`services/`** — Logica de negocio dividida en:
  - `base_shapefile_service.py` — Interfaz ABC + factory.
  - `shapefile_service.py` — Carga lazy de shapefiles chilenos desde disco.
  - `shapeaws_service.py` — Descarga shapefiles desde S3 y luego los consulta.
  - `nominatim_service.py` — Comunicacion con Nominatim.
  - `geo_service.py` — Orquesta las operaciones entre shapefiles y Nominatim.
- **`main.py`** — Punto de entrada. Crea la app Flask, expone `/health` y registra el Blueprint en `/geo`.

---

## Requisitos

- Python 3.13+
- Dependencias: `Flask`, `geopandas`, `shapely`, `requests`, `gunicorn` (ver `requirements.txt`)
- **Shapefiles** de Chile en `app/static/shapes/chile/`:
  - `regiones/Regional.shp`
  - `provincias/Provincias.shp`
  - `comunas/comunas.shp`
  - `regiones/regions.json`

> Los shapefiles no estan versionados (`.gitignore`). Debes descargarlos por separado antes de ejecutar la aplicacion, o bien usar `USE_AWS_SHAPES=true` para obtenerlos desde S3.

---

## Ejecucion local

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Exportar la API Key
export GEO_API_KEY=tu_clave_secreta

# 3. Ejecutar (puerto por defecto 8075)
python app/main.py

# O especificar puerto
python app/main.py 8075
```

---

## Docker

```bash
# Construir imagen
docker build -t geoapi:local .

# Ejecutar container
docker run -e GEO_API_KEY=tu_clave -p 8075:8075 geoapi:local
```

### Docker Compose

```bash
export GEO_API_KEY=tu_clave_secreta
docker compose up --build
```

> `docker-compose.yml` ahora funciona out-of-the-box y construye la imagen localmente.

---

## CI/CD

El workflow de GitHub Actions esta en `.github/workflows/ci-cd.yml`.

### Push a `develop`
- Construye la imagen Docker.
- Escanea la imagen con **Trivy** (falla si encuentra vulnerabilidades HIGH/CRITICAL).
- Ejecuta analisis estatico con **SonarCloud/SonarQube**.

### Tag `release/x.y.z`
- Construye y publica imagen multiplataforma en Docker Hub:
  - `jonnattangc/geoservice:x.y.z`
  - `jonnattangc/geoservice:latest`

### Secrets necesarios en GitHub
Configura estos secrets en **Settings > Secrets and variables > Actions**:

| Secret | Descripcion |
|--------|-------------|
| `DOCKER_USERNAME` | Usuario de Docker Hub. |
| `DOCKER_PASSWORD` | Token de acceso de Docker Hub. |
| `SONAR_TOKEN` | Token de SonarCloud/SonarQube. |
| `SONAR_HOST_URL` | Opcional. URL de SonarQube propio. Para SonarCloud no es necesario. |

> Edita `sonar-project.properties` y reemplaza `sonar.projectKey` y `sonar.organization` por los valores de tu proyecto en SonarCloud.

---

## Variables de entorno

| Variable | Descripcion | Default |
|----------|-------------|---------|
| `GEO_API_KEY` | **Requerida.** API key para el header `x-api-key`. | — |
| `PORT` | Puerto HTTP de la aplicacion. | `8075` |
| `GUNICORN_WORKERS` | Numero de workers de Gunicorn. | `2` |
| `GUNICORN_THREADS` | Threads por worker. | `4` |
| `GUNICORN_TIMEOUT` | Timeout de requests (segundos). | `60` |
| `USE_AWS_SHAPES` | Si es `true`, descarga shapes desde S3. | `false` |
| `AWS_S3_BUCKET` | Bucket S3 con los shapes. | — |
| `AWS_S3_PREFIX` | Prefijo dentro del bucket. | `shapes/chile` |
| `NOMINATIM_URL` | URL base de Nominatim. | `https://nominatim.openstreetmap.org/search.php` |
| `NOMINATIM_TIMEOUT` | Timeout para llamadas a Nominatim. | `20` |
| `NOMINATIM_USER_AGENT` | User-Agent para llamadas a Nominatim. | `geo-api/1.0.0` |

---

## Endpoints

Todas las peticiones a `/geo/*` deben incluir el header:

```
x-api-key: <GEO_API_KEY>
```

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| `GET` | `/health` | Health check (no requiere API key) |
| `GET` | `/geo/regions` | Lista todas las regiones de Chile |
| `GET` | `/geo/{region_id}/provinces` | Lista provincias de una region |
| `GET` | `/geo/{region_id}/communes` | Lista comunas de una region |
| `POST` | `/geo/search` | Geocodifica una direccion |
| `POST` | `/geo/inside` | Verifica si un punto esta dentro de una zona |

### Ejemplos

**Health check:**
```bash
curl http://localhost:8075/health
```

**Listar regiones:**
```bash
curl -H "x-api-key: tu_clave" http://localhost:8075/geo/regions
```

**Buscar direccion:**
```bash
curl -X POST http://localhost:8075/geo/search \
  -H "x-api-key: tu_clave" \
  -H "Content-Type: application/json" \
  -d '{"data": {"street": "Alameda 123", "city": "Santiago", "state": "Metropolitana", "country": "Chile"}}'
```

**Verificar punto dentro de una region:**
```bash
curl -X POST http://localhost:8075/geo/inside \
  -H "x-api-key: tu_clave" \
  -H "Content-Type: application/json" \
  -d '{"data": {"latitude": -33.45, "longitude": -70.67, "zone": {"region": "Metropolitana"}}}'
```

---

## Consideraciones para cluster

- La aplicacion expone `/health` para **liveness** y **readiness probes**.
- El Dockerfile ejecuta Gunicorn, no el servidor de desarrollo de Flask.
- Cada worker de Gunicorn carga los shapefiles en memoria bajo demanda. Si los shapefiles son grandes, considera:
  - Usar menos workers pero mas threads (por ejemplo, `GUNICORN_WORKERS=1`, `GUNICORN_THREADS=8`).
  - Aumentar el limite de memoria del contenedor.
  - Cargar los shapes una sola vez en un volumen compartido o usar un cache compartido.

---

## Fuentes de datos geoespaciales

- [Biblioteca del Congreso Nacional (BCN) — Mapas vectoriales](https://www.bcn.cl/siit/mapas_vectoriales)
- [Geoportal Chile — Division Politica Administrativa 2023](https://www.geoportal.cl/geoportal/catalog/36391/Divisi%C3%B3n%20Pol%C3%ADtica%20Administrativa%202023)

---

## Autor

Jonnattan G
