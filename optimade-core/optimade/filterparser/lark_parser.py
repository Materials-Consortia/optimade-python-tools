from pathlib import Path
from lark import Lark, Tree
from collections import defaultdict


class ParserError(Exception):
    pass


def get_versions():
    dct = defaultdict(dict)
    for filename in Path(__file__).parent.joinpath("../grammar").glob("*.lark"):
        tags = filename.stem.lstrip("v").split(".")
        version = tuple(map(int, tags[:3]))
        variant = "default" if len(tags) == 3 else tags[-1]
        dct[version][variant] = filename
    return dict(dct)


available_parsers = get_versions()


class LarkParser:
    def __init__(self, version=None, variant="default"):

        version = version if version else max(available_parsers.keys())

        if version not in available_parsers:
            raise ParserError(f"Unknown parser grammar version: {version}")

        if variant not in available_parsers[version]:
            raise ParserError(f"Unknown variant of the parser: {variant}")

        self.version = version
        self.variant = variant

        with open(available_parsers[version][variant]) as file:
            self.lark = Lark(file)

        self.tree = None
        self.filter = None

    def parse(self, filter_):
        try:
            self.tree = self.lark.parse(filter_)
            self.filter = filter_
            return self.tree
        except Exception as e:
            raise ParserError(e)

    def __repr__(self):
        if isinstance(self.tree, Tree):
            return self.tree.pretty()
        return repr(self.lark)
