from urllib.parse import urlparse, quote_plus, urlencode, parse_qs
#### START SAMPLE DATA ####
alias = {
    "chemical_formula":"formula_anonymous",
    "formula_prototype": "pretty_formula",
}
endpoint = "http://127.0.0.1:5000/optimade/0.9.6/structures"
params = {
    "filter": "nelements<3",
    "response_format": "jsonapi",
    "email_address": "dwinston@lbl.gov",
    "response_limit": "10",
    "response_fields": "id,nelements,material_id,elements,formula_prototype",
    "sort": "-nelements",
    "page[number]": "1", # TODO what is the query param here??? not listed in the optimade api
}
#### END SAMPLE DATA ####
print(f"{endpoint}?{urlencode(params)}")

def generate(endpoint, params):
    return f"{endpoint}?{urlencode(params)}"
