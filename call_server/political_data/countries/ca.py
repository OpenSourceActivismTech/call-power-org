from flask.ext.babel import gettext as _

import represent
from . import DataProvider, CampaignType

from ..geocode import Geocoder
from ..constants import CA_PROVINCES
from ...campaign.constants import (LOCATION_POSTAL, LOCATION_ADDRESS, LOCATION_LATLON)

import random
import logging
log = logging.getLogger(__name__)

class CACampaignType(CampaignType):
    pass


class CACampaignType_Local(CACampaignType):
    type_name = "Local"


class CACampaignType_Custom(CACampaignType):
    type_name = "Custom"


class CACampaignType_Executive(CACampaignType):
    type_name = "Executive"

    subtypes = [
        ('exec', _("Prime Minister")),
        ('office', _("Office"))
    ]

    def all_targets(self, location, campaign_region=None):
        return {
            'exec': self._get_executive()
        }

    def _get_executive(self):
        return self.data_provider.get_executive()


class CACampaignType_Parliament(CACampaignType):
    type_name = "Parliament"

    subtypes = [
        #('both', _("Both Bodies")),
        #('upper', _("Senate")),
        ('lower', _("House of Commons"))
    ]
    target_orders = [
        #('upper-first', _("Senate First")),
        ('lower-first', _("House of Commons"))
    ]

    def all_targets(self, location, campaign_region=None):
        return {
            #'upper': self._get_senator(location),
            'lower': self._get_member_of_parliament(location)
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

        return result

    def _get_member_of_parliament(self, location):
        reps = self.data_provider.get_representatives(location)
        filtered = self._filter_representatives(reps, "MP")
        return (r['boundary_key'] for r in filtered)

    def _filter_representatives(self, representatives, elected_office="MP", campaign_region=None):
        for boundary_key in representatives:
            rep = self.data_provider.get_boundary_key(boundary_key)
            correct_office = rep['elected_office'].upper() == elected_office
            in_region = campaign_region is None or rep['district_name'].upper() == campaign_region.upper()
            if correct_office and in_region:
                yield rep


class CACampaignType_Province(CACampaignType):
    type_name = "Province"

    subtypes = [
        ('exec', _("Premier")),
        # ('both', _("Legislature - Both Bodies")),
        # ('upper', _("Legislature - Upper Body")),
        ('lower', _("Legislature - Lower Body"))
    ]
    target_orders = [
        # ('shuffle', _("Shuffle")),
        # ('upper-first', _("Upper First")),
        ('lower-first', _("Lower First"))
    ]

    @property
    def region_choices(self):
        return CA_PROVINCES

    def get_subtype_display(self, subtype, campaign_region=None):
        display = super(CACampaignType_Province, self).get_subtype_display(subtype, campaign_region)
        if display:
            return "{} - {}".format(campaign_region, display)
        else:
            return display

    def all_targets(self, location, campaign_region=None):
        return {
            'exec': self._get_state_governor(location, campaign_region),
            'lower': self._get_province_representative(location, campaign_region),
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

    def _get_province_executive(self, location, campaign_region=None):
        return self.data_provider._get_province_executive(location)

    def _get_province_representative(self, location, campaign_region=None):
        reps = self.data_provider.get_representatives(location)
        # TODO, check "MNA" vs "MLA"
        filtered = self._filter_representatives(reps, "MLA", campaign_region)
        return (r['boundary_key'] for r in filtered)

    def _filter_representatives(self, representatives, elected_office="MP", campaign_region=None):
        for boundary_key in representatives:
            rep = self.data_provider.get_boundary_key(boundary_key)
            correct_office = rep['elected_office'].upper() == elected_office
            in_region = campaign_region is None or rep['district_name'].upper() == campaign_region.upper()
            if correct_office and in_region:
                yield rep


class CADataProvider(DataProvider):
    country_name = "Canada"

    campaign_types = [
        ('executive', CACampaignType_Executive),
        ('parliament', CACampaignType_Parliament),
        ('province', CACampaignType_Province),
        ('local', CACampaignType_Local),
        ('custom', CACampaignType_Custom)
    ]

    KEY_OPENNORTH = 'ca:opennorth:{boundary}'

    def __init__(self, cache, **kwargs):
        super(CADataProvider, self).__init__(**kwargs)
        self._cache = cache
        self._geocoder = Geocoder(country='CA')

    def get_location(self, locate_by, raw):
        if locate_by == LOCATION_POSTAL:
            return self._geocoder.postal(raw)
        elif locate_by == LOCATION_ADDRESS:
            return self._geocoder.geocode(raw)
        elif locate_by == LOCATION_LATLON:
            return self._geocoder.reverse(raw)
        else:
            return None


    def load_data(self):
        # we don't have an easy mapping of postcode to riding
        # so just hit OpenNorth with every request and cache responses
        log.info('no data to load for political_data.countries.ca')
        return 0
        

    # convenience methods for easy district access
    def get_executive(self):
        # return Prime Minister's comment line
        return [{'office': 'Prime Minister\'s Office',
                'number': '16139924211'}]


    def get_postcode(self, postcode):
        return represent.postcode(code=postcode)


    def get_representatives(self, location):
        if not location.latitude and location.longitude:
            raise LocationError('CADataProvider.get_representatives requires location with lat/lon')

        point = "{},{}".format(location.latitude, location.longitude)
        reps = represent.representative(point=point)  # add throttle=False here to avoid rate limits

        # calculate keys and cache responses
        keys = []
        for rep in reps:
            boundary_key = self.boundary_url_to_key(rep['related']['boundary_url'])
            cache_key = self.KEY_OPENNORTH.format(boundary=boundary_key)
            rep['boundary_key'] = boundary_key
            self.cache_set(cache_key, rep)
            keys.append(boundary_key)

        return keys


    def get_boundary_key(self, boundary_key):
        key = self.KEY_OPENNORTH.format(boundary=boundary_key)
        return self.cache_get(key, dict())


    def boundary_url_to_key(self, related_url):
        # convert OpenNorth's related boundary url to cache key
        boundary = related_url.strip('/')
        boundary = boundary.replace('boundaries/', '')
        key = boundary.replace('/', ':')
        return key

