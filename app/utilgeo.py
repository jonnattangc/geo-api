try:
    import logging
    import sys
    import os
    import time
    import requests
    import geopandas as gpd
    from geopandas import GeoDataFrame
    from shapely.geometry import Point

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[UtilGeo] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class UtilGeo() :
    map_regs = None
    map_prov = None
    map_comn = None
    file_name_regs : str = None
    file_name_prov : str = None
    file_name_comn : str = None 
    api_key = None

    def __init__(self, root = str(ROOT_DIR) ) :
        try :
            self.api_key = os.environ.get('GEO_API_KEY','NO_INFO')
            file_path = os.path.join(root, 'static')
            file_path = os.path.join(file_path, 'shapes')
            file_path = os.path.join(file_path, 'chile')
            self.file_name_regs = file_path + '/REGIONES/REGIONES_v1.shp'
            self.file_name_prov = file_path + '/PROVINCIAS/PROVINCIAS_v1.shp'
            self.file_name_comn = file_path + '/COMUNAS/COMUNAS_v1.shp'
        except Exception as e:
            print("[GeoPosUtil] ERROR GEO:", e)
            self.api_key = None

    def __del__(self):
        self.api_key = None
        self.file_name_regs = None
        self.file_name_prov = None
        self.file_name_comn = None

    def get_map(self, zone : str) :
        if zone == None :
            return None
        elif zone == 'regs' :
            if self.map_regs == None :
                self.map_regs =  gpd.read_file(self.file_name_regs)
            return self.map_regs
        elif zone == 'prov' :
            if self.map_prov == None :
                self.map_prov =  gpd.read_file(self.file_name_prov)
            return self.map_prov
        elif zone == 'comn' :
            if self.map_comn == None :
                self.map_comn =  gpd.read_file(self.file_name_comn)
            return self.map_comn
        else :
            return None    
        return None

    def get_zones(self, data_rx ) :
        search = None
        place = None
        try :
            if 'country' in data_rx :
                place = data_rx['country']
                search = 'country'
            if 'region' in data_rx :
                place = data_rx['region']
                search = 'regs'
            if 'province' in data_rx :
                place = data_rx['province']
                search = 'prov'
            if 'commune' in data_rx :
                place = data_rx['commune']
                search = 'comn'
        except Exception as e:
             print("ERROR get_zone:", e)
        return str(place), search, self.get_map(search) 
    # ==============================================================================
    # Metodo que pregunta si un punto est'a dentro de un lugar
    # por una posici'on dentro del mapa
    # ==============================================================================
    def point_inside(self, data_rx ) :
        code = 401
        data = {'inside': False}
        try :
            lat = float(data_rx['latitude'])
            lon = float(data_rx['longitude'])
            point = Point( lon, lat )
            finder, shape, elements = self.get_zones(data_rx['zone'])
            # logging.info('Colunnas: ' + str(elements.columns))
            # logging.info('Buscar: ' + str(finder) + " en " + str(len(elements)) + " Elemementos")
            area = self.get_zone_point( point, elements )
            data = self.inside_verification( area, finder, shape )
            code = 200
        except Exception as e:
            print("ERROR point_inside:", e)
        return data, code
    
    def inside_verification( self, area, search : str, shape: str ) :
        is_equal = False
        try :
            if not area.empty :
                finder = str(area[self.get_title_for_shape(shape)].values[0])
                is_equal = search.upper() == finder.upper()
                # logging.info(search.upper() + ' es igual a ' + finder.upper())
        except Exception as e:
            print("ERROR inside_verification:", e)
            is_equal = False
        return {'inside': is_equal }

    def get_title_for_shape(self, shape: str ) :
        if shape == 'regs' :
            return 'REGION'
        elif shape == 'prov' :
            return 'PROVINCIA'
        elif shape == 'comn' :
            return 'COMUNA'
        elif shape == 'country' :
            return 'NAME'
        else :
            return ''
        return ''
    # ==============================================================================
    # Busca si un punto geografico pertenece a un Shape
    # ==============================================================================
    def get_zone_point(self, point: Point, zones: GeoDataFrame ) :
        zone = None
        coordenadas = None
        try :
            if not zones.empty :
                point_gdf = GeoDataFrame(geometry=[point], crs=zones.crs)
                contains = zones.contains(point_gdf.geometry[0])
                zone = zones[contains]                
        except Exception as e:
            print("ERROR inside:", e)
        return zone
    # ==============================================================================
    # Busca la cordenada de una direcci'on en Chile
    # ==============================================================================
    def search_address(self, request_data ) :
        code = 409
        data = None
        try :
            address = str(request_data['address'])
            address = address.replace('pob', 'población')
            address = address.replace('depto', 'departamento')
            address = address.replace('block', 'edificio')
            address = address.replace('.', ' ')
            address = address.replace('  ', ' ')
            address = address.replace(' ', '+')
            logging.info("Addres: " + address )
            url = 'https://nominatim.openstreetmap.org/search?q=' + address
            #url += '&country=Chile'
            url += '&format=jsonv2'
            #url += '&polygon_geojson=1'
            #url += '&addressdetails=1'
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json' }
            m1 = time.monotonic_ns()
            logging.info("URL : " + url )
            resp = requests.get(url, headers = headers, timeout = 40)
            diff = time.monotonic_ns() - m1
            code = resp.status_code
            if( resp.status_code == 200 ) :
                data_response = resp.json()
                logging.info("Response: " + str( data_response ) )
                data = {
                    'latitude'  : str( data_response[0]['lat'] ),
                    'longitude' : str( data_response[0]['lon'] ),
                    'name'      : str( data_response[0]['display_name'] )
                }  
                code = 200
            else :
                data_response = resp.json()
                logging.info("Response: " + str( data_response ) )
        except Exception as e:
            print("ERROR search_address:", e)
        return data, code

    # ==============================================================================
    # Procesa todos los request 
    # ==============================================================================
    def request_process(self, request, subpath : str) :
        m1 = time.monotonic()
        message = "Servicio ejecutado exitosamente"
        http_code  = 200
        data_response = None
        response =  {"message" : message, "data": data_response}
        json_data = None
        logging.info("Reciv " + str(request.method) + " Contex: /geo/" + str(subpath) )
        #logging.info("Reciv Header :\n" + str(request.headers) )
        #logging.info("Reciv Data: " + str(request.data) )
        rx_api_key = request.headers.get('x-api-key')
        if rx_api_key == None or str(rx_api_key) != str(self.api_key) :
            response = {"message" : "No autorizado", "data": data_response }
            http_code  = 401
            return  response, http_code
        try :
            request_data = request.get_json()
            json_data = request_data['data']
            logging.info("JSON : " + str(json_data) )
            if subpath == 'search' : 
                data_response, http_code = self.search_address( json_data )
            elif subpath == 'inside' :
                data_response, http_code = self.point_inside( json_data )
        except Exception as e:
            print("[UtilGeo] Error requestProcess:", e)

        logging.info("[UtilGeo] Servicio Ejecutado en " + str(time.monotonic() - m1) + " msec." )
        response = {"message" : message, "data": data_response }

        return response, http_code 