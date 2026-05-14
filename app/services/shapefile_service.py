import os
import json
import logging
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import Point
from services.base_shapefile_service import BaseShapefileService

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ShapefileService(BaseShapefileService):
    _map_regs = None
    _map_prov = None
    _map_comn = None
    _regions = []
    _file_name_regs = None
    _file_name_prov = None
    _file_name_comn = None
    _initialized = False

    def __init__(self):
        cls = type(self)
        if not cls._initialized:
            self._init_paths()
            self._fill_regions()
            cls._initialized = True

    def _init_paths(self):
        file_path = os.path.join(ROOT_DIR, 'static', 'shapes', 'chile')
        cls = type(self)
        cls._file_name_regs = os.path.join(file_path, 'regiones', 'Regional.shp')
        cls._file_name_prov = os.path.join(file_path, 'provincias', 'Provincias.shp')
        cls._file_name_comn = os.path.join(file_path, 'comunas', 'comunas.shp')
        self._json_regions_file = os.path.join(file_path, 'regiones', 'regions.json')

    def _fill_regions(self):
        cls = type(self)
        try:
            with open(self._json_regions_file) as file:
                json_regions = json.load(file)
            cls._regions = json_regions.get('regiones', [])
        except Exception as e:
            logging.error(f"ERROR fill_regions: {e}")
            cls._regions = []

    def get_regions_list(self):
        return type(self)._regions

    def get_map(self, zone: str):
        logging.info(f"get_map: {zone}")
        cls = type(self)
        if zone is None:
            return None
        if 'reg' in zone:
            if cls._map_regs is None:
                cls._map_regs = gpd.read_file(cls._file_name_regs)
            return cls._map_regs
        if 'prov' in zone:
            logging.info(f"prov!!!")
            if cls._map_prov is None:
                cls._map_prov = gpd.read_file(cls._file_name_prov)
            return cls._map_prov
        if 'com' in zone:
            if cls._map_comn is None:
                cls._map_comn = gpd.read_file(cls._file_name_comn)
            return cls._map_comn
        return None

    def region_name(self, id: str):
        name = None
        try:
            maps = self.get_map('regs')
            ident, value = self.get_title_for_shape('regs')
            if maps is not None and not maps.empty:
                for _, mp in maps.iterrows():
                    if str(mp[ident]) == id:
                        name = str(mp[value])
                        break
        except Exception as e:
            logging.error(f"ERROR region_name: {e}")
        return name

    def get_list(self, shape: str, region: str):
        elements = []
        http_code = 404
        logging.info(f"get_list: {shape}")
        try:
            maps = self.get_map(shape)
            logging.info(f"maps: \n{maps}")
            if maps is not None and not maps.empty:
                ident, value = self.get_title_for_shape(shape)
                for _, mp in maps.iterrows():
                    if region == 'cl':
                        elements.append({'id': str(mp[ident]), 'value': str(mp[value])})
                    else:
                        if str(mp['codregion']) == region:
                            elements.append({'id': str(mp[ident]), 'value': str(mp[value])})
                http_code = 200
        except Exception as e:
            logging.error(f"ERROR get_list: {e}")
            elements = []
            http_code = 500
        return elements, http_code

    def get_title_for_shape(self, shape: str):
        if 'reg' in shape:
            return 'codregion', 'Region'
        if 'prov' in shape:
            return 'cod_prov', 'Provincia'
        if 'com' in shape:
            return 'cod_comuna', 'Comuna'
        if 'country' in shape:
            return '', 'NAME'
        return '', ''

    def get_zone_point(self, point: Point, zones: GeoDataFrame):
        zone = None
        try:
            if zones is None or zones.empty:
                return None
            for _, mp in zones.iterrows():
                if point.within(mp.geometry):
                    zone = mp
                    break
        except Exception as e:
            logging.error(f"ERROR get_zone_point: {e}")
        return zone

    def inside_verification(self, area, search: str, shape: str):
        is_equal = False
        try:
            if area is not None and not area.empty:
                _, finder = self.get_title_for_shape(shape)
                name = str(area[finder].values[0])
                is_equal = search.upper() == name.upper()
        except Exception as e:
            logging.error(f"ERROR inside_verification: {e}")
            is_equal = False
        return {'inside': is_equal}

    def get_zones(self, data_rx):
        search = None
        place = None
        if 'country' in data_rx:
            place = data_rx['country']
            search = 'country'
        if 'region' in data_rx:
            place = data_rx['region']
            search = 'regs'
        if 'province' in data_rx:
            place = data_rx['province']
            search = 'prov'
        if 'commune' in data_rx:
            place = data_rx['commune']
            search = 'comn'
        # 
        return str(place), search, self.get_map(search)
