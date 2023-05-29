from __future__ import annotations

import operator
from typing import Any, Dict, List, Type

import numpy as np
from ase.data import atomic_numbers
from ase.formula import Formula
from lark.lexer import Token  # type: ignore
from lark.tree import Tree  # type: ignore
from optiamde.filtertransformers.base_transformer import BaseTransformer
from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    and_,
    create_engine,
    not_,
    or_,
    select,
)
from sqlalchemy.sql.elements import ColumnElement as Clauses

from optimade.models import EntryResource
from optimade.server.config import CONFIG
from optimade.server.entry_collections import EntryCollection
from optimade.server.mappers import BaseResourceMapper

OPS = {
    "=": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
}

REVERSE_OPS = {">": "<", "<": ">", ">=": "<=", "<=": ">="}

SPECIAL = {
    "nsites",
    "nelements",
    "nperiodic_dimensions",
    "chemical_formula_descriptive",
    "chemical_formula_reduced",
    "chemical_formula_anonymous",
    "chemical_formula_hill",
}

LENGTH_ALIASES = {
    "elements": "nelements",
    "element_ratios": "nelements",
    "cartesian_site_positions": "nsites",
    "species_at_sites": "nsites",
}


class SQLStructureCollection(EntryCollection):
    def __init__(
        self,
        name: str,
        resource_cls: Type[EntryResource],
        resource_mapper: Type[BaseResourceMapper],
        database: str = CONFIG.sql_database,
    ):
        super().__init__(
            resource_cls, resource_mapper, BaseTransformer(mapper=resource_mapper)
        )

        self.engine = create_engine(database, echo=False)

        self.metadata = self.create_metadata()
        self.kinds: Dict[str, str] = {}
        self.structures = self.metadata.tables["structures"]
        self.species = self.metadata.tables["species"]
        self.structure_features = self.metadata.tables["structure_features"]
        self.nstructures = 0

    def initialise_tables(self):
        self.metadata.create_all(self.engine)

    def insert(self, data: List[EntryResource]) -> None:
        """Insert OPTIMADE structures into the corresponding SQL tables."""

        key_value_data: Dict[str, List[Dict]] = {
            "strings": [],
            "ints": [],
            "floats": [],
        }
        tables = self.metadata.tables

        structures = []
        species = []

        for entry in data:
            _id = entry.id
            attributes = entry.attributes
            _type = entry.type
            assert _type == self.resource_cls.type

            attributes = attributes | {"id": str(_id)}

            symbols = attributes.species_at_sites
            formula = Formula.from_list(symbols)
            count = formula.count()
            for symbol, n in count.items():
                species.append({"_id": _id, "Z": atomic_numbers[symbol], "count": n})
            structures.append(attributes)

            for key, value in attributes.items():
                if isinstance(value, str):
                    kind = "strings"
                elif isinstance(value, int):
                    kind = "ints"
                elif isinstance(value, float):
                    kind = "floats"
                else:
                    raise ValueError
                k = self.kinds.get(key)
                if k is not None:
                    if k != kind:
                        raise ValueError
                else:
                    self.kinds[key] = kind
                key_value_data[kind].append({"_id": id, "name": key, "value": value})

        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(tables["structures"].insert(), structures)
                conn.execute(tables["species"].insert(), species)
                for name, data in key_value_data.items():
                    conn.execute(tables[name].insert(), data)

    def execute(self, clauses: Clauses) -> list[int]:
        """Execute SQL-SELECT statement."""
        selection = select(self.structures.c._id).where(clauses)
        with self.engine.connect() as conn:
            result = [row for row in conn.execute(selection)]
        return result

    def _run_db_query(
        self, criteria, single_entry: bool = False
    ) -> List[EntryResource]:
        _filter = criteria.pop("filter", "")
        tree = parse_lark_tree(self.parser.parse(_filter))
        selection = self.select(tree)
        results = self.execute(selection)
        return results

    def _get_row_ids(self, query: str) -> list[int]:
        if query:
            tree = self.parse(query)
            selection = self.select(tree)
            rowids = self.execute(selection)
        else:
            rowids = list(range(1, self.nstructures + 1))
        return rowids

    def select(self, node: Any) -> Clauses:
        """Create SELECT SQL-statement."""
        if len(node) == 3:
            n1, n2, n3 = node
            if n2[0] == "OPERATOR" and n3[0] == "IDENTIFIER":
                key = n3[1]
                op = n2[1]
                value = n1
                op = REVERSE_OPS.get(op, op)
                return self.compare(key, op, value)
            raise ValueError

        n1, n2 = node
        if n1 == "OR":
            return or_(*(self.select(value) for value in n2))
        if n1 == "AND":
            return and_(*(self.select(value) for value in n2))
        if n1 == ("NOT", "NOT"):
            return not_(self.select(n2))
        if n1[0] == "IDENTIFIER":
            key = n1[1]
            *n3, n4 = n2
            name = " ".join(n[0] for n in n3)
            if name == "HAS":
                value = n4
                return self.has(key, value)
            if name == "HAS ALL":
                values = n4 if isinstance(n4, list) else [n4]
                return and_(*(self.has(key, value) for value in values))
            if name == "HAS ANY":
                values = n4 if isinstance(n4, list) else [n4]
                return or_(*(self.has(key, value) for value in values))
            if name in {"ENDS WITH", "ENDS"}:
                value = n4
                assert isinstance(value, str)
                return self.endswith(key, value)
            if name in {"STARTS WITH", "STARTS"}:
                value = n4
                assert isinstance(value, str)
                return self.startswith(key, value)
            if name == "CONTAINS":
                value = n4
                assert isinstance(value, str)
                return self.contains(key, value)
            if name.startswith("LENGTH"):
                value = n4
                op = "="
                if name.endswith("OPERATOR"):
                    op = n3[1][1]
                return self.length(key, op, value)
            if n3[0][0] == "OPERATOR":
                op = n3[0][1]
                value = n4
                return self.compare(key, op, value)

        raise ValueError

    def has(self, key: str, value: str) -> Clauses:
        """Implemention of "elements HAS symbol"."""
        if key in {"elements", "species_at_sites"}:
            Z = atomic_numbers[value]
            return self.structures.c._id.in_(
                select(self.species.c._id).where(self.species.c.Z == Z)
            )
        assert key == "structure_features"
        return and_(
            self.structure_features.c._id == self.structures.c._id,
            self.structure_features.c.name == value,
        )

    def compare(self, key: str, op: str, value: int | float | str) -> Clauses:
        """Implemention of "key <op> value"."""
        cmp = OPS[op]
        if key in SPECIAL:
            return cmp(self.structures.c[key], value)
        table = self.metadata.tables[self.kinds.get(key, "ints")]
        return and_(
            table.c._id == self.structures.c._id,
            table.c.name == key,
            cmp(table.c.value, value),
        )

    def endswith(self, key: str, value: str) -> Clauses:
        """Implemention of "key <op> value"."""
        if key in SPECIAL:
            return self.structures.c[key].endswith(value)
        table = self.metadata.tables["strings"]
        return and_(
            table.c._id == self.structures.c._id,
            table.c.name == key,
            table.c.value.endswith(value),
        )

    def startswith(self, key: str, value: str) -> Clauses:
        """Implemention of "key <op> value"."""
        if key in SPECIAL:
            return self.structures.c[key].startswith(value)
        table = self.metadata.tables["strings"]
        return and_(
            table.c._id == self.structures.c._id,
            table.c.name == key,
            table.c.value.startswith(value),
        )

    def contains(self, key: str, value: str) -> Clauses:
        """Implemention of "key <op> value"."""
        if key in SPECIAL:
            return self.structures.c[key].contains(value)
        table = self.metadata.tables["strings"]
        return and_(
            table.c._id == self.structures.c._id,
            table.c.name == key,
            table.c.value.contains(value),
        )

    def length(self, key: str, op: str, value: int) -> Clauses:
        """Implements "key LENGTH <op> value" via the pre-defined
        `LENGTH_ALIASES`, e.g., when querying for the LENGTH of
        `elements`, use the auxiliary `nelements` field.

        """
        if key in LENGTH_ALIASES:
            return self.compare(LENGTH_ALIASES[key], op, value)
        raise NotImplementedError(f"Length filter not supported on field {key!r}")

    def create_metadata(self) -> MetaData:
        """Create SQL metadata."""
        metadata = MetaData()
        Table(
            "structures",
            metadata,
            Column("_id", Integer, primary_key=True),
            *(
                Column(
                    key, Integer if isinstance(value, int) else String
                )  # type: ignore
                for key, value in get_optimade_things(
                    Formula("H"), np.zeros(3, bool)
                ).items()
            ),
        )
        Table(
            "species",
            metadata,
            Column("_id", Integer, ForeignKey("structures._id")),
            Column("Z", Integer),
            Column("n", Integer),
        )
        Table(
            "ints",
            metadata,
            Column("_id", Integer, ForeignKey("structures._id")),
            Column("name", String),
            Column("value", Integer),
        )
        Table(
            "floats",
            metadata,
            Column("_id", Integer, ForeignKey("structures._id")),
            Column("name", String),
            Column("value", Float),
        )
        Table(
            "strings",
            metadata,
            Column("_id", Integer, ForeignKey("structures._id")),
            Column("name", String),
            Column("value", String),
        )
        Table(
            "structure_features",
            metadata,
            Column("_id", Integer, ForeignKey("structures._id")),
            Column("name", String),
        )

        return metadata


