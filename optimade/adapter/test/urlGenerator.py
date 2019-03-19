from urllib.parse import urlparse, quote_plus, urlencode, parse_qs
#### START SAMPLE DATA ####
alias = {
    "chemical_formula":"formula_anonymous",
    "formula_prototype": "pretty_formula",
}
base_url = "http://127.0.0.1:5000/optimade/0.9.6/"
entry_point = "structures"
params = {
    "filter": "nelements<3",
    "response_format": "jsonapi",
    "email_address": "dwinston@lbl.gov",
    "response_limit": 500,
    "response_fields": "id,nelements,material_id,elements,formula_prototype",
    "sort": "-nelements",
    "page": 5,
}
#### END SAMPLE DATA ####
print(f"{base_url}{entry_point}?{urlencode(params)}")

def generate(base_url, entry_point, params):
    return f"{base_url}{entry_point}?{urlencode(params)}"
