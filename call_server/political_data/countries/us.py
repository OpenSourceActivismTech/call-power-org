from flask.ext.babel import gettext as _
from sunlight import openstates, response_cache

from . import DataProvider, CampaignType

from ..geocode import Geocoder
from ..constants import US_STATES
from ...campaign.constants import (LOCATION_POSTAL, LOCATION_ADDRESS,
                                   LOCATION_LATLON)

import csv
import collections
import random
import itertools


class USCampaignType(CampaignType):
    pass


class USCampaignType_Local(USCampaignType):
    type_name = "Local"


class USCampaignType_Custom(USCampaignType):
    type_name = "Custom"


class USCampaignType_Executive(USCampaignType):
    type_name = "Executive"

    subtypes = [
        ('exec', _("President")),
        ('office', _("Office"))
    ]

    def all_targets(self, location, campaign_region=None):
        return {
            'exec': self._get_executive()
        }

    def _get_executive(self):
        return self.data_provider.get_executive()


class USCampaignType_Congress(USCampaignType):
    type_name = "Congress"

    subtypes = [
        ('both', _("Both Bodies")),
        ('upper', _("Senate")),
        ('lower', _("House"))
    ]
    target_orders = [
        ('shuffle', _("Shuffle")),
        ('upper-first', _("Senate First")),
        ('lower-first', _("House First"))
    ]

    @property
    def region_choices(self):
        return US_STATES

    def all_targets(self, location, campaign_region=None):
        return {
            'upper': self._get_congress_upper(location),
            'lower': self._get_congress_lower(location)
        }

    def sort_targets(self, targets, subtype, order):
        result = []

        if subtype == 'both':
            if order == 'upper-first':
                result.extend(targets.get('upper'))
                result.extend(targets.get('lower'))
            else:
                result.extend(targets.get('lower'))
                result.extend(targets.get('upper'))
        elif subtype == 'upper':
            result.extend(targets.get('upper'))
        elif subtype == 'lower':
            result.extend(targets.get('lower'))

        if order == 'shuffle':
            random.shuffle(result)

        return result

    def _get_congress_upper(self, location):
        districts = self.data_provider.get_districts(location.zipcode)
        # This is a set because zipcodes may cross states
        states = set(d['state'] for d in districts)

        for state in states:
            for senator in self.data_provider.get_senators(state):
                yield self.data_provider.KEY_BIOGUIDE.format(**senator)

    def _get_congress_lower(self, location):
        districts = self.data_provider.get_districts(location.zipcode)

        for district in districts:
            rep = self.data_provider.get_house_members(district['state'], district['house_district'])[0]
            yield self.data_provider.KEY_BIOGUIDE.format(**rep)


class USCampaignType_State(USCampaignType):
    type_name = "State"

    subtypes = [
        ('exec', _("Governor")),
        ('both', _("Legislature - Both Bodies")),
        ('upper', _("Legislature - Upper Body")),
        ('lower', _("Legislature - Lower Body"))
    ]
    target_orders = [
        ('shuffle', _("Shuffle")),
        ('upper-first', _("Upper First")),
        ('lower-first', _("Lower First"))
    ]

    @property
    def region_choices(self):
        return US_STATES

    def get_subtype_display(self, subtype, campaign_region=None):
        display = super(USCampaignType_State, self).get_subtype_display(subtype, campaign_region)
        if display:
            return "{} - {}".format(campaign_region, display)
        else:
            return display

    def all_targets(self, location, campaign_region=None):
        # FIXME: For exec, use campaign state by default. Not user-provided location.
        #        I don't know why this doesn't apply everywhere.
        return {
            'exec': self._get_state_governor(location, campaign_region),
            'upper': self._get_state_upper(location, campaign_region),
            'lower': self._get_state_lower(location, campaign_region)
        }

    def sort_targets(self, targets, subtype, order):
        result = []

        if subtype == 'both':
            if order == 'upper-first':
                result.extend(targets.get('upper'))
                result.extend(targets.get('lower'))
            else:
                result.extend(targets.get('lower'))
                result.extend(targets.get('upper'))
        elif subtype == 'upper':
            result.extend(targets.get('upper'))
        elif subtype == 'lower':
            result.extend(targets.get('lower'))

        if order == 'shuffle':
            random.shuffle(result)

        return result

    def _get_state_governor(self, location, campaign_region=None):
        return self.data_provider.get_state_governor(location)

    def _get_state_upper(self, location, campaign_region=None):
        legislators = self.data_provider.get_state_legislators(location.latlon)
        filtered = self._filter_legislators(legislators, campaign_region)
        return (l for l in filtered if l['chamber'] == 'upper')

    def _get_state_lower(self, location, campaign_region=None):
        legislators = self.data_provider.get_state_legislators(location.latlon)
        filtered = self._filter_legislators(legislators, campaign_region)
        return (l for l in filtered if l['chamber'] == 'lower')

    def _filter_legislators(self, legislators, campaign_region=None):
        for legislator in legislators:
            is_active = legisator['active']
            in_state = campaign_region is None or legislator['state'].upper() == campaign_region.upper()
            if is_active and in_state:
                yield legislator