def get_optimade_things(formula: Formula, pbc: np.ndarray) -> dict:
    """Collect some OPTIMADE stuff."""
    _, reduced, num = formula.stoichiometry()
    count = reduced.count()

    # Alphapetically sorted:
    reduced = Formula.from_dict({symbol: count[symbol] for symbol in sorted(count)})

    # Elements with highest proportion should appear first:
    c = ord("A")
    dct = {}
    for n in sorted(count.values(), reverse=True):
        dct[chr(c)] = n
        c += 1
    anonymous = Formula.from_dict(dct)

    return {
        "chemical_formula_descriptive": None,
        "chemical_formula_reduced": f"{reduced}",
        "chemical_formula_anonymous": f"{anonymous}",
        "chemical_formula_hill": f"{formula:hill}",
        "nsites": num * sum(count.values()),
        "nelements": len(count),
        "nperiodic_dimensions": int(sum(pbc)),
    }


def parse_lark_tree(node: Tree | Token) -> Any:
    """Convert Lark tree to simple data structure.

    See examples in ``parser_test.py``.
    """
    if isinstance(node, Token):
        if node.type == "SIGNED_INT":
            return int(node.value)
        if node.type == "SIGNED_FLOAT":
            return float(node.value)
        if node.type == "ESCAPED_STRING":
            return node.value[1:-1]
        return (node.type, node.value)
    children = [parse_lark_tree(child) for child in node.children]  # type: ignore
    if len(children) == 1:
        return children[0]
    if node.data == "expression":
        return ("OR", children)
    if node.data == "expression_clause":
        return ("AND", children)

    return children
