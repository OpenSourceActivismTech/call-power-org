from flask.ext.babel import gettext as _

class DataProvider(object):
    campaign_types = []

    def __init__(self, **kwargs):
        pass

    def load_data(self):
        """
        Loads all country-specific data and caches the result
        """
        raise NotImplementedError()

    @property
    def campaign_type_choices(self):
        return [(key, campaign_type.name) for key, campaign_type in self.campaign_types]

    def get_campaign_type(self, type_id):
        type_class = dict(self.campaign_types).get(type_id)
        return type_class(self)


class CampaignType(object):
    name = None
    subtypes = []
    target_orders = [
        ('in-order', _("In order"))
    ]

    def __init__(self, data_provider):
        self.data_provider = data_provider

    @property
    def region_choices(self):
        """
        @return  a list of political regions for this campaign type
        """
        return []

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

    @property
    def subtype_choices(self):
        return CampaignType.subtypes + self.subtypes

    def get_subtype_display(self, subtype, campaign_region=None):
        choices_dict = dict(self.subtype_choices)
        return choices_dict.get(subtype, None)

    @property
    def target_order_choices(self):
        return CampaignType.target_orders + self.target_orders

    def get_order_display(self, target_order):
        choices_dict = dict(self.target_order_choices)
        return choices_dict.get(target_order, None)

    def get_targets_for_campaign(self, location, campaign):
        country_code = campaign.get_country_code()
        all_targets = self.all_targets(location, campaign.campaign_state)
        return self.sort_targets(all_targets, campaign.campaign_subtype, campaign.target_ordering)
