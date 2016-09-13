from countries import us, us_state

COUNTRIES = {
    'us': 'countries.us.USDataProvider'
}

class NoDataError(Exception):
    def __init__(self, country_code):
        self.message = "No political data available for '{}'".format(country_code)


def get_country(country_code):
    path = COUNTRIES.get(country_code)

    if path is None:
        raise NoDataError(country_code)

    try:
        module, class_name = path.rsplit('.')
    except ValueError:
        raise NoDataError(country_code)

    try:
        module = __import__(module_name)
        data = getattr(module, class_name)
    except ImportError, AttributeError:
        raise NoDataError(country_code)
    else:
        return data

def load_data(cache):
    us_data = us.USData(cache)
    us_state_data = us_state.USStateData(cache)

    n = 0
    n += us_data.load_data()
    n += us_state_data.load_data()
    return n
