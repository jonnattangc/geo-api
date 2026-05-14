import os
import logging
import time
from flask import Blueprint, request, jsonify
from services.geo_service import GeoService

geo_bp = Blueprint('geo', __name__)


@geo_bp.before_request
def validate_api_key():
    api_key = request.headers.get('x-api-key')
    expected = os.environ.get('GEO_API_KEY', 'NO_INFO')
    if api_key is None or str(api_key) != str(expected):
        logging.info(f"Token No autorizado: {api_key} != {expected}")
        return jsonify({"status": "NOK", "message": "Unauthorized"}), 401


@geo_bp.route('/regions', methods=['GET'])
def get_regions():
    start = time.monotonic()
    service = GeoService()
    data, status = service.get_regions()
    logging.info(f"[GeoController] GET /geo/regions executed in {time.monotonic() - start} sec")
    return jsonify(data), status


@geo_bp.route('/<region_id>/provinces', methods=['GET'])
def get_provinces(region_id):
    start = time.monotonic()
    service = GeoService()
    data, status = service.get_provinces(region_id)
    logging.info(f"[GeoController] GET /geo/{region_id}/provinces executed in {time.monotonic() - start} sec")
    return jsonify(data), status


@geo_bp.route('/<region_id>/communes', methods=['GET'])
def get_communes(region_id):
    start = time.monotonic()
    service = GeoService()
    data, status = service.get_communes(region_id)
    logging.info(f"[GeoController] GET /geo/{region_id}/communes executed in {time.monotonic() - start} sec")
    return jsonify(data), status


@geo_bp.route('/search', methods=['POST'])
def search_address():
    start = time.monotonic()
    request_data = request.get_json()
    data = request_data['data']
    service = GeoService()
    result, status = service.search_address(data)
    logging.info(f"[GeoController] POST /geo/search executed in {time.monotonic() - start} sec")
    return jsonify(result), status


@geo_bp.route('/inside', methods=['POST'])
def point_inside():
    start = time.monotonic()
    request_data = request.get_json()
    data = request_data['data']
    service = GeoService()
    result, status = service.point_inside(data)
    logging.info(f"[GeoController] POST /geo/inside executed in {time.monotonic() - start} sec")
    return jsonify(result), status
