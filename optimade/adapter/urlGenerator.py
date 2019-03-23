from urllib.parse import urlparse, quote_plus, urlencode, parse_qs
def generateFromString(base_url, entry_point, filterString):
    return f"{base_url}{entry_point}?{filterString}"
def generateFromDict(base_url, entry_point, params):
    return f"{base_url}{entry_point}?{urlencode(params)}"
