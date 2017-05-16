from flask import current_app
from collections import OrderedDict

from ..extensions import cache
from ..campaign.constants import INCLUDE_CUSTOM_FIRST, INCLUDE_CUSTOM_LAST, INCLUDE_CUSTOM_ONLY, SEGMENT_BY_LOCATION


def locate_targets(location, campaign, skip_custom=False, cache=cache):
    """
    Convenience method to get targets for location in a given campaign.
    Assumes campaign.segment_by == SEGMENT_BY_LOCATION
    If skip_custom is true, will only return location-based targets
    @return  list of target uids
    """

    if campaign.segment_by and campaign.segment_by != SEGMENT_BY_LOCATION:
        current_app.logger.error('Called locate_targets on campaign where segment_by=%s (%s)' % (campaign.segment_by, campaign.id))
        return []

    campaign_data = campaign.get_campaign_data(cache)
    location_targets = campaign_data.get_targets_for_campaign(location, campaign)
    custom_targets = [t.uid for t in campaign.target_set]

    if skip_custom:
        return location_targets

    if campaign.target_set:
        if campaign.target_ordering == 'shuffle':
            random.shuffle(custom_targets)

        if campaign.include_custom == INCLUDE_CUSTOM_FIRST:
            combined = custom_targets + location_targets
            return list(OrderedDict.fromkeys(combined))
        elif campaign.include_custom == INCLUDE_CUSTOM_LAST:
            combined = location_targets + custom_targets
            return list(OrderedDict.fromkeys(combined))
        elif campaign.include_custom == INCLUDE_CUSTOM_ONLY:
            # find overlap between custom_targets and location_targets
            overlap = set(custom_targets).intersection(set(location_targets))
            return list(overlap)
        else:
            return custom_targets
    else:
        return location_targets