class USDataProvider(DataProvider):
    country_name = "United States"

    campaign_types = [
        ('executive', USCampaignType_Executive),
        ('congress', USCampaignType_Congress),
        ('state', USCampaignType_State),
        ('local', USCampaignType_Local),
        ('custom', USCampaignType_Custom)
    ]

    KEY_BIOGUIDE = 'us:bioguide:{bioguide_id}'
    KEY_HOUSE = 'us:house:{state}:{district}'
    KEY_SENATE = 'us:senate:{state}'
    KEY_OPENSTATES = 'us_state:openstates:{id}'
    KEY_GOVERNOR = 'us_state:governor:{state}'
    KEY_ZIPCODE = 'us:zipcode:{zipcode}'

    def __init__(self, cache, api_cache=None, **kwargs):
        super(USDataProvider, self).__init__(**kwargs)
        self.cache = cache
        self.geocoder = Geocoder()
        if api_cache is not None:
            response_cache.enable(api_cache)

    def get_location(self, locate_by, raw):
        if locate_by == LOCATION_POSTAL:
            return self.geocoder.zipcode(raw)
        elif locate_by == LOCATION_ADDRESS:
            return self.geocoder.geocode(raw)
        elif locate_by == LOCATION_LATLON:
            return self.geocoder.reverse(raw)
        else:
            return None

    def _load_legislators(self):
        """
        Load US legislator data from saved file
        Returns a dictionary keyed by state to cache for fast lookup

        eg us:senate:CA = [{'title':'Sen', 'first_name':'Dianne',  'last_name': 'Feinstein', ...},
                           {'title':'Sen', 'first_name':'Barbara', 'last_name': 'Boxer', ...}]
        or us:house:CA:13 = [{'title':'Rep', 'first_name':'Barbara',  'last_name': 'Lee', ...}]
        """
        legislators = collections.defaultdict(list)

        with open('call_server/political_data/data/us_legislators.csv') as f:
            reader = csv.DictReader(f)

            for l in reader:
                if l['in_office'] != '1':
                    # skip if out of office
                    continue

                direct_key = self.KEY_BIOGUIDE.format(**l)
                legislators[direct_key].append(l)

                if l['senate_class']:
                    l['chamber'] = 'senate'
                    chamber_key = self.KEY_SENATE.format(**l)
                else:
                    l['chamber'] = 'house'
                    chamber_key = self.KEY_HOUSE.format(**l)
                legislators[chamber_key].append(l)

        return legislators

    def _load_districts(self):
        """
        Load US congressional district data from saved file
        Returns a dictionary keyed by zipcode to cache for fast lookup

        eg us:zipcode:94612 = [{'state':'CA', 'house_district': 13}]
        or us:zipcode:54409 = [{'state':'WI', 'house_district': 7}, {'state':'WI', 'house_district': 8}]
        """
        districts = collections.defaultdict(list)

        with open('call_server/political_data/data/us_districts.csv') as f:
            reader = csv.DictReader(
                f, fieldnames=['zipcode', 'state', 'house_district'])

            for d in reader:
                cache_key = self.KEY_ZIPCODE.format(**d)
                districts[cache_key].append(d)

        return districts

    def _load_governors(self):
        """
        Load US state governor data from saved file
        Returns a dictionary keyed by state to cache for fast lookup

        eg us:governor:CA = {'title':'Governor', 'name':'Jerry Brown Jr.', 'phone': '18008076755'}
        """
        governors = collections.defaultdict(dict)

        with open('call_server/political_data/data/us_states.csv') as f:
            reader = csv.DictReader(f)

            for l in reader:
                direct_key = self.KEY_GOVERNOR.format(**{'state': l['state']})
                d = {
                    'title': 'Governor',
                    'name': l.get('name'),
                    'phone': l.get('phone'),
                    'state': l.get('state')
                }
                governors[direct_key] = d
        return governors

    def load_data(self):
        districts = self._load_districts()
        legislators = self._load_legislators()
        governors = self._load_governors()

        if hasattr(self.cache, 'set_many'):
            self.cache.set_many(districts)
            self.cache.set_many(legislators)
            self.cache.set_many(governors)
        elif hasattr(self.cache, 'update'):
            self.cache.update(legislators)
            self.cache.update(districts)
            self.cache.update(governors)
        else:
            raise AttributeError('cache does not appear to be dict-like')

        return len(districts) + len(legislators) + len(governors)

    def cache_set(self, key, val):
        if hasattr(self.cache, 'set'):
            self.cache.set(key, val)
        elif hasattr(self.cache, 'update'):
            self.cache.update({key: val})
        else:
            raise AttributeError('cache does not appear to be dict-like')

    # convenience methods for easy house, senate, district access
    def get_executive(self):
        # return Whitehouse comment line
        return [{'office': 'Whitehouse Comment Line',
                'number': '12024561111'}]

    def get_house_members(self, state, district):
        key = self.KEY_HOUSE.format(state=state, district=district)
        return self.cache.get(key, list())

    def get_senators(self, state):
        key = self.KEY_SENATE.format(state=state)
        return self.cache.get(key, list())

    def get_districts(self, zipcode):
        key = self.KEY_ZIPCODE.format(zipcode=zipcode)
        return self.cache.get(key, dict())

    def get_governor(self, state):
        cache_key = self.KEY_GOVERNOR.format(state=state)
        return self.cache.get(cache_key) or {}

    def locate_governor(self, state):
        return [self.KEY_GOVERNOR.format(state=state)]

    def get_state_legislators(self, latlon):
        if type(latlon) == tuple:
            lat = latlon[0]
            lon = latlon[1]
        else:
            try:
                (lat, lon) = latlon.split(',')
            except ValueError:
                raise ValueError('USStateData requires location as lat,lon')

        return openstates.legislator_geo_search(lat, lon)

    def get_legid(self, legid):
        cache_key = self.KEY_OPENSTATES.format(id=legid)
        return self.get_key(cache_key) or {}

    def get_bioguide(self, uid):
        key = self.KEY_BIOGUIDE.format(bioguide_id=uid)
        return self.cache.get(key, dict())

    def get_uid(self, key, default=dict()):
        return self.cache.get(key, default)
