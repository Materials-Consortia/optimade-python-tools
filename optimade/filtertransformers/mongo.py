from lark import Transformer, v_args, Token


class MongoTransformer(Transformer):
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

    @v_args(inline=True)
    def non_string_value(self, value):
        """ non_string_value: number | property """
        # Note: Do nothing!
        return value

    @v_args(inline=True)
    def not_implemented_string(self, value):
        """ not_implemented_string: value

        Raise NotImplementedError.
        For further information, see Materials-Consortia/OPTIMADE issue 157:
        https://github.com/Materials-Consortia/OPTIMADE/issues/157
        """
        raise NotImplementedError("Comparing strings is not yet implemented.")

    def value_list(self, arg):
        # value_list: [ OPERATOR ] value ( "," [ OPERATOR ] value )*
        # NOTE: no support for optional OPERATOR, yet, so this takes the
        # parsed values and returns an error if that is being attempted
        for value in arg:
            if str(value) in self.operator_map.keys():
                raise NotImplementedError(
                    f"OPERATOR {value} inside value_list {arg} not implemented."
                )

        return arg

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
        return self._recursive_expression_phrase(arg)

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
        # constant_first_comparison: constant OPERATOR ( non_string_value | not_implemented_string )
        return {arg[2]: {self.reversed_operator_map[self.operator_map[arg[1]]]: arg[0]}}

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
            return {"$all": arg[2]}

        if arg[1] == "ANY":
            return {"$in": arg[2]}

        if arg[1] == "ONLY":
            return {"$all": arg[2], "$size": len(arg[2])}

        # value with OPERATOR
        raise NotImplementedError(
            f"set_op_rhs not implemented for use with OPERATOR. Given: {arg}"
        )

    def length_op_rhs(self, arg):
        # length_op_rhs: LENGTH [ OPERATOR ] value
        # TODO: https://stackoverflow.com/questions/7811163/query-for-documents-where-array-size-is-greater-than-1
        if len(arg) == 2 or (len(arg) == 3 and arg[1] == "="):
            return {"$size": arg[-1]}

        raise NotImplementedError(
            f"Operator {arg[1]} not implemented for LENGTH filter."
        )

    def set_zip_op_rhs(self, arg):
        # set_zip_op_rhs: property_zip_addon HAS ( value_zip | ONLY value_zip_list | ALL value_zip_list |
        # ANY value_zip_list )
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

    @v_args(inline=True)
    def signed_int(self, number):
        # signed_int : SIGNED_INT
        return int(number)

    @v_args(inline=True)
    def number(self, number):
        # number: SIGNED_INT | SIGNED_FLOAT
        if number.type == "SIGNED_INT":
            type_ = int
        elif number.type == "SIGNED_FLOAT":
            type_ = float
        return type_(number)

    def __default__(self, data, children, meta):
        raise NotImplementedError(
            f"Calling __default__, i.e., unknown grammar concept. data: {data}, children: {children}, meta: {meta}"
        )

    def _recursive_expression_phrase(self, arg):
        """ Helper function for parsing `expression_phrase`. Recursively sorts out
        the correct precedence for $and, $or and $nor.

        """
        if len(arg) == 1:
            # without NOT
            return arg[0]

        # handle the case of {"$not": {"$or": [expr1, expr2]}} using {"$nor": [expr1, expr2]}.
        if "$or" in arg[1]:
            return {"$nor": self._recursive_expression_phrase([arg[1]["$or"]])}

        # handle the case of {"$not": {"$and": [expr1, expr2]}} using per-expression negation,
        # e.g. {"$and": [{prop1: {"$not": expr1}}, {prop2: {"$not": ~expr2}}]}.
        # Note that this is not the same as NOT (expr1 AND expr2)!
        if "$and" in arg[1]:
            return {
                "$and": [
                    self._recursive_expression_phrase(["NOT", subdict])
                    for subdict in arg[1]["$and"]
                ]
            }

        # simple case of negating one expression, from NOT (expr) to ~expr.
        return {prop: {"$not": expr} for prop, expr in arg[1].items()}
