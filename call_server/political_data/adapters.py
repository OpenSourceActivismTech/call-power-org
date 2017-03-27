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


class UnitedStatesData(object):
    def target(self, data):
        return {       
            'name': u'{first_name} {last_name}'.format(**data),
            'number': data['phone'], # DC office number
            'title': data['title'],
            'uid': data['bioguide_id']
        }

    def offices(self, data):
        # district office numbers
        office_list = []
        for office in data.get('offices', []):
            if not office['phone']:
                continue
            office_data = {
                'name': office['city'],
                'address': u'{address} {building} {city} {state}'.format(**office),
                'number': office['phone']
            }
            if 'latitude' in office and 'longitude' in office:
                office_data['location'] = 'POINT({latitude}, {longitude})'.format(**office),
            office_list.append(office_data)
        return office_list


class OpenStatesData(object):
    def target(self, data):
        return {
            'name': data['full_name'],
            'title': 'Senator' if data['chamber'] == "upper" else "Represenatative",
            'number': filter(lambda d: d['type'] == 'capitol', data['offices'])[0].get('phone', None),
            'uid': data['leg_id']
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
                'name': office['name'],
                'address': office['address'],
                'number': office['phone']
            })
        return office_list


class GovernorAdapter(object):
    def target(self, data):
        return {
            'name': u'{first_name} {last_name}'.format(**data),
            'title': data['title'],
            'number': data['phone'],
            'uid': data['state'],
        }


class OpenNorthAdapter(object):
    def target(self, data):
        return {
            'name': u'{first_name} {last_name}'.format(**data),
            'title': data['elected_office'],
            'number': filter(lambda d: d['type'] == 'legislature', data['offices'])[0].get('tel', None),
            # legislature office number
            'uid': data['cache_key']
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
                'name': office['type'],
                'address': office['postal'],
                'number': office['tel']
            })
        return office_list

