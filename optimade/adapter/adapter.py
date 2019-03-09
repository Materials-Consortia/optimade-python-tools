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

### THIS IS NOT according to the new format ###
class Adapter():
    def __init__(self, URL,  mongoCollection, converter_name, alias = {}):
        self.url = URL
        self.mongoCollection = mongoCollection
        self.converter_name = converter_name
        self.alias = alias
