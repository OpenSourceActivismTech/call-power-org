import itertools

class DataProvider(object):
    campaign_types = dict()

    def __init__(self, **kwargs):
        pass

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

    def all_targets(self, location, campaign_region=None):
        """
        Find all targets for a location, crossing political boundaries if
        necessary.
        @return  a dictionary of target uids grouped by subtype.
        """
        raise NotImplementedError()

    def sort_targets(self, targets, subtype, order):
        """
        Sort and filter a dictionary of targets (grouped by subtype), as
        returned from all_targets, based on the provided subtype and order.
        @return  a list of sorted and filtered target uids
        """
        raise NotImplementedError()

    def get_targets_for_campaign(self, location, campaign):
        country_code = campaign.get_country_code()
        all_targets = self.all_targets(location, campaign.campaign_state)
        return self.sort_targets(all_targets, campaign.campaign_subtype, campaign.target_ordering)
