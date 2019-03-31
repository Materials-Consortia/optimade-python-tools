import datetime
from marshmallow import pprint
from urlGenerator import generateFromString, generateFromDict
from urllib.parse import urlparse,quote_plus,parse_qs
import pymongo
from GlobalVar import PAGE_LIMIT
class Meta():
    def __init__(self, collection, parsed_args,data, cursor):
        self.collection = collection
        self.parsed_args = parsed_args
        self.data = data
        self.cursor = cursor
        self.constructMetaData()
    def __repr__(self):
        return str(getMetaData(self))
    def constructMetaData(self):
        total_entries = self.cursor.count()
        self.query = {'representation': self.parsed_args.get('representation')}
        self.api_version = self.parsed_args.get('api_version')
        self.data_returned = len(self.data.get('data'))
        self.parsed_args['data_returned'] = self.data_returned
        self.data_available = self.cursor.count()
        self.more_data_available = True if self.data_returned < self.data_available else False
        data = self.data.get('data')
        self.last_id = data[len(data)-1].get("attributes").get("material_id")
        self.time_stamp = datetime.datetime.utcnow().isoformat()
    def getMetaData(self):
        return {"meta": {
                    "query":self.query,
                    "api_version":self.api_version,
                    "data_returned":self.data_returned,
                    "data_available":self.data_available,
                    "more_data_available":self.more_data_available,
                    "last_id":self.last_id,
                    "time_stamp":self.time_stamp
                    }
                }

class Links():
    def __init__(self, collection, parsed_args, cursor):
        self.collection = collection
        self.parsed_args = parsed_args
        self.cursor = cursor
        self.constructLinkData()
    def __repr__(self):
        return str(getLinkData(self))
    def constructLinkData(self):
        self.base_url = {
            "href":self.parsed_args.get('base_url'),
                "meta":{
                    "version":self.parsed_args.get('api_version') #???
                }
            }
        query = self.parsed_args.get("representation")
        filterString = query[query.find("?")+1:]
        entry_point = query[:query.find("?")-1]
        url = generateFromString(self.parsed_args.get('base_url'),entry_point, filterString)
        parsed = urlparse(url)
        args = parse_qs(parsed.query)
        # finding current page
        currentPage = 1
        if(args.get('page') != None):
            currentPage = int(args.get('page')[0])
        # finding max page
        maxPage = self.cursor.count() // int(self.parsed_args.get("response_limit")) + 1

        print("maxPage=", maxPage)

        ## settomg next page
        if currentPage + 1 > maxPage:
            self.next = None
        else:
            args['page'] = currentPage + 1
            self.next = generateFromDict(self.parsed_args.get('base_url'), entry_point, args)
        # setting prev page
        if currentPage - 1 <= 0:
            self.prev = None
        else:
            args['page'] = currentPage - 1  #calculate prev page index
            self.prev = generateFromDict(self.parsed_args.get('base_url'),entry_point, args)

        # setting first page
        args['page'] = 1
        self.first = generateFromDict(self.parsed_args.get('base_url'),entry_point, args)
        # setting last page
        args['page'] = maxPage
        self.last = generateFromDict(self.parsed_args.get('base_url'),entry_point, args)
    def getLinkData(self):
        return {"links": {
                        "next":self.next,
                        "prev":self.prev,
                        "first":self.first,
                        "last":self.last,
                        "base_url":self.base_url,
                    }
                  }
