from . import get_country_data

def locate_targets(location, campaign):
    """
    Locate targets for location for a given campaign.
    @return  list of target uids
    """

    if campaign.target_set:
        return [t.uid for t in campaign.target_set]
    else:
        campaign_data = campaign.get_campaign_data()
        return campaign_data.get_targets_for_campaign(location, campaign)
