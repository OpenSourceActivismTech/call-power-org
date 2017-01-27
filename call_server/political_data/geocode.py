import geopy
import os

from constants import US_STATE_NAME_DICT

GOOGLE_SERVICE = 'GoogleV3'
SMARTYSTREETS_SERVICE = 'LiveAddress'
NOMINATIM_SERVICE = 'Nominatim'

class Location(geopy.Location):
    """
    a light wrapper around the geopy location object
    which can return properties from the raw address_components 
    """

    def _find_in_raw(self, field):
        """
        finds a component by type name in raw address_components
        """
        if self.service is GOOGLE_SERVICE:
            # google style, raw.address_components are a list of dicts, with types in list
            for c in raw['address_components']:
                if 'field' in c['types']:
                    return c['short_name']
            return None
            
        elif self.service is SMARTYSTREETS_SERVICE:
            # smarty streets style, raw.components are named
            return self.raw['components'].get(field)
        
        elif self.service is NOMINATIM_SERVICE:
            return self.raw['address'].get(field)

        try:
            # try simple extraction from components
            return self.raw['components'].get(field)
        except ValueError:
            raise NotImplementedError('unable to parse address components from geocoder service '+self.service)

    @property
    def service(self):
        if hasattr(self, '_service'):
            return self._service
        else:
            return "UnknownService"

    @service.setter
    def service(self, value):
        self._service = value

    @property
    def state(self):
        if self.service is GOOGLE_SERVICE:
            return self._find_in_raw('administrative_area_level_1')
        elif self.service is SMARTYSTREETS_SERVICE:
            return self._find_in_raw('state_abbreviation')
        elif self.service is NOMINATIM_SERVICE:
            state_name = self._find_in_raw('state')
            return US_STATE_NAME_DICT.get(state_name)
        else:
            return self._find_in_raw('state')

    @property
    def latlon(self):
        lat = self.latitude
        lon = self.longitude
        return (lat, lon)

    @property
    def postal(self):
        if self.service is GOOGLE_SERVICE:
            return self._find_in_raw('postal_code')
        elif self.service is SMARTYSTREETS_SERVICE:
            return self._find_in_raw('zipcode')
        elif self.service is NOMINATIM_SERVICE:
            return self._find_in_raw('postcode')
        else:
            return self._find_in_raw('zipcode')


class LocationError(TypeError):
    pass

class Geocoder(object):
    """
    a light wrapper around the geopy client
    with configurable service name
    """

    def __init__(self, API_NAME=None, API_KEY=None, country='us'):
        if not API_NAME or API_KEY:
            # get keys from os.environ, because we may not have current_app context
            API_NAME = os.environ.get('GEOCODE_PROVIDER', 'nominatim')  # default to the FOSS provider
            API_KEY = os.environ.get('GEOCODE_API_KEY', None)

        service = geopy.geocoders.get_geocoder_for_service(API_NAME)
        if API_KEY:
            self.client = service(API_KEY)
        else:
            if API_NAME == 'nominatim':
                # nominatim sets country bias at init
                self.client = service(country_bias=country)
            else: 
                self.client = service()

    def get_service_name(self):
        "returns geopy.geocoder class name, like GoogleV3, LiveAddress, Nominatim, etc"
        return self.client.__class__.__name__.split('.')[-1]

    def postal(self, code, country='us', cache=None):
        if cache and country is 'us':
            districts = cache.get_districts(code)
            if len(districts) == 1:
                d = districts[0]
                l = Location(d, (None, None), d)
                l.service = 'LocalUSDistrictCache'
                return l

        # fallback to geocoder if cache unavailable
        # or if there were multiple returns
        return self.geocode(code, country)

    def geocode(self, address):
        service = self.get_service_name()

        if service is GOOGLE_SERVICE:
            # bias responses to region/country (2-letter TLD)
            result = self.client.geocode(address, region=self.country)
        if service is NOMINATIM_SERVICE:
            # nominatim won't return metadata unless we ask
            result = self.client.geocode(address, addressdetails=True)
        else:
            result.service = self.client.geocode(address)
        return result

    def reverse(self, latlon):
        if type(latlon) == tuple:
            lat = latlon[0]
            lon = latlon[1]
        else:
            try:
                (lat, lon) = latlon.split(',')
            except ValueError:
                raise ValueError('unable to parse latlon as either tuple or comma delimited string')

        return self.client.reverse((lat, lon))
