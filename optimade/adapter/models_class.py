import datetime
from marshmallow import pprint
class Meta():
    def __init__(self, collection, cursor, parsed_args,data):
        self.collection = collection
        self.parsed_args = parsed_args
        self.cursor = cursor
        self.data = data
        print("data = ")
        pprint(data)
        self.constructMetaData()
    def __repr__(self):
        return str({"meta": {
                    "query":self.query,
                    "api_version":self.api_version,
                    "data_returned":self.data_returned,
                    "data_available":self.data_available,
                    "more_data_available":self.more_data_available,
                    "last_id":self.last_id,
                    "response_message":self.response_message,
                    "time_stamp":self.time_stamp
                    }
                })
    def constructMetaData(self):
        total_entries = self.collection.count()
        self.query = {'representation': self.parsed_args.get('representation')}
        self.more_data_available = True if self.collection.count() > self.cursor.count() else False
        self.api_version = self.parsed_args.get('api_version')
        self.data_returned = len(self.data.get('data'))
        self.parsed_args['data_returned'] = self.data_returned
        self.data_available = self.collection.count()
        self.more_data_available = True if  self.data_available > self.data_returned else False
        self.last_id = "NOT IMPLEMENTED YET"
        self.response_message = "NOT IMPLEMENTED YET"
        self.time_stamp = datetime.datetime.utcnow().isoformat()
    def getMetaData(self):
        return {"meta": {
                    "query":self.query,
                    "api_version":self.api_version,
                    "data_returned":self.data_returned,
                    "data_available":self.data_available,
                    "more_data_available":self.more_data_available,
                    "last_id":self.last_id,
                    "response_message":self.response_message,
                    "time_stamp":self.time_stamp
                    }
                }

class Link():
    def __init__(self, collection, cursor, parsed_args):
        self.collection = collection
        self.cursor = cursor
        self.parsed_args = parsed_args
        self.constructLinkData()
    def __repr__(self):
        return str({"link": {
                        "next":self.next,
                        "base_url":self.base_url
                    }
                  })
    def constructLinkData(self):
        self.next = None #HOW TO DO THIS???
        self.base_url = {
            "href":self.parsed_args.get('base_url'),
                "meta":{
                    "version":self.parsed_args.get('api_version') #???
                }
            }
    def getLinkData(self):
        return {"link": {
                        "next":self.next,
                        "base_url":self.base_url
                    }
                  }
