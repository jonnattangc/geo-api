# Geo API

API Flask que permite consultar si un punto geográfico (latitud/longitud) está dentro de una **Región**, **Provincia** o **Comuna** de Chile. También soporta verificación a nivel de **País** y realiza geocodificación inversa de direcciones mediante [Nominatim](https://nominatim.openstreetmap.org/).

---

## Arquitectura

El proyecto está organizado en **2 capas** bajo `app/`:

- **`controllers/geo_controller.py`** — Flask Blueprint que recibe las peticiones HTTP, valida el header `x-api-key`, y delega a los servicios.
- **`services/`** — Lógica de negocio dividida en:
  - `shapefile_service.py` — Carga lazy de shapefiles chilenos y consultas geoespaciales.
  - `nominatim_service.py` — Comunicación con Nominatim para geocodificación de direcciones.
  - `geo_service.py` — Orquesta las operaciones entre shapefiles y Nominatim.
- **`http-server.py`** — Punto de entrada. Crea la app Flask y registra el Blueprint en `/geo`.

> La lógica anterior en un solo archivo `utilgeo.py` fue descompuesta en estos módulos.

---

## Requisitos

- Python 3.13+
- Dependencias: `Flask`, `geopandas`, `shapely`, `requests` (ver `requirements.txt`)
- **Shapefiles** de Chile en `app/static/shapes/chile/`:
  - `regiones/Regional.shp`
  - `provincias/Provincias.shp`
  - `comunas/comunas.shp`
  - `regiones/regions.json`

> Los shapefiles no están versionados (`.gitignore`). Debes descargarlos por separado antes de ejecutar la aplicación.

---

## Ejecución local

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Exportar la API Key
export GEO_API_KEY=tu_clave_secreta

# 3. Ejecutar (requiere puerto como argumento)
python app/http-server.py 8075
```

El servidor escuchará en `0.0.0.0:8075`.

---

## Docker

```bash
# Construir imagen
docker build -t geoapi:prd .

# Ejecutar container
docker run -e GEO_API_KEY=tu_clave -p 8075:8075 geoapi:prd
```

> `docker-compose.yml` requiere un archivo de entorno externo (`../envs/file_geo.env`) y una red llamada `db-net`. Es poco probable que funcione sin crear estos recursos primero.

---

## Endpoints

Todas las peticiones deben incluir el header:

```
x-api-key: <GEO_API_KEY>
```

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/geo/regions` | Lista todas las regiones de Chile |
| `GET` | `/geo/{region_id}/provinces` | Lista provincias de una región |
| `GET` | `/geo/{region_id}/communes` | Lista comunas de una región |
| `POST` | `/geo/search` | Geocodifica una dirección |
| `POST` | `/geo/inside` | Verifica si un punto está dentro de una zona |

### Ejemplos

**Listar regiones:**
```bash
curl -H "x-api-key: tu_clave" http://localhost:8075/geo/regions
```

**Buscar dirección:**
```bash
curl -X POST http://localhost:8075/geo/search \
  -H "x-api-key: tu_clave" \
  -H "Content-Type: application/json" \
  -d '{"data": {"street": "Alameda 123", "city": "Santiago", "state": "Metropolitana", "country": "Chile"}}'
```

**Verificar punto dentro de una región:**
```bash
curl -X POST http://localhost:8075/geo/inside \
  -H "x-api-key: tu_clave" \
  -H "Content-Type: application/json" \
  -d '{"data": {"latitude": -33.45, "longitude": -70.67, "zone": {"region": "Metropolitana"}}}'
```

---

## Fuentes de datos geoespaciales

- [Biblioteca del Congreso Nacional (BCN) — Mapas vectoriales](https://www.bcn.cl/siit/mapas_vectoriales)
- [Geoportal Chile — División Política Administrativa 2023](https://www.geoportal.cl/geoportal/catalog/36391/Divisi%C3%B3n%20Pol%C3%ADtica%20Administrativa%202023)

---

## Autor

Jonnattan G
