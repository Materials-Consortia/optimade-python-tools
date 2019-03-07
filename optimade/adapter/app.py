from flask import Flask
from flask import request
import pymongo
from pymongo import MongoClient
from util import *
import os, subprocess
from models_class import *
from models_schema import *

app = Flask(__name__)
app.config['TESTING'] = True

@app.route('/')
def index():
    return 'home'

@app.route('/optimade/0.9.6/structures/')
def find():
    client = MongoClient()
    db=client.test_database
    test_collection = db.test_collection
    query = dict(request.args)
    result = getData(test_collection, \
                        "http://127.0.0.1:5000/optimade/0.9.6/structures",\
                        query)
    pprint(result)

    return str(result)
    # return parseArgs(args)


if __name__ == '__main__':
    app.run(debug=True)
