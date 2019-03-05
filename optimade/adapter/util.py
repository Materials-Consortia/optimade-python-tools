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

def parseArgs(path,args, alias={}):
    print()
    print(args)
    print()
    result = {}
    result['response_limit'] = int(args['response_limit'])
    result['response_fields'] = args['response_fields'].split(",")
    # swap content in query['response_fields'] to format in alias
    for i in range(len(args['response_fields'])):
        if(args['response_fields'][i] in alias):
            result['response_fields'][i] = alias[args['response_fields'][i]]
    #
    json_sort_query = args['sort']
    # change from json sorting format to mongoDB sorting method, TODO: change to support multiple sort objects
    if(json_sort_query.find("-") > -1):
        result['sort'] = (json_sort_query[json_sort_query.find("-")+1:], pymongo.ASCENDING)
    else:
        result['sort'] = (json_sort_query, pymongo.DESCENDING)
    splitted = path.split("/")
    #adding path params to the result
    result["endpoint"] = splitted[1]
    result["api_version"] = splitted[2] # assuming that our grammar is our api version
    result["entry"] = splitted[3]
    #
    result['query'] = "filter = %s" % args['filter']
    result.pop('filter',None)
    #
    out = subprocess.Popen(['mongoconverter', result['query']],
               stdout=subprocess.PIPE,
               stderr=subprocess.STDOUT)
    stdout,stderr = out.communicate()
    #
    # do i need to do try/except and throw custom error here?
    result['query'] = ast.literal_eval(stdout.decode("ascii"))

    # return result
    return result

def getDataFromCollection(collection, query):
    # print(result['sort'])
    cursor = collection.find(query['query'], projection=query['response_fields'])\
                            .sort([query['sort']])\
                            .limit(query['response_limit'])
    return cursor
