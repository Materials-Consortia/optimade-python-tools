from lark import Transformer


class OperatorError(Exception):
    pass


class UnknownMongoDBQueryError(Exception):
    pass


op_expr = {
    "<": "$lt",
    "<=": "$lte",
    ">": "$gt",
    ">=": "$gte",
    "!=": "$ne",
    "=": "$eq",
}


def conjoin_args(args):
    """ Conjoin from left to right.

    Args:
        args (list): [<something> CONJUNCTION] <something>

    Returns:
        dict: MongoDB filter
    """
    if len(args) == 1:
        return args[0]
    conj = f'${args[1].value.lower()}'
    return {conj: [args[0], args[2]]}


class MongoTransformer(Transformer):
    """
     class for transforming Lark tree into MongoDB format
    """
    def start(self, args):
        return args[0]

    def expression(self, args):
        return conjoin_args(args)

    def term(self, args):
        if args[0] == "(":
            return conjoin_args(args[1:-1])
        return conjoin_args(args)

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
        field = args[0].value
        if isinstance(args[2], list):
            if args[1].value != "=":
                raise NotImplementedError(
                    "x,y,z values only supported for '=' operator"
                )
            return {field: {"$all": args[2]}}

        op = op_expr[args[1].value]
        val_tok = args[2]
        try:
            val = float(val_tok.value)
        except ValueError:
            val = val_tok.value
            if val.startswith("\"") and val.endswith("\""):
                val = val[1:-1]
        return {field: {op: val}}

    def combined(self, args):
        elements = []
        for val_tok in args:
            try:
                val = float(val_tok.value)
            except ValueError:
                val = val_tok.value
                if val.startswith("\"") and val.endswith("\""):
                    val = val[1:-1]
            elements.append(val)
        return elements
