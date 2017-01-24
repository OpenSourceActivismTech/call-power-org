import logging

from run import BaseTestCase

from call_server.political_data.lookup import locate_targets
from call_server.political_data.countries.ca import CADataProvider
from call_server.political_data.geocode import Location
from call_server.campaign.models import Campaign


class TestData(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        # quiet logging
        logging.getLogger(__name__).setLevel(logging.WARNING)

        cls.mock_cache = {}  # mock flask-cache outside of application context
        cls.ca_data = CADataProvider(cls.mock_cache)
        # cls.ca_data.load_data()

    def setUp(self):
        self.PARLIAMENT_CAMPAIGN = Campaign(
            country_code='ca',
            campaign_type='parliament',
            campaign_subtype='lower',
            target_ordering='in-order',
            locate_by='address')

    def test_cache(self):
        self.assertIsNotNone(self.mock_cache)
        self.assertIsNotNone(self.ca_data)

    def test_postcodes(self):
        riding = self.ca_data.get_postcode('L5G4L3')
        self.assertEqual(riding['province'], 'ON')
        self.assertEqual(riding['city'], 'Mississauga')

    def test_locate_targets(self):
        location_address = "1588 S Service Rd Mississauga, ON, Canada"
        keys = locate_targets(location_address, self.PARLIAMENT_CAMPAIGN, self.mock_cache)
        # returns a list of target boundary keys
        self.assertEqual(len(keys), 1)

        mp = self.ca_data.get_boundary_key(keys[0])
        self.assertEqual(mp['elected_office'], 'MP')
        self.assertEqual(mp['representative_set_name'], 'House of Commons')
        self.assertEqual(mp['district_name'].replace(u"\u2014", "-"), 'Mississauga-Lakeshore')
