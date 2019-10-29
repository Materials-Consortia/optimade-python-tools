from lark import Transformer, v_args, Token


class NotImplementedRule(Exception):
    pass


class OperatorError(Exception):
    pass


class UnknownMongoDBQueryError(Exception):
    pass


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
    operator_map = {"<": "$lt", "<=": "$lte", ">": "$gt", ">=": "$gte", "!=": "$ne", "=": "$eq"}

    def __init__(self):
        super().__init__()

    def property(self, arg):
        # property: IDENTIFIER ( "." IDENTIFIER )*
        return '.'.join(arg)

    def number(self, arg):
        # number: SIGNED_INT | SIGNED_FLOAT
        token = arg[0]
        if token.type == 'SIGNED_INT':
            return int(token)
        elif token.type == 'SIGNED_FLOAT':
            return float(token)

    @v_args(inline=True)
    def string(self, string):
        # string: ESCAPED_STRING
        return string.strip('"')

    @v_args(inline=True)
    def value(self, value):
        # value: string | number | property
        # Note: Do nothing!
        return value

    @v_args(inline=True)
    def constant(self, value):
        # constant: string | number
        # Note: Do nothing!
        return value

    @v_args(inline=True)
    def operator(self, operator):
        # !operator: ("<" | "<=" | ">" | ">=" | "=" | "!=")
        return self.operator_map[operator]

    @v_args(inline=True)
    def value_op_rhs(self, operator, value):
        # value_op_rhs: operator value
        return {operator: value}

    def known_op_rhs(self, arg):
        # known_op_rhs: IS ( KNOWN | UNKNOWN )
        if arg[1] == 'KNOWN':
            return {'$exists': True}
        elif arg[1] == 'UNKNOWN':
            return {'$exists': False}

    def fuzzy_string_op_rhs(self, arg):
        # fuzzy_string_op_rhs: CONTAINS string | STARTS [ WITH ] string | ENDS [ WITH ] string

        # The WITH keyword may be omitted.
        if isinstance(arg[1], Token) and arg[1].type == "WITH":
            pattern = arg[2]
        else:
            pattern = arg[1]

        if arg[0] == 'CONTAINS':
            return {'$regex': f'{pattern}'}
        elif arg[0] == 'STARTS':
            return {'$regex': f'^{pattern}'}
        elif arg[0] == 'ENDS':
            return {'$regex': f'{pattern}$'}

    def set_op_rhs(self, arg):
        # set_op_rhs: HAS ( [ operator ] value | ALL value_list | ANY value_list | ONLY value_list )

        if len(arg) == 2:
            # only value without operator
            return {'$in': arg[1]}
        else:
            if arg[1] == 'ALL':
                raise NotImplementedRule
            elif arg[1] == 'ANY':
                raise NotImplementedRule
            elif arg[1] == 'ONLY':
                raise NotImplementedRule
            else:
                # value with operator
                raise NotImplementedRule

    def set_zip_op_rhs(self, arg):
        # set_zip_op_rhs: property_zip_addon HAS ( value_zip | ONLY value_zip_list | ALL value_zip_list |
        # ANY value_zip_list )
        raise NotImplementedRule

    def property_first_comparison(self, arg):
        # property_first_comparison: property ( value_op_rhs | known_op_rhs | fuzzy_string_op_rhs | set_op_rhs |
        # set_zip_op_rhs )
        return {arg[0]: arg[1]}

    def constant_first_comparison(self, arg):
        # constant_first_comparison: constant value_op_rhs
        return {prop: {oper: arg[0]} for oper, prop in arg[1].items()}

    def predicate_comparison(self, arg):
        # predicate_comparison: length_comparison
        raise NotImplementedRule

    @v_args(inline=True)
    def comparison(self, value):
        # comparison: constant_first_comparison | property_first_comparison
        # Note: Do nothing!
        return value

    def expression_phrase(self, arg):
        # expression_phrase: [ NOT ] ( comparison | predicate_comparison | "(" expression ")" )
        if len(arg) == 1:
            # without NOT
            return arg[0]
        else:
            # with NOT
            # TODO: This implementation probably fails in the case of `predicate_comparison` or `"(" expression ")"`
            return {prop: {'$not': expr} for prop, expr in arg[1].items()}

    def expression_clause(self, arg):
        # expression_clause: expression_phrase [ AND expression_clause ]
        if len(arg) == 1:
            # expression_phrase without 'AND'
            return arg[0]
        else:
            # combining multiple 'and's together
            if isinstance(arg[2], dict) and '$and' in arg[2]:
                # TODO: it has to be tested very carefully
                return {'$and': [arg[0], *arg[2]['$and']]}

            # expression_phrase with 'AND'
            return {'$and': [arg[0], arg[2]]}

    def expression(self, arg):
        # expression: expression_clause [ OR expression ]
        if len(arg) == 1:
            # expression_clause without 'OR'
            return arg[0]
        else:
            # combining multiple 'and's together
            if isinstance(arg[2], dict) and '$or' in arg[2]:
                # TODO: it has to be tested very carefully
                return {'$or': [arg[0], *arg[2]['$or']]}

            # expression_clause with 'OR'
            return {'$or': [arg[0], arg[2]]}

    def filter(self, arg):
        # filter: expression*
        if not arg:
            return None
        return arg[0]

    def __default__(self, data, children, meta):
        print(data, children, meta)
        return data


if __name__ == '__main__':
    from optimade.filterparser import LarkParser

    p = LarkParser(version=(0, 10, 0))
    t = NewMongoTransformer()

    f = 'a IS KNOWN AND a.a STARTS WITH "asdfsd" OR a < a AND NOT 8 >= b'

    print(f)
    print(p.parse(f))
    print(t.transform(p.parse(f)))
