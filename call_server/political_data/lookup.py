from ..campaign.constants import (TYPE_CONGRESS, TYPE_STATE, TYPE_EXECUTIVE,
    TARGET_EXECUTIVE, TARGET_CHAMBER_BOTH, TARGET_CHAMBER_UPPER, TARGET_CHAMBER_LOWER,
    LOCATION_POSTAL, LOCATION_ADDRESS, LOCATION_LATLON,
    ORDER_IN_ORDER, ORDER_SHUFFLE, ORDER_UPPER_FIRST, ORDER_LOWER_FIRST)

from ..extensions import cache

from . import get_country_data


def locate_targets(location, campaign):
    """
    Locate targets for location for a given campaign.
    @return  list of target uids
    """

    if campaign.target_set:
        return [t.uid for t in campaign.target_set]
    else:
        country_code = campaign.get_country_code()
        country_data = get_country_data(country_code, cache=cache, api_cache='localmem')
        campaign_data = country_data.get_campaign_type(campaign.campaign_type)
        targets = campaign_data.get_targets(location, campaign.campaign_state)
        # TODO: Choose which targets to use based on campaign subtype (this returns a dictionary)
        # TODO: Sort targets based on campaign target_ordering
        return targets
