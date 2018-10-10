import pql
from optimade.filter import Parser
from lark import Transformer

# data for pql to mongodb symbol
optiMadeToPQLOperatorSwitch = {
    "=":"==",
    "<=":"<=",
    ">=":">=",
    "=>":">=",
    "!=": "!=",
    "<":"<",
    ">":">",
}

# convert pql to mongodb symbol
def OptiMadeToPQLOperatorValidator(x):
    return optiMadeToPQLOperatorSwitch[x]

# @param string -- input raw optimade input
# @param index -- index in which "," was found
# Procedure:
# 1. find the first and last quote centering from the index of the ","
# 2. get everything between first and last quote
# 3. split the string into individual elements
# 4. put them into Python Query Language format
def combineMultiple(string, index):
    firstQuoteIndex = 0
    for firstQuoteIndex in reversed(range(0, index)):
        if(ord(string[firstQuoteIndex]) == 34):
            firstQuoteIndex = firstQuoteIndex + 1
            break
    lastQuoteIndex = index
    for lastQuoteIndex in range(index, len(string)):
        if(ord(string[lastQuoteIndex])== 34):
            break
    insertion = string[firstQuoteIndex:lastQuoteIndex]
    insertion = insertion.split(",")
    return string[:firstQuoteIndex - 1] + 'all({})'.format(insertion) + string[lastQuoteIndex + 1:], lastQuoteIndex + 1

# @param PQL: raw PQL
# Procedure:
# 1. go through PQL, find "," to find where i need to combine multiple elements
# 2. combine multiple
# 3. return the cleaned PQL
def parseInput(PQL):
    length = len(PQL)
    i = 0
    while(i < length):
        if(PQL[i] == ","):
            PQL, newIndex = combineMultiple(PQL, i)
            i = newIndex
        i = i + 1
    return PQL

# @param rawMongoDbQuery -- input that needs to be cleaned
# Procedure:
# recursively go through the rawMongoDbQuery, turn string into float if possible in the value field
def cleanMongo(rawMongoDbQuery):
    if(type(rawMongoDbQuery) != dict):
        return
    for k in rawMongoDbQuery:
        value = rawMongoDbQuery[k]
        if(type(value) == list):
            for v in value:
                cleanMongo(v)
        elif(type(value) == dict):
            cleanMongo(value)
        elif(type(value) == str):
            try:
                value = float(value)
                rawMongoDbQuery[k] = float(value)
            except:
                f = value
        else:
            raise Exception('Unable to parse through rawMongoDbQuery')

# class for transforming Lark tree into PQL format
class OptimadeToPQLTransformer(Transformer):
    def comparison(self, args):
        A = str(args[0])
        B = ""
        for b in args[2:]:
            if B == "":
                B = b
            else:
                B = B + ", " + b
        operator = OptiMadeToPQLOperatorValidator(args[1])
        return A + operator + '"' + B + '"'
    def atom(self, args):
        return args[0]
    def term(self, args):
        result = ""
        for arg in args:
            if arg.lower() == "and" or arg.lower() == "or":
                arg = arg.lower()
            result = result + " " + arg.lower()
        return "(" + result.lstrip() + ")"

    def expression(self, args):
        result = ""
        for arg in args:
            lower = arg.lower()
            if(lower == "and" or lower == "or"):
                arg = lower
            result = result + " " + arg
        return result.lstrip()
    def start(self, args):
        return args[1]
    def combined(self, args):
        return args[0]


# main function for converting optimade query to mongoDB query
# Procedure:
# 1. converting optimadeQuery into Lark tree
# 2. converting tree into raw PQL
# 3. parsing the rawPQL into cleaned PQL (putting combined item in place)
# 4. parse cleaned PQL into raw MongoDB query
# 5. parse raw MongoDB Query into cleaned MongoDb Query (turn values in string into float if possible)
def optimadeToMongoDBConverter(optimadeQuery):
    p = Parser(version=(0, 9, 6))

    tree=""
    try:
        tree = p.parse(optimadeQuery)
    except:
        return "ERROR: Unable to parse {} into rawPQL".format(optimadeQuery)

    cleanedPQL = ""
    try:
        rawPQL = OptimadeToPQLTransformer().transform(tree)
        cleanedPQL = parseInput(rawPQL)
    except:
        return "ERROR: Unable to transform tree to PQL {}".format(tree)

    mongoDbQuery = {}
    try:
        mongoDbQuery = pql.find(cleanedPQL)
    except:
        return "ERROR: Unable parse PQL to MongoDB execute conversion"

    cleanMongo(mongoDbQuery)
    return mongoDbQuery
