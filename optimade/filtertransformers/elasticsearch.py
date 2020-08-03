from typing import List

import lark
from elasticsearch_dsl import Q, Text, Keyword, Integer, Field
from optimade.models import CHEMICAL_SYMBOLS, ATOMIC_NUMBERS


_cmp_operators = {">": "gt", ">=": "gte", "<": "lt", "<=": "lte"}
_rev_cmp_operators = {">": "<", ">=": "<=", "<": ">", "<=": "=>"}
_has_operators = {"ALL": "must", "ANY": "should"}
_length_quantities = {
    "elements": "nelements",
    "elements_rations": "nelements",
    "dimension_types": "dimension_types",
}


class Quantity:
    """ Class to provide information about available quantities to the transformer.

    The elasticsearch transformer will :class:`Quantity`s to (a) do some semantic checks,
    (b) map quantities to the underlying elastic index.

    Attributes:
        name: The name of the quantity as used in the filter expressions.
        es_field: The name of the field for this quanity in elastic search, will be
            ``name`` by default.
        elastic_mapping_type: A decendent of an elasticsearch_dsl Field that denotes which
            mapping was used in the elastic search index.
        length_quantity: Elasticsearch does not support length of arrays, but we can
            map fields with array to other fields with ints about the array length. The
            LENGTH operator will only be supported for quantities with this attribute.
        has_only_quantity: Elasticsearch does not support exclusive search on arrays, like
            a list of chemical elements. But, we can order all elements by atomic number
            and use a keyword field with all elements to perform this search. This only
            works for elements (i.e. labels in ``CHEMICAL_SYMBOLS``) and quantities
            with this attribute.
        nested_quantity: To support optimade's 'zipped tuple' feature (e.g.
            'elements:elements_ratios HAS "H":>0.33), we use elasticsearch nested objects
            and nested queries. This quantity will provide the field for the nested
            object that contains the quantity (and others). The zipped tuples will only
            work for quantities that share the same nested object quantity.
    """

    def __init__(
        self,
        name,
        es_field: str = None,
        elastic_mapping_type: Field = None,
        length_quantity: "Quantity" = None,
        has_only_quantity: "Quantity" = None,
        nested_quantity: "Quantity" = None,
    ):

        self.name = name
        self.es_field = es_field if es_field is not None else name
        self.elastic_mapping_type = (
            Keyword if elastic_mapping_type is None else elastic_mapping_type
        )
        self.length_quantity = length_quantity
        self.has_only_quantity = has_only_quantity
        self.nested_quantity = nested_quantity

    def __repr__(self):
        return self.name


