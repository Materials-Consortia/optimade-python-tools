from lark import Transformer


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

    f = 'a.a = "text" OR a<a AND NOT b>=8'
    tree = p.parse(f)
    print(tree)
    print(tree.pretty())

    t.transform(tree)
