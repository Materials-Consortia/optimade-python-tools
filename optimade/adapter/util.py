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
from globals import PAGE_LIMIT

#### Start of Helper methods for parseURL ####
def initalizeQueryParam(queryParam):
    # queryParam['response_message'] = []
    queryParam['status'] = 200
    queryParam['error_message'] = []
def fillFilter(queryParam, args, alias):
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
        print("curernt query = ", queryParam['query'])
    args.pop('filter', None)
def fillResponseFormat(queryParam, args):
    queryParam['response_format'] = args['response_format'][0] if args.get('response_format') != None else "jsonapi"
    args.pop('response_format',None)
    if(queryParam.get('response_format','jsonapi') != 'jsonapi'):
        queryParam['status'] = 400
        queryParam['error_message'].append("Currently only support jsonapi response format, but resquested <{}>".format(queryParam.get('response_format')))
def fillEmailAddress(queryParam, args):
    queryParam['email_address'] = args['email_address'][0] if args.get('email_address') != None else  None
    args.pop('email_address',None)
def fillResponseLimit(queryParam, args):
    queryParam['response_limit'] = int(args['response_limit'][0]) if args.get('response_limit',None) != None else PAGE_LIMIT
    if(queryParam['response_limit'] > PAGE_LIMIT):
        queryParam['error_message'].append("Input response_limit is <{}>, greater than database page limit <{}>, will default to database page limit.".format(queryParam['response_limit'], PAGE_LIMIT))
        queryParam['status'] = 400
    args.pop('response_limit')
def fillResponseFields(queryParam, args, alias):
    queryParam['response_fields'] = None
    if(args.get('response_fields') != None):
        fields = args['response_fields'][0].split(",")
        queryParam['response_fields'] = [alias[field] if field in alias  else field for field in fields ]
    args.pop('response_fields', None)
def fillPagination(queryParam, args):
    queryParam['page'] = int(args['page'][0]) if args.get('page') != None else 1
    if(queryParam['page'] <= 0):
        queryParam['status'] = 400
        queryParam['error_message'].append(\
                                    "Page = {} but have to Page has to be greater than or equal to 1"\
                                    .format(queryParam['page']))
    args.pop('page', None)
def fillSortFields(queryParam, args):
    # change from json sorting format to mongoDB sorting method, TODO: change to support multiple sort objects
    if(args.get('sort') != None):
        json_sort_query = args.get('sort')[0]
        if(json_sort_query.find("-") > -1):
            queryParam['sort'] = [(json_sort_query[json_sort_query.find("-")+1:], pymongo.ASCENDING)]
        else:
            queryParam['sort'] = [(json_sort_query, pymongo.DESCENDING)]
    else:
        queryParam['sort'] = None
    args.pop('sort', None)
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
def fillMPSpecificParams(queryParam, args):
    matching_db_list = []
    for arg in args:
        start_index = arg.find("mp_")
        if(arg[0:3] == "mp_"):
            key = arg[3:]
            queryParam[key] = args[arg][0]
            matching_db_list.append(arg)
    for match in matching_db_list:
        args.pop(match)

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
    initalizeQueryParam(queryParam)
    fillFilter(queryParam, args, alias)
    fillResponseFormat(queryParam, args)
    fillEmailAddress(queryParam, args)
    fillResponseLimit(queryParam, args)
    fillResponseFields(queryParam, args, alias)
    fillOtherOptionalFields(url, queryParam, path, args)
    fillPagination(queryParam, args)
    fillMPSpecificParams(queryParam, args)

    if(len(args) > 0):
        queryParam['status'] = 400
        queryParam['error_message'].append("Unknown Params detected: {}".format(str(args)))
    return queryParam

def getDataFromCollection(collection, query):
    pageSize = query.get('response_limit')
    cursor = collection.find(filter=query.get('query',None),
                            projection=query.get('response_fields', None),
                            skip=(query.get('page')-1) * pageSize,
                            limit=pageSize,
                            no_cursor_timeout=query.get('no_cursor_timeout', False),
                            sort=query.get('sort', None),
                            allow_partial_results=query.get('allow_partial_results', False),
                            oplog_replay=query.get('oplog_replay', False),
                            modifiers=query.get('modifiers', None),
                            batch_size=query.get('batch_size', 0),
                            manipulate=query.get('manipulate', True),
                            collation=query.get('collation', None),
                            hint=query.get('hint', None),
                            max_scan=query.get('max_scan', None),
                            max_time_ms=query.get('max_time_ms', None),
                            max=query.get('max', None),
                            min=query.get('min', None),
                            return_key=query.get('return_key', False),
                            show_record_id= query.get('show_record_id', False) == "True" or query.get('show_record_id', False) == "true",
                            snapshot=query.get('snapshot', False),
                            comment=query.get('comment', None),
                            session=query.get('session', None)
                            )
    return cursor
def getResponse(collection, url, alias={}):
    parsed_args = parseURL(url, alias)
    if(parsed_args.get('status', None) == 200):
        cursor = getDataFromCollection(collection, parsed_args)
        data = StructureSchema(many=True).dump(list(cursor)).data
        meta = Meta(collection, parsed_args, data, cursor.clone())
        link = Links(collection, parsed_args, cursor.clone(), url)
        result = {"data": data['data'], "meta":meta.getMetaData()["meta"], "links":link.getLinkData()["links"]}
        return result
    else:
        return {"ERROR": parsed_args}
def debugPrinting(parsed_args, data, result):
    # print("########## START OF DEBUGGING  ##########")
    # print()
    # print("### START OF parsed_args  ###")
    # pprint(parsed_args)
    # print("### END OF parsed_args  ###")
    # print()
    #
    # print()
    # print("### START OF data  ###")
    # pprint(data)
    # print("### END OF data  ###")
    # print()
    # pprint(result)
    print("########## END OF DEBUGGING  ##########")
