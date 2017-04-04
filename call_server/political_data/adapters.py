# translate country specific data to campaign model field names


def adapt_by_key(key):
    if key.startswith("us:bioguide"):
        return UnitedStatesData()
    elif key.startswith("us_state:openstates"):
        return OpenStatesData()
    elif key.startswith("us_state:governor"):
        return GovernorAdapter()
    elif key.startswith("ca:opennorth"):
        return OpenNorthAdapter()
    else:
        return data
    # TODO add for other countries


class DataAdapter(object):
    def __init__(self, **kwargs):
        pass

    def key(self, key):
        return key       

    def target(self, data):
        raise NotImplementedError()

    def offices(self, data):
        raise NotImplementedError()


class UnitedStatesData(DataAdapter):
    def key(self, key):
        # split district office id from rest of bioguide
        if '-' in key:
            biogude, office = key.split('-')
            return bioguide
        else:
            return key

    def target(self, data):
        return {
            'name': u'{first_name} {last_name}'.format(**data),
            'number': data.get('phone', ''), # DC office number
            'title': data.get('title', ''),
            'uid': data.get('bioguide_id', '')
        }

    def offices(self, data):
        # district office numbers
        office_list = []
        for office in data.get('offices', []):
            if not office['phone']:
                continue
            office_data = {
                'name': office.get('city', ''),
                'number': office.get('phone', ''),
                'id': office.get('id', '')
            }
            if 'city' in office and 'state' in office:
                if 'address' in office and 'building' in office:
                    office_data['address'] = '{address} {building} {city} {state}'.format(**office)
                elif 'address' in office:
                    office_data['address'] = '{address} {city} {state}'.format(**office)
                else:
                    office_data['address'] = '{city} {state}'.format(**office)
            else:
                office_data['address'] = ''

            if 'latitude' in office and 'longitude' in office:
                office_data['location'] = 'POINT({latitude}, {longitude})'.format(**office)
            office_list.append(office_data)
        return office_list


class OpenStatesData(DataAdapter):
    def target(self, data):
        return {
            'name': data.get('full_name', ''),
            'title': 'Senator' if data['chamber'] == "upper" else "Represenatative",
            'number': filter(lambda d: d['type'] == 'capitol', data['offices'])[0].get('phone', ''),
            'uid': data.get('leg_id', '')
        }

    def offices(self, data):
        office_list = []
        for office in data.get('offices', []):
            if office['type'] == 'capitol':
                # capitol office is captured in target.number
                continue
            if not office['phone']:
                continue
            office_list.append({
                'name': office.get('name', ''),
                'address': office.get('address', ''),
                'number': office.get('phone', '')
            })
        return office_list


class GovernorAdapter(DataAdapter):
    def target(self, data):
        return {
            'name': u'{first_name} {last_name}'.format(**data),
            'title': data.get('title', ''),
            'number': data.get('phone', ''),
            'uid': data.get('state', ''),
        }


class OpenNorthAdapter(DataAdapter):
    def target(self, data):
        return {
            'name': u'{first_name} {last_name}'.format(**data),
            'title': data.get('elected_office', ''),
            'number': filter(lambda d: d['type'] == 'legislature', data['offices'])[0].get('tel', ''),
            # legislature office number
            'uid': data.get('cache_key', '')
        }

    def offices(self, data):
        office_list = []
        for office in data.get('offices', []):
            if office['type'] == 'legislature':
                # legislature office is captured in target.number
                continue
            if not office['tel']:
                continue
            office_list.append({
                'name': office.get('type', ''),
                'address': office.get('postal', ''),
                'number': office.get('tel', '')
            })
        return office_list

