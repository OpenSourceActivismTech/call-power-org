COUNTRIES = {
    'us': 'countries.us.USDataProvider'
}

class NoDataError(Exception):
    def __init__(self, country_code):
        self.message = "No political data available for '{}'".format(country_code)


def get_country_data(country_code):
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
    n = 0

    for country_code in COUNTRIES.keys():
        country_data = get_country_data(country_code)
        n += country.load_data()

    return n
