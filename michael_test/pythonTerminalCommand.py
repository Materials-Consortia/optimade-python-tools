import os, subprocess
from urllib.parse import urlparse,quote_plus,parse_qs
import pymongo
from pymongo import MongoClient
from urllib.parse import urlparse, quote_plus, urlencode, parse_qs
import ast
def parseURL(url):
    """
    @param url: input url
    @return 1. path -- the path of user's request, ex: /optimade/0.9.6/structures
            2. query -- user's query fields which is a dictionary with keys filter,
                        response_format, email_address, response limit, response_fields,
                        and sort
    """
    parsed = urlparse(url)
    path = parsed.path
    query = parse_qs(parsed.query)
    alias = {
        "chemical_formula":"formula_anonymous",
        "pretty_formula": "formula_prototype",
    }
    query['response_limit'] = int(query['response_limit'][0])
    query['response_fields'] = query['response_fields'][0].split(",")
    # swap content in query['response_fields'] to format in alias
    for i in range(len(query['response_fields'])):
        if(query['response_fields'][i] in alias):
            query['response_fields'][i] = alias[query['response_fields'][i]]

    json_sort_query = query['sort'][0]
    # change from json sorting format to mongoDB sorting method, TODO: change to support multiple sort objects
    if(json_sort_query.find("-") > -1):
        query['sort'] = (json_sort_query[json_sort_query.find("-")+1:], pymongo.ASCENDING)
    else:
        query['sort'] = (json_sort_query, pymongo.DESCENDING)
    splitted = path.split("/")
    #adding path params to the result
    query["endpoint"] = splitted[1]
    query["grammar"] = splitted[2]
    query["entry"] = splitted[3]

    query['query'] = "filter = %s" % query['filter'][0]
    query.pop('filter',None)

    # calling mongo converter to convert query['query'], but that is not working, so temporary solution:
    out = subprocess.Popen(['mongoconverter', query['query']],
               stdout=subprocess.PIPE,
               stderr=subprocess.STDOUT)
    stdout,stderr = out.communicate()
    # print(stdout.decode("ascii"))
    # do i need to do try/except and throw custom error here?
    query['query'] = ast.literal_eval(stdout.decode("ascii"))

    # query['query'] = {'nelements': {'$lt': 3.0}}
    return query
def concatinator(endpoint, params):
    return f"{endpoint}?{urlencode(params)}"

endpoint = "https://materialsproject.org/optimade/0.9.6/structures"
params = {
    "filter": "nelements<3",
    "response_format": "json",
    "email_address": "dwinston@lbl.gov",
    "response_limit": "10",
    "response_fields": "id,nelements,chemical_formula",
    "sort": "-nelements",
}
url = concatinator(endpoint, params)
#print("url = " + url)

result = parseURL(url)
# print("Result from parseURL = ", result)

client = MongoClient()
db=client.test_database
test_collection = db.test_collection
# print(result['sort'])
cursor = test_collection.find(result['query'], projection=result['response_fields'])\
                        .sort([result['sort']])\
                        .limit(result['response_limit'])
# TODO: ask winston what does pagination do?
# i read up a little bit and it seems like this sort is already doing pagination by doing the limit thing
# for i in cursor:
#     print(i)


### BELOW IS MARSHMALLOW MODEL ###
from marshmallow_jsonapi import Schema, fields
class Compound():
    def __init__(self, elements, nelements, pretty_formula, formula_anonymous, material_id):
        self.elements = elements
        self.nelements = nelements
        self.pretty_formula = pretty_formula
        self.formula_anonymous = formula_anonymous
        self.material_id = material_id
        self.id = material_id

class CompoundSchema(Schema):
#     chemsys = fields.Str()
    elements = fields.List(fields.String)
    nelements = fields.Int()
    pretty_formula = fields.Str()
    formula_anonymous = fields.Str()
    material_id = fields.Str()
    id = fields.Str()

    class Meta:
        type_ = "compound"
        strict = True

compound_schema = CompoundSchema()


# import pymongo
# from pymongo import MongoClient
# client = MongoClient()
# db=client.test_database
# test_collection = db.test_collection
# cursor = test_collection.find()
# counter = 0
# data = []
for document in cursor:
    print(document) #todo: build compound according to what user passed in
    d = CompoundSchema().dump( Compound(
                                    document["elements"],
                                    document["nelements"],
                                    document["pretty_formula"],
                                    document["formula_anonymous"],
                                    document["material_id"]))
    data.append(d)
## TODO: build a more generic return type that contains
# {
# 	"endpoint": "https://materialsproject.org/optimade/0.9.6/structures"
# 	"email_address": "dwinston@lbl.gov",
# 	"response_format": "json",
# 	"data": [
# 		{CompoundSceheme}
# 		{CompoundScheme}
# 	]
#
# }

print(data)
