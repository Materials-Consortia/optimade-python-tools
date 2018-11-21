import sys, os
import configparser
# below is a hack, not too sure why without this line the program would crash at from mongo...
sys.path.append(os.path.dirname(__file__))
from mongo import optimadeToMongoDBConverter
import json
import argparse
import ast
import re

def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]


    ap = argparse.ArgumentParser()
    ap.add_argument("Query", help="Query with quotation mark around it. ex: 'filter= a < 0'")
    ap.add_argument("-v", "--Version", required=False, help="The version of the Lark grammer desired, surrounded by quotation mark. ex: {}".format(' "(1,2,3)" '))
    ap.add_argument("-a", "--Alias", required=False, help='Aliases with quotation mark around it. ex: "{}"'.format("{'a':'b'}"))
    
    args=ap.parse_args()


    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

    def prepVersion(v):
        """
        @param v: user input Version
        Procedure:
            1. if v is None, then return None
            2. otherwise, split v into array
            3. remove all other characters such as "()" from each index
            4. And change string to int
            5. turn the resulting list into a tuple
        """
        if(v == None or v == ""):
            return None
        else:
            array = v.split(",")
            r = range(len(array))
            result = list(r)
            for i in r:
                result[i] = int(re.sub("\D", "", array[i]))
            return tuple(result)

    def prepAlias(a):
        """
        @param a: user input Aliases
        Procedure:
            1. if Alias is None, return None
            2. otherwise, literal_eval a to get a dictionary, return the resultant
        """
        if(a == None):
            return None
        else:
            return ast.literal_eval(a)

    alias = dict()
    if(config['aliases']!=None):
        d = dict(config.items('aliases'))
        for key in d:
            alias[key] = config['aliases'][key]
    if(args.Alias != None):
        alias = prepAlias(args.Alias)

    v = None
    if(config['version'] != None):
        a = config['version']['major']
        b = config['version']['minor']
        c = config['version']['patch']
        v = (int(a), int(b) , int(c))
    if(args.Version != None):
        v = prepVersion(args.Version)

    result = optimadeToMongoDBConverter(args.Query, v, alias)
    return result



if __name__ == "__main__":
    main()
