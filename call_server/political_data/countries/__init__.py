class DataProvider(object):
    campaign_types = dict()

    def get_campaign_type(self, type_id):
        type_class = self.campaign_types.get(type_id)
        return type_class(self)

    def load_data(self):
        """
        Loads all country-specific data and caches the result
        """
        raise NotImplementedError()


class CampaignType(object):
    name = None
    subtypes = []
    target_order_choices = []

    def __init__(self, data_provider):
        self.data_provider = data_provider

    @property
    def regions(self):
        """
        @return  a list of political regions for this campaign type
        """
        raise NotImplementedError()

    def get_targets(self, location, campaign_region=None):
        """
        Find all targets for a location, crossing political boundaries if
        necessary.
        @return  a dictionary of target uids grouped by subtype.
        """
        raise NotImplementedError()
