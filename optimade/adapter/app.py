from flask import Flask, jsonify
from flask import request
import pymongo
from pymongo import MongoClient
from util import *
import os, subprocess
from models_class import *
from models_schema import *
import configparser

app = Flask(__name__)
app.config['TESTING'] = True

@app.route('/')
def index():
    return 'home'

@app.route('/optimade/0.9.6/structures/')
def find():
    # Test 1(full URL w/o pagination) --> http://127.0.0.1:5000/optimade/0.9.6/structures?filter=nelements%3C3&response_format=jsonapi&email_address=dwinston%40lbl.gov&response_limit=10&response_fields=id%2Cnelements%2Cmaterial_id%2Celements%2Cformula_prototype&sort=-nelements
    # Test 2(no projection/response_fields) --> http://127.0.0.1:5000/optimade/0.9.6/structures?filter=nelements%3C3&response_format=jsonapi&email_address=dwinston%40lbl.gov&response_limit=10&sort=-nelements
    # Test 3(no query) --> http://127.0.0.1:5000/optimade/0.9.6/structures?response_format=jsonapi&email_address=dwinston%40lbl.gov&response_limit=10&response_fields=id%2Cnelements%2Cmaterial_id%2Celements%2Cformula_prototype&sort=-nelements
    # Test 4(no sort) --> http://127.0.0.1:5000/optimade/0.9.6/structures?filter=nelements%3C3&response_format=jsonapi&email_address=dwinston%40lbl.gov&response_limit=10&response_fields=id%2Cnelements%2Cmaterial_id%2Celements%2Cformula_prototype
    # Test 5(no limit) --> http://127.0.0.1:5000/optimade/0.9.6/structures?filter=nelements%3C3&response_format=jsonapi&email_address=dwinston%40lbl.gov&response_fields=id%2Cnelements%2Cmaterial_id%2Celements%2Cformula_prototype&sort=-nelements
    # Test 6(pagination) -->http://127.0.0.1:5000/optimade/0.9.6/structures?filter=nelements%3C3&response_format=jsonapi&email_address=dwinston%40lbl.gov&response_limit=10&response_fields=id%2Cnelements%2Cmaterial_id%2Celements%2Cformula_prototype&sort=-nelements&page%5Bnumber%5D=1

    # current --> http://127.0.0.1:5000/optimade/0.9.6/structures?filter=nelements%3C3&response_format=jsonapi&email_address=dwinston%40lbl.gov&response_limit=10&response_fields=id%2Cnelements%2Cmaterial_id%2Celements%2Cformula_prototype&sort=-nelements&page=1
    # TODO: CONFIG PARSER
    # alias = {
    #     "chemical_formula":"formula_anonymous",
    #     "formula_prototype": "pretty_formula",
    # }

    # if the current workign directory contains config.ini
    alias_file_path = None
    for File in os.listdir("."):
        if File == "config.ini":
            alias_file_path = os.getcwd() + "/config.ini"
    

    #### START OF DATABASE CONNECTION  ####
    client = MongoClient()
    db=client.test_database
    test_collection = db.test_collection
    #### END OF DATABASE CONNECTION  ####
    result = getResponse(test_collection, request.url, alias_file_path)

    # return jsonify(result)
    return jsonify(response=result)


if __name__ == '__main__':
    app.run(debug=True)
