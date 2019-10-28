from lark import Transformer
from lark.lexer import Token


class JSONTransformer(Transformer):
    def __init__(self, compact=False):
        self.compact = compact
        super().__init__()

    def __default__(self, data, children, meta):
        items = []
        for c in children:
            if isinstance(c, Token):
                token_repr = {
                    "@module": "lark.lexer",
                    "@class": "Token",
                    "type_": c.type,
                    "value": c.value,
                }
                if self.compact:
                    del token_repr["@module"]
                    del token_repr["@class"]
                items.append(token_repr)
            elif isinstance(c, dict):
                items.append(c)
            else:
                raise ValueError(f"Unknown type {type(c)} for tree child {c}")
        tree_repr = {
            "@module": "lark",
            "@class": "Tree",
            "data": data,
            "children": items,
        }
        if self.compact:
            del tree_repr["@module"]
            del tree_repr["@class"]
        return tree_repr


class DebugTransformer(Transformer):
    """Prints out all the nodes and its arguments during the walk-through of the tree."""

    def __init__(self):
        super().__init__()

    def __default__(self, data, children, meta):
        print('Node: ', data, children)
        return data


if __name__ == '__main__':
    from optimade.filterparser import LarkParser

    p = LarkParser(version=(0, 10, 0))
    t = DebugTransformer()
    # t = JSONTransformer(compact=True)

    f = 'a.a = "asdfsd" OR a<a AND NOT b>=8'
    print(p.parse(f))
    print(t.transform(p.parse(f)))
