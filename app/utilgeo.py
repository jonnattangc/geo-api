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

    """
    Obtiene el mapa de datos de alguna zona particular 
    """
    def get_map(self, zone : str) :        
        if zone == None :
            return None
        elif zone.find('reg') >= 0 :
            if self.map_regs == None :
                self.map_regs =  gpd.read_file(self.file_name_regs)
            return self.map_regs
        elif zone.find('prov') >= 0 :
            if self.map_prov == None :
                self.map_prov =  gpd.read_file(self.file_name_prov)
            return self.map_prov
        elif zone.find('com') >= 0 :
            if self.map_comn == None :
                self.map_comn =  gpd.read_file(self.file_name_comn)
            return self.map_comn
        else :
            return None    
        return None

    def region_name(self, id: str) :
        name = None
        try :
            maps = self.get_map( 'regs' )
            ident, value = self.get_title_for_shape('regs')
            if not maps.empty :
                for index, mp in maps.iterrows() :
                    if str(mp[ident]) == id :
                        name =  str(mp[value])
                        break
        except Exception as e: 
            print("ERROR region_name:", e)
        return name
    def get_list( self, shape: str, region: str ) :
        elements = []
        http_code = 404
        try :
            logging.info('Busca ' + shape + ' de la region ' + region )
            maps = self.get_map(shape)
            if not maps.empty :
                ident, value = self.get_title_for_shape(shape)
                for index, mp in maps.iterrows() :
                    if region == 'cl' :
                        elements.append({'id': str(mp[ident]), 'value': str(mp[value])})
                    else:
                        if str(mp['CUT_REG']) == region :
                          elements.append({'id': str(mp[ident]), 'value': str(mp[value])})
                http_code = 200
        except Exception as e:
            print("ERROR get_list:", e)
            elements = []
            http_code = 500
        return elements, http_code
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
                _, finder = str(area[self.get_title_for_shape(shape)].values[0])
                is_equal = search.upper() == finder.upper()
                # logging.info(search.upper() + ' es igual a ' + finder.upper())
        except Exception as e:
            print("ERROR inside_verification:", e)
            is_equal = False
        return {'inside': is_equal }

    def get_title_for_shape(self, shape: str ) :
        if shape.find('reg') >= 0 :
            return 'CUT_REG', 'REGION'
        elif shape.find('prov') >= 0 :
            return 'CUT_PROV', 'PROVINCIA'
        elif shape.find('com') >= 0 :
            return 'CUT_COM', 'COMUNA'
        elif shape.find('country') >= 0 :
            return '', 'NAME'
        else :
            return '', ''
        return '', ''
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
            url = 'https://nominatim.openstreetmap.org/search.php?'
            url += 'street=' + str(request_data['street'])
            url += '&city=' + str(request_data['city'])
            url += '&state=' + str(request_data['state'])
            url += '&country=' + str(request_data['country'])
            url += '&format=jsonv2'
            #url += '&polygon_geojson=1'
            #url += '&addressdetails=1'
            headers = {
                'Accept': 'application/json', 
                'user-agent': 'jonnattan/1.0.0'
            }
            logging.info("URL : " + url )
            resp = requests.get(url, headers = headers, timeout = 20)
            logging.info('Http Response: ' + str(resp)  )
            code = resp.status_code
            if( resp.status_code == 200 ) :
                data_response = resp.json()
                logging.info("Response: " + str( data_response ) )
                if len(data_response) > 0 :
                    data = {
                        'latitude'  : str( data_response[0]['lat'] ),
                        'longitude' : str( data_response[0]['lon'] ),
                        'detail'    : str( data_response[0]['display_name'] )
                    }  
            else :
                data = None
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
            if request.method == 'POST' :
                request_data = request.get_json()
                json_data = request_data['data']
                logging.info("JSON : " + str(json_data) )
                if subpath == 'search' : 
                    data_response, http_code = self.search_address( json_data )
                elif subpath == 'inside' :
                    data_response, http_code = self.point_inside( json_data )
                else :
                    http_code = 404
                    message = "Servicio POST /geo/" + subpath + " no encontrado"
            elif request.method == 'GET' :
                if subpath.find('regions') >= 0 :
                    regiones, http_code = self.get_list( 'regions', 'cl' )
                    data_response = { 'regions': regiones}    
                elif subpath.find('provinces') >= 0 :
                    reg = subpath.replace('/provinces','')
                    provincias, http_code = self.get_list( 'provinces', reg )
                    data_response = { 'region': self.region_name(reg), 'provinces': provincias}    
                elif subpath.find('communes') >= 0 :
                    reg = subpath.replace('/communes','')
                    comunas, http_code = self.get_list( 'communes', reg )
                    data_response = { 'region': self.region_name(reg), 'communes': comunas}  
                else :
                    http_code = 404
                    message = "Servicio GET /geo/" + subpath + " no encontrado"
            else: 
                http_code = 404
                message = "Servicio no encontrado"
        except Exception as e:
            print("[UtilGeo] Error requestProcess:", e)

        logging.info("[UtilGeo] Servicio Ejecutado en " + str(time.monotonic() - m1) + " msec." )
        response = {"message" : message, "data": data_response }

        return response, http_code 