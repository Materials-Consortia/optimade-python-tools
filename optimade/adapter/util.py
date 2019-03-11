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
import sys

#### Start of Helper methods for parseURL ####
def initializeParsedResult(queryParam):
        ## the must haves in the spec, set to default values if not later overwrote
        queryParam['filter'] = None
        queryParam['response_format'] = None
        queryParam['email_address'] = None
        queryParam['response_limit'] = 10; # default response_limit = 10
        queryParam['response_fields'] = []

def fillFilter(queryParam, args):
    queryParam['query'] = None
    if(args.get('filter') != None):
        queryParam['query'] = "filter = %s" % args['filter'][0]
        queryParam.pop('filter',None)
        # get output from your converter
        out = subprocess.Popen(['mongoconverter', queryParam['query']],
                   stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT)
        stdout,stderr = out.communicate()
        # do i need to do try/except and throw custom error here?
        queryParam['query'] = ast.literal_eval(stdout.decode("ascii"))
def fillResponseFormat(queryParam, args):
    queryParam['response_format'] = args['response_format'][0] if args.get('response_format') != None else None
def fillEmailAddress(queryParam, args):
    queryParam['email_address'] = args['email_address'][0] if args.get('email_address') != None else  None
def fillResponseLimit(queryParam, args):
    queryParam['response_limit'] = int(args['response_limit'][0]) if args.get('response_limit') != None else sys.maxsize
def fillResponseFields(queryParam, args, alias):
    queryParam['response_fields'] = None
    if(args.get('response_fields') != None):
        fields = args['response_fields'][0].split(",")
        queryParam['response_fields'] = [alias[field] if field in alias  else field for field in fields ]

def fillSortFields(queryParam, args):
    # change from json sorting format to mongoDB sorting method, TODO: change to support multiple sort objects
    if(args.get('sort') != None):
        json_sort_query = args.get('sort')[0]
        if(json_sort_query.find("-") > -1):
            queryParam['sort'] = (json_sort_query[json_sort_query.find("-")+1:], pymongo.ASCENDING)
        else:
            queryParam['sort'] = (json_sort_query, pymongo.DESCENDING)
    else:
        queryParam['sort'] = []
def fillOtherOptionalFields(url, queryParam, path, args):
    fillSortFields(queryParam, args)
    splitted = path.split("/")
    # adding contents in path.
    queryParam["endpoint"] = splitted[1]
    queryParam["api_version"] = splitted[2] # assuming that our grammar is our api version
    queryParam["entry"] = splitted[3]


    entry_point_index = url.find(splitted[3])
    queryParam["representation"] = url[entry_point_index:]
    queryParam["base_url"] = url[:entry_point_index]

#### End of Helper methods for parseURL ####

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
    args = parse_qs(parsed.query)

    queryParam = {}
    initializeParsedResult(queryParam)
    fillFilter(queryParam, args)
    fillResponseFormat(queryParam, args)
    fillEmailAddress(queryParam, args)
    fillResponseLimit(queryParam, args)
    fillResponseFields(queryParam, args, alias)
    fillOtherOptionalFields(url, queryParam, path, args)
    return queryParam

def getDataFromCollection(collection, query):
    cursor = collection.find(filter=query.get('query'),
                             projection=query.get('response_fields'),
                             limit=query.get('response_limit'))
    if(query.get('sort')):
        cursor.sort([query.get('sort')])
    return cursor


def getResponse(collection, url, alias={}):
    parsed_args = parseURL(url, alias)
    if(parsed_args.get('response_format') == 'jsonapi'):
        cursor = getDataFromCollection(collection, parsed_args)
        data = StructureSchema(many=True).dump(list(cursor)).data
        meta = Meta(collection, cursor, parsed_args, data)
        link = Link(collection, cursor, parsed_args)
        # debugPrinting(parsed_args, data)
        return {"data": data['data'], "meta":meta.getMetaData()["meta"], "link":link.getLinkData()["link"]}
    else:
        class FormatNotImplementedError(Exception):
            pass
        raise FormatNotImplementedError("Format <{}> is not implemented".format(parsed_args.get('response_format')))
def debugPrinting(parsed_args, data):
    print("########## START OF DEBUGGING  ##########")
    print()
    print("### START OF parsed_args  ###")
    pprint(parsed_args)
    print("### END OF parsed_args  ###")
    print()

    print()
    print("### START OF data  ###")
    pprint(data)
    print("### END OF data  ###")
    print()
    print("########## END OF DEBUGGING  ##########")
