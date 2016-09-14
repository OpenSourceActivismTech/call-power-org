import countries
import importlib

COUNTRIES = {
    'us': 'call_server.political_data.countries.us.USDataProvider'
}

class NoDataProviderError(Exception):
    def __init__(self, country_code):
        self.message = "No data provider available for country code '{}'".format(country_code)


def get_country_data(country_code, **kwargs):
    path = COUNTRIES.get(country_code)

    if path is None:
        raise NoDataProviderError(country_code)

    try:
        module_name, class_name = path.rsplit('.', 1)
    except ValueError:
        raise NoDataProviderError(country_code)

    try:
        module = importlib.import_module(module_name)
        dataProviderClass = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise NoDataProviderError(country_code)
    else:
        return dataProviderClass(**kwargs)

def load_data(cache):
    n = 0

    for country_code in COUNTRIES.keys():
        country_data = get_country_data(country_code, cache=cache)
        n += country_data.load_data()

    return n
