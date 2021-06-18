from functools import lru_cache
from typing import Any, Callable, Dict, Generator, List, NamedTuple, Tuple

from lark import LarkParser
from optimade.filtertransformers.ase import ASEQueryTree, ASETransformer
from optimade.models import EntryResource
from optimade.server.config import CONFIG
from optimade.server.entry_collections import EntryCollection
# from optimade.server.logger import LOGGER
from optimade.server.mappers import BaseResourceMapper

from ase.db import connect
# from ase.db.core import Database
from ase.db.row import AtomsRow
from ase.formula import Formula

INF = 9999999999999


class ASECollection(EntryCollection):
    def __init__(self,
                 name: str,
                 resource_cls: EntryResource,
                 resource_mapper: BaseResourceMapper,
                 database: str = CONFIG.ase_database):

        self.ase_transformer = ASETransformer(mapper=resource_mapper)

        super().__init__(resource_cls,
                         resource_mapper,
                         self.ase_transformer)

        self.parser = LarkParser(version=(1, 0, 0), variant="default")
        self.collection = ASEDBWrapper(database)

    def __len__(self) -> int:
        """Returns the total number of entries in the collection."""
        return len(self.collection)

    def xxxcount(self, *, filter, skip=0, limit=INF) -> int:
        return self.collection.count(filter, skip=skip, limit=limit)

    def _run_db_query(self,
                      criteria: Dict[str, Any],
                      single_entry: bool = False) -> Tuple[List[Dict[str,
                                                                     Any]],
                                                           int,
                                                           bool]:

        filter_function = create_filter_function(
            criteria['filter'],
            self.parser.parse,
            self.ase_transformer.transform)

        ids = [row.id
               for row in self.collection.select(filter_function,
                                                 skip=criteria['skip'])]

        results = [self.collection.get_result(id)
                   for id in ids[:criteria['limit']]]

        if single_entry:
            data_returned = len(results)
            more_data_available = False
        else:
            data_returned = len(ids)
            more_data_available = data_returned > len(results)

        return results, data_returned, more_data_available


class RowInfo(NamedTuple):
    """Summary of a row in a real ASE database (used for search)."""

    id: int
    elements: Dict[str, int]
    chemical_formula_hill: str
    chemical_formula_abc: str
    nsites: int


FilterFunction = Callable[[RowInfo], bool]


def dbrow2rowinfo(row: AtomsRow) -> RowInfo:
    """Pull out stuff needed for search."""
    formula = Formula(row.formula)
    rowinfo = RowInfo(row.id,
                      row.count_atoms(),
                      f'{formula:hill}',
                      f'{formula:abc}',
                      row.natoms)

    return rowinfo


class ASEDBWrapper:
    def __init__(self, db_filename: str):
        """Search interface for ASE database."""
        self.db = connect(db_filename)
        self.rows = [dbrow2rowinfo(dbrow) for dbrow in self.db.select()]

    def __len__(self):
        return len(self.rows)

    def select(self,
               filter_function: FilterFunction,
               skip: int = 0,
               limit: int = INF) -> Generator[RowInfo, None, None]:
        """Select rows using a filter function."""
        for i, row in enumerate(self.rows):
            if i == skip + limit:
                return
            if i >= skip and filter_function(row):
                yield row

    def xxxcount(self, filter: str, skip=0, limit=INF):
        return sum(1 for _ in self.select(filter, skip=skip, limit=limit))


def create_code_string(query: ASEQueryTree) -> str:
    """Convert query-tree object to a Python function.

    Example:

    >>> tree = ('AND', [('nelements', ('=', 3)),
    ...                 ('elements', ('HAS', '"Cu"'))])
    >>> create_code_string(tree)
    '(len(row.elements) == 3) and ("Cu" in row.elements)'
    """

    q1, q2 = query

    if q1 == 'AND':
        return ' and '.join(f'({create_code_string(q)})' for q in q2)

    if q1 == 'nelements':
        op, val = q2
        if op == '=':
            op = '=='
        return f'len(row.elements) {op} {val}'

    if q1 == 'elements':
        q3, q4 = q2

        if q3 == 'HAS':
            return f'{q4} in row.elements'

        if q3 == 'HAS ALL':
            return f'all(symbol in row.elements for symbol in {q4})'

    raise NotImplementedError(query)


@lru_cache(maxsize=100)
def xxxcreate_filter_function(query) -> Callable[[RowInfo], bool]:
    """Convert OPTIMADE query string to a Python filter function."""
    code_string = create_code_string(query)
    code = compile('lambda row: ' + code_string,
                   '<string>',
                   'eval')
    filter_function = eval(code)
    return filter_function


@lru_cache(maxsize=100)
def create_filter_function(optimade_query: str,
                           parse,
                           transform) -> FilterFunction:
    """Convert OPTIMADE query string to a Python filter function."""
    tree = parse(optimade_query)
    query = transform(tree)
    code_string = create_code_string(query)
    code = compile('lambda row: ' + code_string,
                   '<string>',
                   'eval')
    filter_function = eval(code)
    return filter_function
