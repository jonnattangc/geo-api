import logging
import requests


class NominatimService:
    @staticmethod
    def search_address(request_data: dict):
        code = 409
        data = None
        try:
            url = (
                f"https://nominatim.openstreetmap.org/search.php?"
                f"street={request_data['street']}"
                f"&city={request_data['city']}"
                f"&state={request_data['state']}"
                f"&country={request_data['country']}"
                f"&format=jsonv2"
            )
            headers = {
                'Accept': 'application/json',
                'user-agent': 'jonnattan/1.0.0'
            }
            logging.info(f"URL: {url}")
            resp = requests.get(url, headers=headers, timeout=20)
            logging.info(f"Http Response: {resp}")
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
            else:
                data = None
        except Exception as e:
            logging.error(f"ERROR search_address: {e}")
        return data, code
