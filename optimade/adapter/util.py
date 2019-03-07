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
    result = {}
    result['response_limit'] = int(args['response_limit'])
    result['response_fields'] = args['response_fields'].split(",")

    # swap content in query['response_fields'] to format in alias
    for i in range(len(args['response_fields'])):
        if(args['response_fields'][i] in alias):
            result['response_fields'][i] = alias[args['response_fields'][i]]

    # change from json sorting format to mongoDB sorting method, TODO: change to support multiple sort objects
    json_sort_query = args.get('sort')
    if(json_sort_query!= None):
        if(json_sort_query.find("-") > -1):
            result['sort'] = (json_sort_query[json_sort_query.find("-")+1:], pymongo.ASCENDING)
        else:
            result['sort'] = (json_sort_query, pymongo.DESCENDING)
    else:
        result['sort'] = []
    splitted = path.split("/")

    # adding contents in path.
    result["endpoint"] = splitted[len(splitted)-3]
    result["api_version"] = splitted[len(splitted)-2] # assuming that our grammar is our api version
    result["entry"] = splitted[len(splitted)-1]

    result['query'] = "filter = %s" % args['filter']
    result.pop('filter',None)
    # get output from your converter
    out = subprocess.Popen(['mongoconverter', result['query']],
               stdout=subprocess.PIPE,
               stderr=subprocess.STDOUT)
    stdout,stderr = out.communicate()
    # do i need to do try/except and throw custom error here?
    result['query'] = ast.literal_eval(stdout.decode("ascii"))
    return result

def getDataFromCollection(collection, query):
    # print(result['sort'])
    q = query.get('query')
    proj = query.get('response_fields')
    sorting = query.get('sort')
    limit = query.get('response_limit')
    cursor = None
    if(sorting == None):
        if(limit == None):
            cursor = collection.find(query.get('query'), projection=query.get('response_fields'))
        else:
            cursor = collection.find(query.get('query'), projection=query.get('response_fields'))\
                    .limit(query.get('response_limit'))
    else:
        cursor = collection.find(query.get('query'), projection=query.get('response_fields'))\
                            .sort([query.get('sort')])\
                            .limit(query.get('response_limit'))
    return cursor

def getData(collection, path, query):
    parsed_args = parseArgs(path,query, query)
    pprint(parsed_args)
    cursor = getDataFromCollection(collection, parsed_args)
    data = StructureSchema(many=True).dump(list(cursor)).data
    return data
