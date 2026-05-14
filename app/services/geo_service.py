import logging
from shapely.geometry import Point
from services.base_shapefile_service import BaseShapefileService
from services.nominatim_service import NominatimService


class GeoService:
    def __init__(self, shapefile_service: BaseShapefileService = None):
        self.shapefile_service = shapefile_service or BaseShapefileService.create()
        self.nominatim_service = NominatimService()

    def get_regions(self):
        regiones, http_code = self.shapefile_service.get_list('regions', 'cl')
        return {'regions': regiones}, http_code

    def get_provinces(self, region_id: str):
        logging.info(f"get_provinces: {region_id}")
        provincias, http_code = self.shapefile_service.get_list('provinces', region_id)
        return {
            'region': self.shapefile_service.region_name(region_id),
            'provinces': provincias
        }, http_code

    def get_communes(self, region_id: str):
        comunas, http_code = self.shapefile_service.get_list('communes', region_id)
        return {
            'region': self.shapefile_service.region_name(region_id),
            'communes': comunas
        }, http_code

    def search_address(self, data: dict):
        return self.nominatim_service.search_address(data)

    def point_inside(self, data: dict):
        code = 401
        result = {'inside': False}
        try:
            lat = float(data['latitude'])
            lon = float(data['longitude'])
            point = Point(lon, lat)
            finder, shape, elements = self.shapefile_service.get_zones(data['zone'])
            logging.info(f"point_inside: search {finder} in {shape}\n{elements}")
            area = self.shapefile_service.get_zone_point(point, elements)
            logging.info(f"point_inside: {area}")
            result = self.shapefile_service.inside_verification(area, finder, shape)
            code = 200
        except Exception as e:
            logging.error(f"ERROR point_inside: {e}")
        return result, code
