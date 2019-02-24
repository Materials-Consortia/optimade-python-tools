from marshmallow_jsonapi import Schema, fields
from marshmallow import pprint
import os, subprocess
from urllib.parse import urlparse,quote_plus,parse_qs
import pymongo
from pymongo import MongoClient
from urllib.parse import urlparse, quote_plus, urlencode, parse_qs
import ast
import datetime
from models_schema import *
from marshmallow_jsonschema import JSONSchema

def parseURL(url, alias):
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

    result = {}
    result['response_limit'] = int(query['response_limit'][0])
    result['response_fields'] = query['response_fields'][0].split(",")
    # swap content in query['response_fields'] to format in alias
    for i in range(len(query['response_fields'])):
        if(query['response_fields'][i] in alias):
            result['response_fields'][i] = alias[query['response_fields'][i]]

    json_sort_query = query['sort'][0]
    # change from json sorting format to mongoDB sorting method, TODO: change to support multiple sort objects
    if(json_sort_query.find("-") > -1):
        result['sort'] = (json_sort_query[json_sort_query.find("-")+1:], pymongo.ASCENDING)
    else:
        quresultery['sort'] = (json_sort_query, pymongo.DESCENDING)
    splitted = path.split("/")
    #adding path params to the result
    result["endpoint"] = splitted[1]
    result["api_version"] = splitted[2] # assuming that our grammar is our api version
    result["entry"] = splitted[3]

    result['query'] = "filter = %s" % query['filter'][0]
    # result.pop('filter',None)

    out = subprocess.Popen(['mongoconverter', result['query']],
               stdout=subprocess.PIPE,
               stderr=subprocess.STDOUT)
    stdout,stderr = out.communicate()

    # do i need to do try/except and throw custom error here?
    result['query'] = ast.literal_eval(stdout.decode("ascii"))

    return result

def generateSampleURL(endpoint, params):
    return f"{endpoint}?{urlencode(params)}"

def getDataFromDb(query):


    client = MongoClient()
    db=client.test_database
    test_collection = db.test_collection
    # print(result['sort'])
    cursor = test_collection.find(query['query'], projection=query['response_fields'])\
                            .sort([query['sort']])\
                            .limit(query['response_limit'])
    return cursor
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

#### START OF PARSING URL ####
url = generateSampleURL(endpoint, params)
query = parseURL(url, alias)
#### END OF PARSING URL ####

# get data from database
cursor = getDataFromDb(query)

# organizing data into an array
data = []
data_returned_counter = 0
for document in cursor:
    # structure_schema = StructureSchema().dump(Structure(param=document))
    data.append(document)
    data_returned_counter += 1

# generating other information needed in the response per specification
data = Data(data)
# pprint(data.data)

# print(data_schema.data)
# print(data.data)
links = Links(None, None)
meta = Meta(
            query = {"representation":"/structures/?filter=a=1 AND b=2"},
            api_version = query.get("api_version"),
            time_stamp = datetime.datetime.utcnow().isoformat(),
            data_returned = data_returned_counter,
            more_data_available = True,
            )
#
#
links_schema = LinksSchema()
meta_schema = MetaSchema()
# data_schema = DataSchema()
#
#
# data_schema = data_schema.dump(data)
# pprint(data_schema.data)
#
# data = {"data": data.data}
# links = {"links": links_schema.dump(links).data['data']['attributes']}
# meta = {"meta": meta_schema.dump(meta).data}
#
#
# response = Response(links, meta, data)
# response_schema = ResponseSchema()
# #
# # # TODO: how to dump data...
# pprint(response_schema.dump(response).data)
result = {
        "links":links_schema.dump(links).data['data']['attributes'],
        "data":data.data,
        "meta":meta_schema.dump(meta).data}

pprint(result)