class Transformer(lark.Transformer):
    """ Transformer that transforms ``v0.10.0`` grammer parse trees into queries.

    Uses elasticsearch_dsl and will produce a :class:`Q` instance.
    """

    def __init__(self, quantities: List[Quantity]):
        """
        Arguments:
            quantities: A list of :class:`Quantity`s that describe how optimade (and other)
                quantities are mapped to the elasticsearch index.
        """
        self.index_mapping = {quantity.name: quantity for quantity in quantities}

    def _field(self, quantity, nested=None):
        if nested is not None:
            return "%s.%s" % (nested.es_field, quantity.name)

        return quantity.es_field

    def _order_terms(self, lhs, o, rhs):
        if isinstance(lhs, Quantity):
            if isinstance(rhs, Quantity):
                raise Exception(
                    "Cannot compare two quantities: %s, %s" % (lhs.name, rhs.name)
                )

            return lhs, o, rhs
        else:
            if isinstance(rhs, Quantity):
                o = _rev_cmp_operators.get(o, o)
                return rhs, o, lhs

            raise Exception("Cannot compare two values: %s, %s" % (str(lhs), str(lhs)))

    def _query(self, quantity, o, value, nested=None):
        field = self._field(quantity, nested=nested)
        if o in _cmp_operators:
            return Q("range", **{field: {_cmp_operators[o]: value}})

        if quantity.elastic_mapping_type == Text:
            query_type = "match"
        elif quantity.elastic_mapping_type in [Keyword, Integer]:
            query_type = "term"
        else:
            raise NotImplementedError("Quantity has unsupported ES field type")

        if o in ["=", ""]:
            return Q(query_type, **{field: value})

        if o == "!=":
            return ~Q(
                query_type, **{field: value}
            )  # pylint: disable=invalid-unary-operand-type

        raise Exception("Unknown operator %s" % o)

    def _has_query(self, quantities, predicates):
        if len(quantities) != len(predicates):
            raise Exception(
                "Tuple length does not match: %s <o> %s "
                % (":".join(quantities), ":".join(predicates))
            )

        if len(quantities) == 1:
            o, value = predicates[0]
            return self._query(quantities[0], o, value)

        nested_quantity = quantities[0].nested_quantity
        if nested_quantity is None or any(
            q.nested_quantity != nested_quantity for q in quantities
        ):
            raise Exception(
                "Expression with tuples are only supported for %s"
                % ", ".join(quantities)
            )

        queries = [
            self._query(field, o, value, nested=nested_quantity)
            for field, (o, value) in zip(quantities, predicates)
        ]

        return Q(
            "nested",
            path=self._field(nested_quantity),
            query=dict(bool=dict(must=queries)),
        )

    def _wildcard_query(self, quantity, wildcard):
        return Q("wildcard", **{self._field(quantity): wildcard})

    def __default__(self, tree, children, *args, **kwargs):
        """ Default behavior for rules that only replace one symbol with another """
        return children[0]

    def and_expr(self, args):
        if len(args) == 1:
            return args[0]
        l, r = args
        return l & r

    def or_expr(self, args):
        if len(args) == 1:
            return args[0]
        l, r = args
        return l | r

    def not_expr(self, args):
        (o,) = args
        return ~o

    def cmp_op(self, args):
        l, o, r = args
        field, o, value = self._order_terms(l, o, r)
        return self._query(field, o, value)

    def has_op(self, args):
        quantities, predicates = args
        return self._has_query(quantities, predicates)

    def has_list_op(self, args):
        quantities, o, predicates_list = args
        queries = [
            self._has_query(quantities, predicates) for predicates in predicates_list
        ]

        if o in _has_operators:
            return Q("bool", **{_has_operators[o]: queries})

        raise NotImplementedError

    def has_only_op(self, args):
        quantity, lst = args

        if quantity.has_only_quantity is None:
            raise Exception("HAS ONLY is not supported by %s" % quantity.name)

        def values():
            for predicates in lst:
                if len(predicates) != 1:
                    raise Exception("Tuples not supported in HAS ONLY")
                op, value = predicates[0]
                if op != "":
                    raise Exception("Predicated not supported in HAS ONLY")
                if not isinstance(value, str):
                    raise Exception("Only strings supported in HAS ONLY")
                yield value

        try:
            order_numbers = list([ATOMIC_NUMBERS[element] for element in values()])
            order_numbers.sort()
            value = "".join([CHEMICAL_SYMBOLS[number] for number in order_numbers])
        except KeyError:
            raise Exception("HAS ONLY is only supported for chemical symbols")

        return Q("term", **{quantity.has_only_quantity.name: value})

    def length(self, args):
        (quantity,) = args
        if quantity.length_quantity is None:
            raise Exception("LENGTH is not supported for %s" % quantity.name)

        return quantity.length_quantity

    def known_op(self, args):
        quantity, qualifier = args
        query = Q("exists", field=self._field(quantity))
        if qualifier == "KNOWN":
            return query
        elif qualifier == "UNKNOWN":
            return ~query  # pylint: disable=invalid-unary-operand-type

        raise NotImplementedError

    def contains_op(self, args):
        quantity, value = args
        return self._wildcard_query(quantity, "*%s*" % value)

    def starts_op(self, args):
        quantity, value = args
        return self._wildcard_query(quantity, "%s*" % value)

    def ends_op(self, args):
        quantity, value = args
        return self._wildcard_query(quantity, "*%s" % value)

    def list(self, args):
        return list(args)

    def quantity_tuple(self, args):
        return list(args)

    def predicate_tuple(self, args):
        return list(args)

    def predicate(self, args):
        if len(args) == 1:
            return "", args[0]
        else:
            return args[0], args[1]

    def quantity(self, args):
        quantity_name = args[0]

        if quantity_name not in self.index_mapping:
            raise Exception("%s is not a searchable quantity" % quantity_name)

        quantity = self.index_mapping.get(quantity_name, None)
        if quantity is None:
            quantity = Quantity(name=quantity_name)

        return quantity

    def int_literal(self, args):
        return int(args[0])

    def float_literal(self, args):
        return float(args[0])

    def string_literal(self, args):
        return args[0].strip('"')
