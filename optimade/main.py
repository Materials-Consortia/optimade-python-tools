from optimade.converter.mongo import optimadeToMongoDBConverter
import argparse
from ast import literal_eval
import re

ap = argparse.ArgumentParser()
ap.add_argument("Query", help="Query with quotation mark around it. ex: 'filter= a < 0'")
ap.add_argument("-v", "--Version", required=False, help="The version of the Lark grammer desired, surrounded by quotation mark. ex: {}".format(' "(1,2,3)" '))
ap.add_argument("-a", "--Alias", required=False, help='Aliases with quotation mark around it. ex: "{}"'.format("{'a':'b'}"))
args=ap.parse_args()


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
    if(v == None):
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
        return literal_eval(a)


print(optimadeToMongoDBConverter(args.Query, prepVersion(args.Version), prepAlias(args.Alias)))
