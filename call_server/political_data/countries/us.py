import csv
import collections
import random

from . import DataProvider, CampaignType

from ...campaign.constants import (TARGET_CHAMBER_BOTH, TARGET_CHAMBER_UPPER, TARGET_CHAMBER_LOWER,
        ORDER_IN_ORDER, ORDER_SHUFFLE, ORDER_UPPER_FIRST, ORDER_LOWER_FIRST)

from ..geocode import Geocoder


class USCampaignType(CampaignType):
    pass


class USCampaignType_Executive(USCampaignType):
    name = "Executive"
    subtypes = [
        ('exec', "President"),
        ('office', "Office")
    ]

    def get_targets(self, location, campaign_region=None):
        return {
            'exec': list(self.data_provider.get_executive())
        }


class USCampaignType_Congress(USCampaignType):
    name = "Congress"
    subtypes = [
        ('upper', "Senate"),
        ('lower', "House")
    ]
    target_order_choices = [
        ('upper-first', "Senate First"),
        ('lower-first', "House First")
    ]

    def get_targets(self, location, campaign_region=None):
        return {
            'upper': list(self.data_provider.get_congress_upper(location)),
            'lower': list(self.data_provider.get_congress_lower(location))
        }


class USCampaignType_State(USCampaignType):
    name = "State"
    subtypes = [
        ('exec', "Governor"),
        ('upper', "Legislature - Upper Body"),
        ('lower', "Legislature - Lower Body")
    ]

    def get_targets(self, location, campaign_region=None):
        # FIXME: For exec, use campaign state by default. Not user-provided location.
        #        I don't know why this doesn't apply everywhere.
        return {
            'exec': list(self.data_provider.get_state_governor(location))
            'upper': list(self.data_provider.get_state_upper(location)),
            'lower': list(self.data_provider.get_state_lower(location))
        }


class USDataProvider(DataProvider):
    campaign_types = {
        'executive': USCampaignType_Executive,
        'congress': USCampaignType_Congress,
        'state': USCampaignType_State,
        # 'local': USCampaignType_Local,
        # 'custom': USCampaignType_Custom
    }

    KEY_BIOGUIDE = 'us:bioguide:{bioguide_id}'
    KEY_HOUSE = 'us:house:{state}:{district}'
    KEY_SENATE = 'us:senate:{state}'
    KEY_ZIPCODE = 'us:zipcode:{zipcode}'

    def __init__(self, cache):
        self.cache = cache
        self.geocoder = Geocoder()

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

    def load_data(self):
        districts = self._load_districts()
        legislators = self._load_legislators()

        if hasattr(self.cache, 'set_many'):
            self.cache.set_many(districts)
            self.cache.set_many(legislators)
        elif hasattr(self.cache, 'update'):
            self.cache.update(legislators)
            self.cache.update(districts)
        else:
            raise AttributeError('cache does not appear to be dict-like')

        return len(districts) + len(legislators)

    # convenience methods for easy house, senate, district access
    def get_house_member(self, state, district):
        key = self.KEY_HOUSE.format(state=state, district=district)
        return self.cache.get(key)

    def get_senators(self, state):
        key = self.KEY_SENATE.format(state=state)
        return self.cache.get(key) or []

    def get_districts(self, zipcode):
        return self.cache.get(self.KEY_ZIPCODE.format(zipcode=zipcode)) or {}

    def get_bioguide(self, uid):
        return self.cache.get(self.KEY_BIOGUIDE.format(bioguide_id=uid)) or {}

    def get_executive(self):
        # return Whitehouse comment line
        return [{'office': 'Whitehouse Comment Line',
                'number': '12024561111'}]

    def get_uid(self, key):
        return self.cache.get(key) or {}

    def get_congress_upper(self, location):
        districts = self.get_districts(location.zipcode)
        # This is a set because zipcodes may cross states
        states = set(d['state'] for d in districts)

        for state in states:
            for senator in self.get_senators(state):
                yield self.KEY_BIOGUIDE.format(**senator)

    def get_congress_lower(self, location):
        districts = self.get_districts(location.zipcode)

        for district in districts:
            rep = self.get_house_member(district['state'], district['house_district'])[0]
            yield self.KEY_BIOGUIDE.format(**rep)
