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
import configparser

#### Start of Helper methods for parseURL ####
def initalizeQueryParam(queryParam):
    """
    Summary:
        initialize query parameters

    Extended Description:
        initiaize status and error message parameters

    Args:
        queryParam(dict): desired dictionary to append status and error_message in
    """

    queryParam['status'] = 200
    queryParam['error_message'] = []
def fillFilter(queryParam, args, alias_file_path):
    """
    Summary:
        add the filter parameter if it exist
    Extended Description:
        Step 1: if the filter parameter does not exist, append only None to queryParam's query field
        Step 2: if the filter parameter exist, get the original filter parameter
        Step 3: if the alias_file_path is not None, call mongoconverter with alias_file_path
        Step 4: if alias_file_path is None, call mongoconverter without alias_file_path
        Step 5: asscii decode the response from mongoconverter and replace with original filter.
    Args:
        queryParam(dict): all parameters, to be appended to.
        args(dict): original input dictionary, information to be extracted from
        alias_file_path(string): where the config file exist, if None, no config file is attached
    """
    queryParam['query'] = None
    if(args.get('filter', None) != None):
        queryParam['query'] = "filter = %s" % args['filter'][0]
        queryParam.pop('filter', None)
        args.pop('filter', None)
        # get output from your converter

        try:
            # command = 'mongoconverter "filter=chemical_formula=O2"'
            if(alias_file_path):
                out = subprocess.Popen(['mongoconverter', queryParam['query'], '-config', alias_file_path],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
            else:
                out = subprocess.Popen(['mongoconverter', queryParam['query']],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
            stdout,stderr = out.communicate()
        except subprocess.CalledProcessError as e:
            raise e


        # do i need to do try/except and throw custom error here?
        queryParam['query'] = ast.literal_eval(stdout.decode("ascii"))
def fillResponseFormat(queryParam, args):
    """
    Summary:
        append response format onto queryParam

    Extended Description:
        if the response format is not specified or is specified to be anything other than jsonapi, record an error and the correct message
    Args:
        queryParam(dict): all parameters, to be appended to.
        args(dict): original input dictionary, information to be extracted from
    """
    queryParam['response_format'] = args['response_format'][0] if args.get('response_format') != None else "jsonapi"
    args.pop('response_format',None)
    if(queryParam.get('response_format','jsonapi') != 'jsonapi'):
        queryParam['status'] = 400
        queryParam['error_message'].append("Currently only support jsonapi response format, but resquested <{}>".format(queryParam.get('response_format')))
def fillEmailAddress(queryParam, args):
    """
    Summary:
        fill email address
    Extended Description:
        fill the email address if it exist, otherwise record None
    Args:
        queryParam(dict): all parameters, to be appended to.
        args(dict): original input dictionary, information to be extracted from
    """
    queryParam['email_address'] = args['email_address'][0] if args.get('email_address') != None else  None
    args.pop('email_address',None)
def fillResponseLimit(queryParam, args):
    """
    Summary:
        fill response limit
    Extended Description:
        fill response limit if it exist, otherwise default to database limit specified by the global variable PAGE_LIMIT
        if the input response limit is greater than PAGE_LIMIT, record 400 error with corresponding message
    Args:
        queryParam(dict): all parameters, to be appended to.
        args(dict): original input dictionary, information to be extracted from
    """
    queryParam['response_limit'] = int(args['response_limit'][0]) if args.get('response_limit',None) != None else PAGE_LIMIT
    if(queryParam['response_limit'] > PAGE_LIMIT):
        queryParam['error_message'].append("Input response_limit is <{}>, greater than database page limit <{}>, will default to database page limit.".format(queryParam['response_limit'], PAGE_LIMIT))
        queryParam['status'] = 400
    args.pop('response_limit')
def fillResponseFields(queryParam, args,alias_file_path=None):
    """
    Summary:
        fill response fields
    Extended Description:
        read in alias_file_path if it exist and create the alias dictionary
        parse through fields in args and record the response fields, if it matches a key in alias, use the value of that key
    Args:
        queryParam(dict): all parameters, to be appended to.
        args(dict): original input dictionary, information to be extracted from
        alias_file_path: the path where the alias file is
    """
     #### START OF READING ALIAS FROM CONFIG  ####
    config = configparser.ConfigParser()
    config.read(alias_file_path)
    class ConfigFileNotFoundException(Exception):
        pass
    if(not (config.has_section('aliases') )):
        raise ConfigFileNotFoundException("Config File Not Found at Location: {}".format(args.Config))
    alias = dict()
    if(config.has_section('aliases')):
        d = dict(config.items('aliases'))
        for key in d:
            alias[key] = config['aliases'][key]
    #### END OF READING ALIAS FROM CONFIG  ####

    queryParam['response_fields'] = None
    if(args.get('response_fields') != None):
        fields = args['response_fields'][0].split(",")
        queryParam['response_fields'] = [alias[field] if field in alias  else field for field in fields ]
        # queryParam['response_fields'] = [field for field in fields]
    args.pop('response_fields', None)
def fillPagination(queryParam, args):
    """
    Summary:
        fill pagination information

    Extended Description:
        fill in pagination information, if the page requested is less than 0, then append error message
        if no pagination information specified, default to start at page 1
    Args:
        queryParam(dict): all parameters, to be appended to.
        args(dict): original input dictionary, information to be extracted from

    """
    queryParam['page'] = int(args['page'][0]) if args.get('page') != None else 1
    if(queryParam['page'] <= 0):
        queryParam['status'] = 400
        queryParam['error_message'].append(\
                                    "Page = {} but have to Page has to be greater than or equal to 1"\
                                    .format(queryParam['page']))
    args.pop('page', None)
def fillSortFields(queryParam, args):
    """
    Summary:
        fill sorting information

    Extended Description:
        if sort is not specified, set sort to None, otherwise, get the sort, and convert it to pymongo format and append it
    Args:
        queryParam(dict): all parameters, to be appended to.
        args(dict): original input dictionary, information to be extracted from

    """
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
    """
    Summary:
        fill other miscellaneous fields
    Extended Description:
        filling fields of
            - endpoint
            - apio_version
            - entry
            - representation
            - base_url
    Args:
        url(string): input url
        queryParam(dict): all parameters, to be appended to.
        path: first part of the url
        args(dict): original input dictionary, information to be extracted from
    Return:
    """
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
    """
    Summary:
        fill database specific information

    Extended Description:
        check if the prefix matches desired database prefix, append the param after removing the prefix if it is matches

    Args:
        queryParam(dict): all parameters, to be appended to.
        args(dict): original input dictionary, information to be extracted from
    """
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

def parseURL(url, alias_file_path):
    """
    Summary:

    Extended Description:


    Args:
        url(string): input url
    Return
        path -- the path of user's request, ex: /optimade/0.9.6/structures
        query -- user's query fields which is a dictionary with keys filter,
                response_format, email_address, response limit, response_fields, and sort
    """
    parsed = urlparse(url)
    path = parsed.path
    args = parse_qs(parsed.query)

    queryParam = {}
    initalizeQueryParam(queryParam)
    fillFilter(queryParam, args, alias_file_path)
    fillResponseFormat(queryParam, args)
    fillEmailAddress(queryParam, args)
    fillResponseLimit(queryParam, args)
    fillResponseFields(queryParam, args, alias_file_path)
    fillOtherOptionalFields(url, queryParam, path, args)
    fillPagination(queryParam, args)
    fillMPSpecificParams(queryParam, args)

    if(len(args) > 0):
        queryParam['status'] = 400
        queryParam['error_message'].append("Unknown Params detected: {}".format(str(args)))
    return queryParam

def getDataFromCollection(collection, query):
    """
    Summary:
    Get the data from collection

    Extended Description:
    Step 1: find out the correct pagination
    Step 2: generate a cursor that contains the correct attribute to go through the specified collection
    Step 3: return the cursor

    Args:
        collection(pymongo.collection): the desired collection to query through
        query(dict): contain relevant querying information
    Return:
        cursor(pymongo.cursor): cursor that has the correct attributes and is tagged to the correct collection
    """
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
def getResponse(collection, url, alias_file_path=None):
    """
    Summary:
    Called by server who received a request, connected to the correct database, and have configured aliases,
    return correct response per th

    Extended Description:
    Use the alias specified and given a a specific collection to find the data that the input URL specifies
    Step 1: Parse URL, do a short semantic check on whether the URL is according to Optimade specification
    Step 2: If URL is not per specification, throw the parsed URL and do not query the collection
    Step 3: If URL is per specification(code is 200), then first query through the linked collection, generate Meta data, and Links
    Step 4: Combine the Data, Meta, and Links, return it as a dictionary

    Args:
        collection(pymongo.collection): collection to query through
        url(String): input url, needs to be parsed to extract relavent information
        alias_file_path(String): None if no alias specified, otherwise needs to be read in as a config file
    Return:
        result: either a dictionary that contain ERROR and the parsed params, or the correct result in dictionary format
    """
    parsed_args = parseURL(url, alias_file_path)
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
    # print("########## END OF DEBUGGING  ##########")
    print("NOT BEGUGGING")
