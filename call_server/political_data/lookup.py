from ..extensions import cache
from ..campaign.constants import INCLUDE_CUSTOM_FIRST, INCLUDE_CUSTOM_LAST, INCLUDE_CUSTOM_ONLY

def locate_targets(location, campaign, cache=cache):
    """
    Convenience method to get targets for location in a given campaign.
    @return  list of target uids
    """

    campaign_data = campaign.get_campaign_data(cache)
    location_targets = campaign_data.get_targets_for_campaign(location, campaign)
    custom_targets = [t.uid for t in campaign.target_set]

    if campaign.target_set:
        if campaign.target_ordering == 'shuffle':
            random.shuffle(custom_targets)

        if campaign.include_custom == INCLUDE_CUSTOM_FIRST:
            return custom_targets + location_targets
        elif campaign.include_custom == INCLUDE_CUSTOM_LAST:
            return location_targets + custom_targets
        elif campaign.include_custom == INCLUDE_CUSTOM_ONLY:
            return custom_targets
        else:
            return custom_targets
    else:
        return location_targets
