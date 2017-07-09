import geopy
import os

from constants import US_STATE_NAME_DICT, CA_PROVINCE_NAME_DICT

GOOGLE_SERVICE = 'GoogleV3'
SMARTYSTREETS_SERVICE = 'LiveAddress'
NOMINATIM_SERVICE = 'Nominatim'
LOCAL_USDATA_SERVICE = 'LocalUSDataProvider'

class Location(geopy.Location):
    """
    a light wrapper around the geopy location object
    which can return properties from the raw address_components 
    """

    def __init__(self, *args, **kwargs):
        if isinstance(args[0], basestring):
            super(Location, self).__init__(*args, **kwargs)
        else:
            self._wrapped_obj = args[0]

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        if attr == '_wrapped_obj':
            return self
        if attr in self._wrapped_obj.__dict__:
            return getattr(self._wrapped_obj, attr)
        else:
            raise AttributeError('Location object has no attribute %s' % attr)

    def _find_in_raw(self, field):
        """
        finds a component by type name in raw address_components
        """
        if not self.raw:
            return None

        if self.service == GOOGLE_SERVICE:
            # google style, raw.address_components are a list of dicts, with types in list
            for c in self.raw['address_components']:
                if field in c['types']:
                    return c['short_name']
            return None
            
        elif self.service == SMARTYSTREETS_SERVICE:
            # smarty streets style, raw.components are named
            return self.raw['components'].get(field)
        
        elif self.service == NOMINATIM_SERVICE:
            return self.raw['address'].get(field)

        elif self.service == LOCAL_USDATA_SERVICE:
            return self.raw.get(field)

        try:
            # try simple extraction from components
            return self.raw['components'].get(field)
        except KeyError, ValueError:
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
        if self.service == GOOGLE_SERVICE:
            return self._find_in_raw('administrative_area_level_1')
        elif self.service == SMARTYSTREETS_SERVICE:
            return self._find_in_raw('state_abbreviation')
        elif self.service == NOMINATIM_SERVICE:
            if self._find_in_raw('country_code') == 'us':
                state_name = self._find_in_raw('state')
                return US_STATE_NAME_DICT.get(state_name)
            elif self._find_in_raw('country_code') == 'ca':
                province_name = self._find_in_raw('state')
                return CA_PROVINCE_NAME_DICT.get(province_name)
        else:
            return self._find_in_raw('state')

    @property
    def latlon(self):
        lat = self.latitude
        lon = self.longitude
        return (lat, lon)

    @property
    def postal(self):
        if self.service == GOOGLE_SERVICE:
            return self._find_in_raw('postal_code')
        elif self.service == SMARTYSTREETS_SERVICE:
            return self._find_in_raw('zipcode')
        elif self.service == NOMINATIM_SERVICE:
            return self._find_in_raw('postcode')
        elif self.service == LOCAL_USDATA_SERVICE:
            return self._find_in_raw('zipcode')
        else:
            return self._find_in_raw('zipcode')


class LocationError(TypeError):
    pass

class Geocoder(object):
    """
    a light wrapper around the geopy client
    with configurable service name
    """

    def __init__(self, API_NAME=None, API_KEY=None, country='US'):
        if not API_NAME or API_KEY:
            # get keys from os.environ, because we may not have current_app context
            API_NAME = os.environ.get('GEOCODE_PROVIDER', 'nominatim')  # default to the FOSS provider
            API_KEY = os.environ.get('GEOCODE_API_KEY', None)

        service = geopy.geocoders.get_geocoder_for_service(API_NAME)
        self.country = country

        if API_NAME == 'nominatim':
                # nominatim sets country bias at init
                # and has no API_KEY
                self.client = service(country_bias=country, timeout=3)
        elif API_NAME == 'liveaddress':
            AUTH_TOKEN = os.environ.get('GEOCODE_API_TOKEN', None)
            self.client = service(API_KEY, AUTH_TOKEN, timeout=3)
        elif API_KEY:
            self.client = service(API_KEY, timeout=3)
        else:
            raise LocationError('configure your geocoder with environment variables GEOCODE_PROVIDER and GEOCODE_API_KEY')
            

    def get_service_name(self):
        "returns geopy.geocoder class name, like GoogleV3, LiveAddress, Nominatim, etc"
        return self.client.__class__.__name__.split('.')[-1]

    def postal(self, code, country='us', provider=None):
        if provider and country == 'us':
            districts = provider.get_districts(code)
            if len(districts) == 1:
                d = districts[0]
                l = Location(code, (None, None), d)
                l.service = 'LocalUSDataProvider'
                return l

        # fallback to geocoder if cache unavailable
        # or if there were multiple returns
        return self.geocode(code)

    def geocode(self, address):
        service = self.get_service_name()

        try:
            if service == GOOGLE_SERVICE:
                response = self.client.geocode(address, region=self.country)
                # bias responses to region/country (2-letter TLD)           
            if service == NOMINATIM_SERVICE:
                # nominatim won't return metadata unless we ask
                response = self.client.geocode(address, addressdetails=True)
            if service == SMARTYSTREETS_SERVICE:
                # smarty just return one response
                response = self.client.geocode(address, exactly_one=True)
            else:
                response = self.client.geocode(address)

            result = Location(response)
            result.service = service

        except geopy.exc.GeocoderTimedOut:
            result = Location()
            result.service = "Timeout"
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

        return Location(self.client.reverse((lat, lon)))
