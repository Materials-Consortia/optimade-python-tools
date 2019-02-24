from adapter import *

#### START SAMPLE DATA ####
alias = {
    "chemical_formula":"formula_anonymous",
    "formula_prototype": "pretty_formula",
}
endpoint = "https://materialsproject.org/optimade/0.9.6/structures"
params = {
    "filter": "nelements<3",
    "response_format": "json",
    "email_address": "dwinston@lbl.gov",
    "response_limit": "10",
    "response_fields": "id,nelements,material_id,elements,formula_prototype",
    "sort": "-nelements",
}
#### END SAMPLE DATA ####

def generateSampleURL(endpoint, params):
    return f"{endpoint}?{urlencode(params)}"
adaptor = Adapter(
                generateSampleURL(endpoint, params),
                MongoClient().test_database.test_collection,
                "mongoconverter",
                alias)
result = adaptor.getResponse()

pprint(adaptor.result)
