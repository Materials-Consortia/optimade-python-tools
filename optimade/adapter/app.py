from flask import Flask
from flask import request
import pymongo
from pymongo import MongoClient
from util import *
import os, subprocess

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
    args = dict(request.args)
    return str(parseArgs('/optimade/0.9.6/structures/', args))
    # return parseArgs(args)


if __name__ == '__main__':
    app.run(debug=True)
