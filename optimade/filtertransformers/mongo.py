from lark import Transformer, v_args, Token


op_expr = {"<": "$lt", "<=": "$lte", ">": "$gt", ">=": "$gte", "!=": "$ne", "=": "$eq"}


def conjoin_args(args):
    """ Conjoin from left to right.

    Args:
        args (list): [<something> CONJUNCTION] <something>

    Returns:
        dict: MongoDB filter
    """
    if len(args) == 1:
        return args[0]
    conj = f"${args[1].value.lower()}"
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
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
        return {field: {op: val}}

    def combined(self, args):
        elements = []
        for val_tok in args:
            try:
                val = float(val_tok.value)
            except ValueError:
                val = val_tok.value
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
            elements.append(val)
        return elements


class NewMongoTransformer(Transformer):
    """Support for grammar v0.10.1"""

    operator_map = {
        "<": "$lt",
        "<=": "$lte",
        ">": "$gt",
        ">=": "$gte",
        "!=": "$ne",
        "=": "$eq",
    }
    reversed_operator_map = {
        "$lt": "$gt",
        "$lte": "$gte",
        "$gt": "$lt",
        "$gte": "$lte",
        "$ne": "$ne",
        "$eq": "$eq",
    }

    def __init__(self):
        super().__init__()

    def filter(self, arg):
        # filter: expression*
        return arg[0] if arg else None

    @v_args(inline=True)
    def constant(self, value):
        # constant: string | number
        # Note: Do nothing!
        return value

    @v_args(inline=True)
    def value(self, value):
        # value: string | number | property
        # Note: Do nothing!
        return value

    def value_list(self, arg):
        # value_list: [ OPERATOR ] value ( "," [ OPERATOR ] value )*
        raise NotImplementedError

    def value_zip(self, arg):
        # value_zip: [ OPERATOR ] value ":" [ OPERATOR ] value (":" [ OPERATOR ] value)*
        raise NotImplementedError

    def value_zip_list(self, arg):
        # value_zip_list: value_zip ( "," value_zip )*
        raise NotImplementedError

    def expression(self, arg):
        # expression: expression_clause ( OR expression_clause )
        # expression with and without 'OR'
        return {"$or": arg} if len(arg) > 1 else arg[0]

    def expression_clause(self, arg):
        # expression_clause: expression_phrase ( AND expression_phrase )*
        # expression_clause with and without 'AND'
        return {"$and": arg} if len(arg) > 1 else arg[0]

    def expression_phrase(self, arg):
        # expression_phrase: [ NOT ] ( comparison | "(" expression ")" )
        if len(arg) == 1:
            # without NOT
            return arg[0]

        # with NOT
        # TODO: This implementation probably fails in the case of `"(" expression ")"`
        return {prop: {"$not": expr} for prop, expr in arg[1].items()}

    @v_args(inline=True)
    def comparison(self, value):
        # comparison: constant_first_comparison | property_first_comparison
        # Note: Do nothing!
        return value

    def property_first_comparison(self, arg):
        # property_first_comparison: property ( value_op_rhs | known_op_rhs | fuzzy_string_op_rhs | set_op_rhs |
        # set_zip_op_rhs | length_op_rhs )
        return {arg[0]: arg[1]}

    def constant_first_comparison(self, arg):
        # constant_first_comparison: constant value_op_rhs
        # TODO: Probably the value_op_rhs rule is not the best for implementing this.
        return {
            prop: {self.reversed_operator_map[oper]: arg[0]}
            for oper, prop in arg[1].items()
        }

    @v_args(inline=True)
    def value_op_rhs(self, operator, value):
        # value_op_rhs: OPERATOR value
        return {self.operator_map[operator]: value}

    def known_op_rhs(self, arg):
        # known_op_rhs: IS ( KNOWN | UNKNOWN )
        return {"$exists": arg[1] == "KNOWN"}

    def fuzzy_string_op_rhs(self, arg):
        # fuzzy_string_op_rhs: CONTAINS value | STARTS [ WITH ] value | ENDS [ WITH ] value

        # The WITH keyword may be omitted.
        if isinstance(arg[1], Token) and arg[1].type == "WITH":
            pattern = arg[2]
        else:
            pattern = arg[1]

        # CONTAINS
        if arg[0] == "CONTAINS":
            regex = f"{pattern}"
        elif arg[0] == "STARTS":
            regex = f"^{pattern}"
        elif arg[0] == "ENDS":
            regex = f"{pattern}$"
        return {"$regex": regex}

    def set_op_rhs(self, arg):
        # set_op_rhs: HAS ( [ OPERATOR ] value | ALL value_list | ANY value_list | ONLY value_list )

        if len(arg) == 2:
            # only value without OPERATOR
            return {"$in": arg[1:]}

        if arg[1] == "ALL":
            raise NotImplementedError
        if arg[1] == "ANY":
            raise NotImplementedError
        if arg[1] == "ONLY":
            raise NotImplementedError

        # value with OPERATOR
        raise NotImplementedError

    def set_zip_op_rhs(self, arg):
        # set_zip_op_rhs: property_zip_addon HAS ( value_zip | ONLY value_zip_list | ALL value_zip_list |
        # ANY value_zip_list )
        raise NotImplementedError

    def length_op_rhs(self, arg):
        # length_op_rhs: LENGTH [ OPERATOR ] value
        # TODO: https://stackoverflow.com/questions/7811163/query-for-documents-where-array-size-is-greater-than-1
        if len(arg) == 2 or (len(arg) == 3 and arg[1] == "="):
            return {"$size": arg[-1]}

        raise NotImplementedError

    def property_zip_addon(self, arg):
        # property_zip_addon: ":" property (":" property)*
        raise NotImplementedError

    def property(self, arg):
        # property: IDENTIFIER ( "." IDENTIFIER )*
        return ".".join(arg)

    @v_args(inline=True)
    def string(self, string):
        # string: ESCAPED_STRING
        return string.strip('"')

    def number(self, arg):
        # number: SIGNED_INT | SIGNED_FLOAT
        token = arg[0]
        if token.type == "SIGNED_INT":
            type_ = int
        elif token.type == "SIGNED_FLOAT":
            type_ = float
        return type_(token)

    def __default__(self, data, children, meta):
        raise NotImplementedError(
            f"Calling __default__, i.e., unknown grammar concept. data: {data}, children: {children}, meta: {meta}"
        )
