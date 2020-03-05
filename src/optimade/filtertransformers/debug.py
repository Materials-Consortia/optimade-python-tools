from lark import Transformer


class DebugTransformer(Transformer):  # pragma: no cover
    def __init__(self):
        super().__init__()

    def __default__(self, data, children, meta):
        print("Node: ", data, children)
        return data


class TransformerSkeleton(Transformer):  # pragma: no cover
    """Prints out all the nodes and its arguments during the walk-through of the tree."""

    def __init__(self):
        super().__init__()

    def filter(self, arg):
        # filter: expression*
        print("Node: ", "filter", arg)
        return "filter"

    def constant(self, arg):
        # constant: string | number
        print("Node: ", "constant", arg)
        return "constant"

    def value(self, arg):
        # value: string | number | property
        print("Node: ", "value", arg)
        return "value"

    def value_list(self, arg):
        # value_list: [ OPERATOR ] value ( "," [ OPERATOR ] value )*
        print("Node: ", "value_list", arg)
        return "value_list"

    def value_zip(self, arg):
        # value_zip: [ OPERATOR ] value ":" [ OPERATOR ] value (":" [ OPERATOR ] value)*
        print("Node: ", "value_zip", arg)
        return "value_zip"

    def value_zip_list(self, arg):
        # value_zip_list: value_zip ( "," value_zip )*
        print("Node: ", "value_zip_list", arg)
        return "value_zip_list"

    def expression(self, arg):
        # expression: expression_clause [ OR expression ]
        print("Node: ", "expression", arg)
        return "expression"

    def expression_clause(self, arg):
        # expression_clause: expression_phrase [ AND expression_clause ]
        print("Node: ", "expression_clause", arg)
        return "expression_clause"

    def expression_phrase(self, arg):
        # expression_phrase: [ NOT ] ( comparison | predicate_comparison | "(" expression ")" )
        print("Node: ", "expression_phrase", arg)
        return "expression_phrase"

    def comparison(self, arg):
        # comparison: constant_first_comparison | property_first_comparison
        # Note: Do nothing!
        print("Node: ", "comparison", arg)
        return "comparison"

    def property_first_comparison(self, arg):
        # property_first_comparison: property ( value_op_rhs | known_op_rhs | fuzzy_string_op_rhs | set_op_rhs |
        # set_zip_op_rhs )
        print("Node: ", "property_first_comparison", arg)
        return "property_first_comparison"

    def constant_first_comparison(self, arg):
        # constant_first_comparison: constant value_op_rhs
        print("Node: ", "constant_first_comparison", arg)
        return "constant_first_comparison"

    def predicate_comparison(self, arg):
        # predicate_comparison: length_comparison
        print("Node: ", "predicate_comparison", arg)
        return "predicate_comparison"

    def value_op_rhs(self, arg):
        # value_op_rhs: OPERATOR value
        print("Node: ", "value_op_rhs", arg)
        return "value_op_rhs"

    def known_op_rhs(self, arg):
        # known_op_rhs: IS ( KNOWN | UNKNOWN )
        print("Node: ", "known_op_rhs", arg)
        return "known_op_rhs"

    def fuzzy_string_op_rhs(self, arg):
        # fuzzy_string_op_rhs: CONTAINS string | STARTS [ WITH ] string | ENDS [ WITH ] string
        print("Node: ", "fuzzy_string_op_rhs", arg)
        return "fuzzy_string_op_rhs"

    def set_op_rhs(self, arg):
        # set_op_rhs: HAS ( [ OPERATOR ] value | ALL value_list | ANY value_list | ONLY value_list )
        print("Node: ", "set_op_rhs", arg)
        return "set_op_rhs"

    def set_zip_op_rhs(self, arg):
        # set_zip_op_rhs: property_zip_addon HAS ( value_zip | ONLY value_zip_list | ALL value_zip_list |
        # ANY value_zip_list )
        print("Node: ", "set_zip_op_rhs", arg)
        return "set_zip_op_rhs"

    def length_comparison(self, arg):
        # length_comparison: LENGTH property OPERATOR value
        print("Node: ", "length_comparison", arg)
        return "length_comparison"

    def property_zip_addon(self, arg):
        # property_zip_addon: ":" property (":" property)*
        print("Node: ", "property_zip_addon", arg)
        return "property_zip_addon"

    def property(self, arg):
        # property: IDENTIFIER ( "." IDENTIFIER )*
        print("Node: ", "property", arg)
        return "property"

    def string(self, arg):
        # string: ESCAPED_STRING
        print("Node: ", "string", arg)
        return "string"

    def number(self, arg):
        # number: SIGNED_INT | SIGNED_FLOAT
        print("Node: ", "number", arg)
        return "number"

    def __default__(self, data, children, meta):
        print("Node: ", data, children)
        return data


if __name__ == "__main__":  # pragma: no cover
    from optimade.filterparser import LarkParser

    p = LarkParser(version=(0, 10, 0))
    # t = DebugTransformer()
    t = TransformerSkeleton()

    # f = 'a.a = "text" OR a<a AND NOT b>=8'

    # single list

    f = "list HAS < 3"

    f = "list HAS < 3, > 4"  # -> error
    f = "list HAS ALL < 3, > 4"

    # multiple lists

    f = "list1:list2 HAS < 3 : > 4"
    f = "list1:list2 HAS ALL < 3 : > 4"

    f = "list1:list2 HAS < 3 : > 4, < 2 : > 5"  # -> error
    f = "list1:list2 HAS ALL < 3 : > 4, < 2 : > 5"
    f = "list1:list2 HAS ALL < 3, < 2 : > 4, > 5"  # -> error

    # f = 'list1:list2 HAS < 3, > 4'  # -> error
    # f = 'list1:list2 HAS ALL < 3, > 4'  # -> error

    f = 'elements:elements_ratios HAS ALL "Al":>0.3333, "Al":<0.3334'
    f = 'elements:elements_ratios HAS ALL "Al":>0.3333 AND elements_ratio<0.3334'
    f = 'elements:elements_ratios HAS ALL "Al" : >0.3333, <0.3334'  # -> error

    f = "list1:list2 HAS ALL < 3 : > 4, < 2 : > 5 : > 4, < 2 : > 5"  # valid but wrong
    f = "ghf.flk<gh"  # valid but wrong

    # f = ''

    tree = p.parse(f)
    print(tree)
    print(tree.pretty())

    t.transform(tree)
