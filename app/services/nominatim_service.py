import logging
import os
import requests
from urllib.parse import urlencode


class NominatimService:
    BASE_URL = os.environ.get('NOMINATIM_URL', 'https://nominatim.openstreetmap.org/search.php')
    TIMEOUT = int(os.environ.get('NOMINATIM_TIMEOUT', '20'))
    USER_AGENT = os.environ.get('NOMINATIM_USER_AGENT', 'geo-api/1.0.0')

    @staticmethod
    def search_address(request_data: dict):
        code = 409
        data = None
        try:
            params = {
                'street': request_data.get('street', ''),
                'city': request_data.get('city', ''),
                'state': request_data.get('state', ''),
                'country': request_data.get('country', ''),
                'format': 'jsonv2'
            }
            url = f"{NominatimService.BASE_URL}?{urlencode(params)}"
            headers = {
                'Accept': 'application/json',
                'User-Agent': NominatimService.USER_AGENT
            }
            logging.info(f"URL: {url}")
            resp = requests.get(url, headers=headers, timeout=NominatimService.TIMEOUT)
            logging.info(f"Http Response: {resp.status_code}")
            code = resp.status_code
            if resp.status_code == 200:
                data_response = resp.json()
                if len(data_response) > 0:
                    direction = data_response[0]
                    for value in data_response:
                        if value.get('type') == 'residential':
                            direction = value
                            break
                    data = {
                        'latitude': str(direction['lat']),
                        'longitude': str(direction['lon']),
                        'detail': str(direction['display_name']),
                        'type': str(direction['type'])
                    }
        except requests.exceptions.Timeout:
            logging.error("ERROR search_address: timeout contacting Nominatim")
            code = 504
        except Exception as e:
            logging.error(f"ERROR search_address: {e}")
        return data, code
