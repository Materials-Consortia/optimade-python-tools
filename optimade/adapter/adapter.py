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


class Adapter():
    def __init__(self, URL,  mongoCollection, converter_name, alias = {}):
        self.url = URL
        self.mongoCollection = mongoCollection
        self.converter_name = converter_name
        self.alias = alias

    def parseURL(self, url, alias, converter_name):
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

        self.query = {}
        self.query['response_limit'] = int(query['response_limit'][0])
        self.query['response_fields'] = query['response_fields'][0].split(",")
        # swap content in query['response_fields'] to format in alias
        for i in range(len(query['response_fields'])):
            if(query['response_fields'][i] in alias):
                self.query['response_fields'][i] = alias[query['response_fields'][i]]

        json_sort_query = query['sort'][0]
        # change from json sorting format to mongoDB sorting method, TODO: change to support multiple sort objects
        if(json_sort_query.find("-") > -1):
            self.query['sort'] = (json_sort_query[json_sort_query.find("-")+1:], pymongo.ASCENDING)
        else:
            self.query['sort'] = (json_sort_query, pymongo.DESCENDING)
        splitted = path.split("/")
        #adding path params to the result
        self.query["endpoint"] = splitted[1]
        self.query["api_version"] = splitted[2] # assuming that our grammar is our api version
        self.query["entry"] = splitted[3]

        self.query['raw_query'] = "filter = %s" % query['filter'][0]
        # result.pop('filter',None)

        out = subprocess.Popen([converter_name, self.query['raw_query']],
                   stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT)
        stdout,stderr = out.communicate()

        # do i need to do try/except and throw custom error here?
        self.query['query'] = ast.literal_eval(stdout.decode("ascii"))

        return self.query
    def getDataFromCollection(self, query, mongoCollection):
        self.cursor = mongoCollection.find(query['query'], projection=query['response_fields'])\
                                .sort([query['sort']])\
                                .limit(query['response_limit'])
        return self.cursor
    def generateResponse(self,cursor):
        data = []
        data_returned_counter = 0
        for document in cursor:
            data.append(document)
            data_returned_counter += 1

        # generating other information needed in the response per specification
        data = Data(data)
        links = Links(None, None)
        meta = Meta(
                    query = {"representation":"/{}/?{}".format(self.query['entry'], self.query['raw_query'])},
                    api_version = self.query.get("api_version"),
                    time_stamp = datetime.datetime.utcnow().isoformat(),
                    data_returned = data_returned_counter,
                    more_data_available = True,
                    )
        #
        #
        links_schema = LinksSchema()
        meta_schema = MetaSchema()

        result = {
                "links":links_schema.dump(links).data['data']['attributes'],
                "data":data.data,
                "meta":meta_schema.dump(meta).data}

        # pprint(result)
        return result

    def getResponse(self):
        self.query = self.parseURL(self.url, self.alias, self.converter_name)
        self.cursor = self.getDataFromCollection(self.query, self.mongoCollection)
        self.result = self.generateResponse(self.cursor)
        return self.result
