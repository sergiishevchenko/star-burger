import requests

from django.conf import settings
from .models import Location


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={"geocode": address, "apikey": apikey, "format": "json"})
    response.raise_for_status()

    found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    if not found_places:
        return None
    most_relevant = found_places[0]
    lng, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lng, lat


def get_or_create_locations(*addresses):
    api_key = settings.YANDEX_API_KEY
    addresses = [*addresses]
    locations = {locate.address: (locate.lat, locate.lng) for locate in Location.objects.filter(address__in=addresses)}

    for address in addresses:
        if address in [locate for locate in locations.keys()]:
            continue
        coordinates = fetch_coordinates(api_key, address)
        if coordinates:
            coordinates_lng, coordinates_lat = coordinates
        else:
            coordinates_lng, coordinates_lat = None, None
        new_locate = Location.objects.create(address=address, lat=coordinates_lat, lng=coordinates_lng)
        locations[new_locate.address] = (new_locate.lat, new_locate.lng)
    return locations


