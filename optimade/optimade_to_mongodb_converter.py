import pql
from optimade.filter import Parser
from lark import Transformer


optiMadeToPQLOperatorSwitch = {
    "=":"==",
    "<=":"<=",
    ">=":">=",
    "=>":">=",
    "!=": "!=",
    "<":"<",
    ">":">",
}

def OptiMadeToPQLOperatorValidator(x):
    return optiMadeToPQLOperatorSwitch[x]

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

def parseInput(PQL):
    length = len(PQL)
    i = 0
    while(i < length):
        if(PQL[i] == ","):
            PQL, newIndex = combineMultiple(PQL, i)
            i = newIndex
        i = i + 1
    return PQL

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
            print("value", value)


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



def optimadeToMongoDBConverter(optimadeQuery):
    p = Parser(version=(0, 9, 6))

    tree = p.parse(optimadeQuery)

    rawPQL = OptimadeToPQLTransformer().transform(tree)
    cleanedPQL = parseInput(rawPQL)

    mongoDbQuery = {}
    try:
        mongoDbQuery = pql.find(cleanedPQL)
    except:
        return "ERROR: Unable to PQL to MongoDB execute conversion"

    cleanMongo(mongoDbQuery)
    return mongoDbQuery
