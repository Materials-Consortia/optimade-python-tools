import pql
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from optimade.filter import Parser
from lark import Transformer
import re

# data for pql to mongodb symbol
optiMadeToPQLOperatorSwitch = {
    "=":"==",
    "<=":"<=",
    ">=":">=",
    "!=": "!=",
    "<":"<",
    ">":">",
}

class OperatorError(Exception):
    pass

def OptiMadeToPQLOperatorValidator(x):
    """
    convert pql to mongodb symbol
    """
    item = optiMadeToPQLOperatorSwitch.get(x)
    if(type(item) != None):
        return item
    else:
        raise OperatorError("<{}> is not a valid operator".format(x))


def combineMultiple(PQL, index):
    """
     @param string -- input raw optimade input
     @param index -- index in which "," was found
     Procedure:
         1. find the first and last quote centering from the index of the ","
         2. get everything between first and last quote
         3. split the string into individual elements
         4. put them into Python Query Language format
    """
    for i in reversed(range(index)):
        if(PQL[i] == "'" or PQL[i] == '"'):
            firstIndex = i
            break
    for i in range(index, len(PQL)):
        if(PQL[i] == "'" or PQL[i]== '"'):
            lastIndex = i
            break
    insertion = PQL[firstIndex + 1 : lastIndex] # since the first index is inclusive, need to exclude the quote
    insertion = insertion.split(",")
    # remove the preceding 0 for all individual entries, insert those as array format into the original PQL query
    result = PQL[:firstIndex] + "all({})".format([item.lstrip() for item in insertion])
    # update pointer to after the combined sequence
    result_index = len(result)
    result = result +  PQL[lastIndex + 1:]
    return result, result_index

def cleanPQL(PQL):
    """
     @param PQL: raw PQL
     Procedure:
         1. go through PQL, find "," to find where i need to combine multiple elements
         2. combine multiple
         3. return the cleaned PQL
    """
    length = len(PQL)
    i = 0
    while(i < length):
        if(PQL[i] == ","):
            PQL, newIndex = combineMultiple(PQL, i)
            i = newIndex
        i = i + 1
    return PQL

class UnknownMongoDBQueryError(Exception):
    pass

def cleanMongo(rawMongoDbQuery):
    """
    @param rawMongoDbQuery -- input that needs to be cleaned
    Procedure:
        recursively go through the rawMongoDbQuery, turn string into float if possible in the value field
    """
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
            raise UnknownMongoDBQueryError("Unrecognized MongoDB Query \n {}".format(rawMongoDbQuery))


class OptimadeToPQLTransformer(Transformer):
    """
     class for transforming Lark tree into PQL format
    """
    def comparison(self, args):
        A = str(args[0])
        B = args[2]
#        B = ""
#        for b in args[2:]:
#            if B == "":
#                B = b
#            else:
#                B = B + ", " + b
        operator = OptiMadeToPQLOperatorValidator(args[1])
        return A + operator + '"' + B + '"'
    def atom(self, args):
        return ' '.join(args) if len(args) == 2 else args[0]
    def term(self, args):
        result = ""
        for arg in args:
            if arg.lower() == "and" or arg.lower() == "or":
                arg = arg.lower()
            result = result + " " + arg
        return "(" + result.lstrip() + ")"
    def expression(self, args):
        result = ""
        for arg in args:
            result = result + " " + arg
        return result.lstrip()
    def start(self, args):
        return args[1]
    def combined(self, args):
        return args[0]


op_expr = {
    "<": "$lt",
    "<=": "$lte",
    ">": "$gt",
    ">=": "$gte",
    "!=": "$ne",
    "=": "$eq",
}


class MongoTransformer(Transformer):
    """
     class for transforming Lark tree into MongoDB format
    """
    def start(self, args):
        return args[0]

    def expression(self, args):
        if len(args) == 1:
            return args[0]

        # Conjunct expressions together from left to right,
        # finally conjuncting to terminal term.
        #
        # Example scenarios:
        #
        # expression CONJUNCTION term
        # ...(nothing)
        # expression CONJUNCTION expression CONJUNCTION term
        # ...CONJUNCTION term
        # expression CONJUNCTION expression CONJUNCTION expression CONJUNCTION term
        # ...CONJUNCTION expression CONJUNCTION term
        # ...CONJUNCTION term

        args_to_process = args.copy()
        while len(args_to_process) >= 2:
            looper = 1
            cont = args_to_process[0] if looper == 1 else output
            conj = f'${args_to_process[1].value.lower()}'
            output = {conj: [cont, args_to_process[2]]}
            args_to_process = args_to_process[3:]
            looper += 1

        return output

    def term(self, args):
        if args[0] == "(":
            raise NotImplementedError("openparen")
        if len(args) == 1:
            return args[0]
        args_to_process = args.copy()
        output = self.expression(args)
        return output

        # TODO refactor args>=3 case of self.expression to call fn that this
        # method can also call in that case.
        # raise NotImplementedError("recursion")

    def atom(self, args):
        """Optionally negate a comparison."""
        # Two cases:
        # 1. args is parsed comparison, or
        # 2. args is NOT token and parsed comparison
        #     - [ Token(NOT, 'not'), {field: {op: val}} ]
        #        -> {field: {$not: {op: val}}}
        if len(args) == 2:
            field, predicate = next(((k, v) for k, v in args[1].items()))
            return {field: {"$not": predicate}}
        else:
            return args[0]

    def comparison(self, args):
        # TODO account for parens and `combined` subexpression.
        if args[-1] == ")":
            raise NotImplementedError("end paren")
        if args[-1] == "'":
            raise NotImplementedError("combined")

        field = args[0].value
        op = op_expr[args[1].value]
        val_tok = args[2]
        if val_tok.isnumeric():
            val = float(val_tok.value)
        else:
            val = val_tok.value
        return {field: {op: val}}

    def combined(self, args):
        pass


def parseAlias(query, aliases):
    """
    @param optimadeQuery -- the query to be parsed
    @param aliases -- dictionary with structure {"OPTIMADE_STRUCTURE_NAME": "YOUR_DB_STRUCTURE_NAME"}
    Procedure:
        1. loop through all aliases
        2. replace all occurences of OPTIMADE_STRUCTURE_NAME with YOUR_DB_STRUCTURE_NAME
        3. return the resultant optimadeQuery
    """
    if(aliases != None):
        for alias in aliases:
            query = re.sub(r"\b%s\b"%alias, aliases[alias], query)
    return query
def optimadeToMongoDBConverter(optimadeQuery, version=None, aliases=None):
    """
    main function for converting optimade query to mongoDB query
    Procedure:
     1. converting optimadeQuery into Lark tree
     2. converting tree into raw PQL
     3. parsing the rawPQL into cleaned PQL (putting combined item in place)
     4. parse cleaned PQL into raw MongoDB query
     5. parse raw MongoDB Query into cleaned MongoDb Query (turn values in string into float if possible)
    """

    p = Parser(version=version)
    optimadeQuery = parseAlias(optimadeQuery, aliases)
    try:
        tree = p.parse(optimadeQuery)
        rawPQL = OptimadeToPQLTransformer().transform(tree)
        cleanedPQL = cleanPQL(rawPQL)
        mongoDbQuery = pql.find(cleanedPQL)
    except Exception as e:
        return e

    cleanMongo(mongoDbQuery)
    return mongoDbQuery
