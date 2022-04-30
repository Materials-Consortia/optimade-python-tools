"""This submodule implements the
[`MongoTransformer`][optimade.filtertransformers.mongo.MongoTransformer],
which takes the parsed filter and converts it to a valid pymongo/BSON query.
"""


import copy
import warnings
import itertools
from typing import Dict, List, Any
from lark import v_args, Token
from optimade.filtertransformers.base_transformer import BaseTransformer, Quantity
from optimade.server.exceptions import BadRequest
from optimade.server.warnings import TimestampNotRFCCompliant

__all__ = ("MongoTransformer",)


class MongoTransformer(BaseTransformer):
    """A filter transformer for the MongoDB backend.

    Parses a lark tree into a dictionary representation to be
    used by pymongo or mongomock. Uses post-processing functions
    to handle some specific edge-cases for MongoDB.

    Attributes:
        operator_map: A map from comparison operators
            to the mongoDB specific versions.
        inverse_operator_map: A map from operators to their
            logical inverse.
        mapper: A resource mapper object that defines the
            expected fields and acts as a container for
            various field-related configuration.

    """

    operator_map = {
        "<": "$lt",
        "<=": "$lte",
        ">": "$gt",
        ">=": "$gte",
        "!=": "$ne",
        "=": "$eq",
    }

    inverse_operator_map = {
        "$lt": "$gte",
        "$lte": "$gt",
        "$gt": "$lte",
        "$gte": "$lt",
        "$ne": "$eq",
        "$eq": "$ne",
        "$in": "$nin",
        "$nin": "$in",
    }

    def postprocess(self, query: Dict[str, Any]):
        """Used to post-process the nested dictionary of the parsed query."""
        query = self._apply_relationship_filtering(query)
        query = self._apply_length_operators(query)
        query = self._apply_unknown_or_null_filter(query)
        query = self._apply_has_only_filter(query)
        query = self._apply_mongo_id_filter(query)
        query = self._apply_mongo_date_filter(query)
        return query

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
        raise NotImplementedError("Correlated list queries are not supported.")

    def value_zip_list(self, arg):
        # value_zip_list: value_zip ( "," value_zip )*
        raise NotImplementedError("Correlated list queries are not supported.")

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
    def property_first_comparison(self, quantity, query):
        # property_first_comparison: property ( value_op_rhs | known_op_rhs | fuzzy_string_op_rhs | set_op_rhs |
        # set_zip_op_rhs | length_op_rhs )

        # Awkwardly, MongoDB will match null fields in $ne filters,
        # so we need to add a check for null equality in evey $ne query.
        if "$ne" in query:
            return {"$and": [{quantity: query}, {quantity: {"$ne": None}}]}

        # Check if a $size query is being made (indicating a length_op_rhs filter); if so, check for
        # a defined length alias to replace the $size call with the corresponding filter on the
        # length quantity then carefully merge the two queries.
        #
        # e.g. `("elements", {"$size": 2, "$all": ["Ag", "Au"]})` should become
        # `{"elements": {"$all": ["Ag", "Au"]}, "nelements": 2}` if the `elements` -> `nelements`
        # length alias is defined.
        if "$size" in query:
            if (
                getattr(self.backend_mapping.get(quantity), "length_quantity", None)
                is not None
            ):
                size_query = {
                    self.backend_mapping[
                        quantity
                    ].length_quantity.backend_field: query.pop("$size")
                }

                final_query = {}
                if query:
                    final_query = {quantity: query}
                for q in size_query:
                    if q in final_query:
                        final_query[q].update(size_query[q])
                    else:
                        final_query[q] = size_query[q]

                return final_query

        return {quantity: query}

    def constant_first_comparison(self, arg):
        # constant_first_comparison: constant OPERATOR ( non_string_value | not_implemented_string )
        return self.property_first_comparison(
            arg[2], {self.operator_map[self._reversed_operator_map[arg[1]]]: arg[0]}
        )

    @v_args(inline=True)
    def value_op_rhs(self, operator, value):
        # value_op_rhs: OPERATOR value
        return {self.operator_map[operator]: value}

    def known_op_rhs(self, arg):
        # known_op_rhs: IS ( KNOWN | UNKNOWN )
        # The OPTIMADE spec also required a type comparison with null, this must be post-processed
        # so here we use a special key "#known" which will get replaced in post-processing with the
        # expanded dict
        return {"#known": arg[1] == "KNOWN"}

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
            return {"#only": arg[2]}

        # value with OPERATOR
        raise NotImplementedError(
            f"set_op_rhs not implemented for use with OPERATOR. Given: {arg}"
        )

    def property(self, args):
        # property: IDENTIFIER ( "." IDENTIFIER )*
        quantity = super().property(args)
        if isinstance(quantity, Quantity):
            quantity = quantity.backend_field

        return ".".join([quantity] + args[1:])

    def length_op_rhs(self, arg):
        # length_op_rhs: LENGTH [ OPERATOR ] value
        if len(arg) == 2 or (len(arg) == 3 and arg[1] == "="):
            return {"$size": arg[-1]}

        if arg[1] in self.operator_map and arg[1] != "!=":
            # create an invalid query that needs to be post-processed
            # e.g. {'$size': {'$gt': 2}}, which is not allowed by Mongo.
            return {"$size": {self.operator_map[arg[1]]: arg[-1]}}

        raise NotImplementedError(
            f"Operator {arg[1]} not implemented for LENGTH filter."
        )

    def set_zip_op_rhs(self, arg):
        # set_zip_op_rhs: property_zip_addon HAS ( value_zip | ONLY value_zip_list | ALL value_zip_list |
        # ANY value_zip_list )
        raise NotImplementedError("Correlated list queries are not supported.")

    def property_zip_addon(self, arg):
        # property_zip_addon: ":" property (":" property)*
        raise NotImplementedError("Correlated list queries are not supported.")

    def _recursive_expression_phrase(self, arg: List) -> Dict[str, Any]:
        """Helper function for parsing `expression_phrase`. Recursively sorts out
        the correct precedence for `$not`, `$and` and `$or`.

        Parameters:
            arg: A list containing the expression to be evaluated and whether it
                is negated, e.g., `["NOT", expr]` or just `[expr]`.

        Returns:
             The evaluated filter as a nested dictionary.

        """

        def handle_not_and(arg: Dict[str, List]) -> Dict[str, List]:
            """Handle the case of `~(A & B) -> (~A | ~B)`.

            We have to check for the special case in which the "and" was created
            by a previous NOT, e.g.,
            `NOT (NOT ({"a": {"$eq": 6}})) -> NOT({"$and": [{"a": {"$ne": 6}},{"a": {"$ne": None}}]})`

            Parameters:
                arg: A dictionary with key `"$and"` containing a list of expressions.

            Returns:
                A dictionary with key `"$or"` containing a list of the appropriate negated expressions.
            """

            expr1 = arg["$and"][0]
            expr2 = arg["$and"][1]
            if expr1.keys() == expr2.keys():
                key = list(expr1.keys())[0]
                for e, f in itertools.permutations((expr1, expr2)):
                    if e.get(key) == {"$ne": None}:
                        return self._recursive_expression_phrase(["NOT", f])

            return {
                "$or": [
                    self._recursive_expression_phrase(["NOT", subdict])
                    for subdict in arg["$and"]
                ]
            }

        def handle_not_or(arg: Dict[str, List]) -> Dict[str, List]:
            """Handle the case of ~(A | B) -> (~A & ~B).

            !!! note
            Although the MongoDB `$nor` could be used here, it is not convenient as it
            will also return documents where the filtered field is missing when testing
            for inequality.

            Parameters:
                arg: A dictionary with key `"$or"` containing a list of expressions.

            Returns:
                A dictionary with key `"$and"` that lists the appropriate negated expressions.
            """

            return {
                "$and": [
                    self._recursive_expression_phrase(["NOT", subdict])
                    for subdict in arg["$or"]
                ]
            }

        if len(arg) == 1:
            # without NOT
            return arg[0]

        if "$or" in arg[1]:
            return handle_not_or(arg[1])

        if "$and" in arg[1]:
            return handle_not_and(arg[1])

        prop, expr = next(iter(arg[1].items()))
        operator, value = next(iter(expr.items()))
        if operator == "$not":  # Case of double negation e.g. NOT("$not":{ ...})
            return {prop: value}

        # If the NOT operator occurs at the lowest nesting level,
        # the expression can be simplified by using the opposite operator and removing the not.
        if operator in self.inverse_operator_map:
            filter_ = {prop: {self.inverse_operator_map[operator]: value}}
            if operator in ("$in", "$eq"):
                filter_ = {"$and": [filter_, {prop: {"$ne": None}}]}
            return filter_

        filter_ = {prop: {"$not": expr}}
        if "#known" in expr:
            return filter_
        return {"$and": [filter_, {prop: {"$ne": None}}]}

    def _apply_length_operators(self, filter_: dict) -> dict:
        """Check for any invalid pymongo queries that involve applying a
        comparison operator to the length of a field, and transform
        them into a test for existence of the relevant entry, e.g.
        "list LENGTH > 3" becomes "does the 4th list entry exist?".

        """

        def check_for_length_op_filter(_, expr):
            return (
                isinstance(expr, dict)
                and "$size" in expr
                and isinstance(expr["$size"], dict)
            )

        def apply_length_op(subdict, prop, expr):
            # assumes that the dictionary only has one element by design
            # (we just made it above in the transformer)
            operator, value = list(expr["$size"].items())[0]
            if operator in self.operator_map.values() and operator != "$ne":
                # worth being explicit here, I think
                _prop = None
                existence = None
                if operator == "$gt":
                    _prop = f"{prop}.{value + 1}"
                    existence = True
                elif operator == "$gte":
                    _prop = f"{prop}.{value}"
                    existence = True
                elif operator == "$lt":
                    _prop = f"{prop}.{value}"
                    existence = False
                elif operator == "$lte":
                    _prop = f"{prop}.{value + 1}"
                    existence = False
                if _prop is not None:
                    subdict.pop(prop)
                    subdict[_prop] = {"$exists": existence}

            return subdict

        return recursive_postprocessing(
            filter_,
            check_for_length_op_filter,
            apply_length_op,
        )

    def _apply_relationship_filtering(self, filter_: dict) -> dict:
        """Check query for property names that match the entry
        types, and transform them as relationship filters rather than
        property filters.

        """

        def check_for_entry_type(prop, _):
            return str(prop).count(".") == 1 and str(prop).split(".")[0] in (
                "structures",
                "references",
            )

        def replace_with_relationship(subdict, prop, expr):
            _prop, _field = str(prop).split(".")
            if _field != "id":
                raise NotImplementedError(
                    f'Cannot filter relationships by field "{_field}", only "id" is supported.'
                )

            subdict[f"relationships.{_prop}.data.{_field}"] = expr
            subdict.pop(prop)
            return subdict

        return recursive_postprocessing(
            filter_, check_for_entry_type, replace_with_relationship
        )

    def _apply_has_only_filter(self, filter_: dict) -> dict:
        """This method loops through the query and replaces the magic key `"#only"`
        with the proper 'HAS ONLY' query.
        """

        def check_for_only_filter(_, expr):
            """Find cases where the magic key `"#only"` is in the query."""
            return isinstance(expr, dict) and ("#only" in expr)

        def replace_only_filter(subdict: dict, prop: str, expr: dict):
            """Replace the magic key `"#only"` (added by this transformer) with an `$elemMatch`-based query.

            The first part of the query selects all the documents that contain any value that does not
            match any target values for the property `prop`.
            Subsequently, this selection is inverted, to get the documents that only have
            the allowed values.
            This inversion also selects documents with edge-case values such as null or empty lists;
            these are removed in the second part of the query that makes sure that only documents
            with lists that have at least one value are selected.

            """

            if "$and" not in subdict:
                subdict["$and"] = []

            if prop.startswith("relationships."):
                if prop not in (
                    "relationships.references.data.id",
                    "relationships.structures.data.id",
                ):
                    raise BadRequest(f"Unable to query on unrecognised field {prop}.")
                first_part_prop = ".".join(prop.split(".")[:-1])
                subdict["$and"].append(
                    {
                        first_part_prop: {
                            "$not": {"$elemMatch": {"id": {"$nin": expr["#only"]}}}
                        }
                    }
                )
                subdict["$and"].append({first_part_prop + ".0": {"$exists": True}})

            else:
                subdict["$and"].append(
                    {prop: {"$not": {"$elemMatch": {"$nin": expr["#only"]}}}}
                )
                subdict["$and"].append({prop + ".0": {"$exists": True}})

            subdict.pop(prop)
            return subdict

        return recursive_postprocessing(
            filter_, check_for_only_filter, replace_only_filter
        )

    def _apply_unknown_or_null_filter(self, filter_: dict) -> dict:
        """This method loops through the query and replaces the check for
        KNOWN with a check for existence and a check for not null, and the
        inverse for UNKNOWN.

        """

        def check_for_known_filter(_, expr):
            """Find cases where the query dict looks like
            `{"field": {"#known": T/F}}` or
            `{"field": "$not": {"#known": T/F}}`, which is a magic word
            for KNOWN/UNKNOWN filters in this transformer.

            """
            return isinstance(expr, dict) and (
                "#known" in expr or "#known" in expr.get("$not", {})
            )

        def replace_known_filter_with_or(subdict, prop, expr):
            """Replace magic key `"#known"` (added by this transformer) with the appropriate
            combination of `$exists` and/or test for nullity.
            combination of $exists and/or $eq/$ne null.

            """
            not_ = set(expr.keys()) == {"$not"}
            if not_:
                expr = expr["$not"]

            exists = expr["#known"] ^ not_

            top_level_key = "$or"
            comparison_operator = "$eq"
            if exists:
                top_level_key = "$and"
                comparison_operator = "$ne"

            if top_level_key not in subdict:
                subdict[top_level_key] = []

            subdict[top_level_key].append({prop: {"$exists": exists}})
            subdict[top_level_key].append({prop: {comparison_operator: None}})

            subdict.pop(prop)

            return subdict

        return recursive_postprocessing(
            filter_, check_for_known_filter, replace_known_filter_with_or
        )

    def _apply_mongo_id_filter(self, filter_: dict) -> dict:
        """This method loops through the query and replaces any operations
        on the special Mongodb `_id` key with the corresponding operation
        on a BSON `ObjectId` type.
        """

        def check_for_id_key(prop, _):
            """Find cases where the query dict is operating on the `_id` field."""
            return prop == "_id"

        def replace_str_id_with_objectid(subdict, prop, expr):
            from bson import ObjectId

            for operator in subdict[prop]:
                val = subdict[prop][operator]
                if operator not in ("$eq", "$ne"):
                    if self.mapper is not None:
                        prop = self.mapper.get_optimade_field(prop)
                    raise NotImplementedError(
                        f"Operator {operator} not supported for query on field {prop!r}, can only test for equality"
                    )
                if isinstance(val, str):
                    subdict[prop][operator] = ObjectId(val)
            return subdict

        return recursive_postprocessing(
            filter_, check_for_id_key, replace_str_id_with_objectid
        )

    def _apply_mongo_date_filter(self, filter_: dict) -> dict:
        """This method loops through the query and replaces any operations
        on suspected timestamp properties with the corresponding operation
        on a BSON `DateTime` type.
        """

        def check_for_timestamp_field(prop, _):
            """Find cases where the query dict is operating on a timestamp field."""
            if self.mapper is not None:
                prop = self.mapper.get_optimade_field(prop)
            return prop == "last_modified"

        def replace_str_date_with_datetime(subdict, prop, expr):
            """Encode suspected dates in with BSON."""
            import bson.json_util

            for operator in subdict[prop]:
                query_datetime = bson.json_util.loads(
                    bson.json_util.dumps({"$date": subdict[prop][operator]}),
                    json_options=bson.json_util.DEFAULT_JSON_OPTIONS.with_options(
                        tz_aware=True, tzinfo=bson.tz_util.utc
                    ),
                )
                if query_datetime.microsecond != 0:
                    warnings.warn(
                        f"Query for timestamp {subdict[prop][operator]!r} for field {prop!r} contained microseconds, which is not RFC3339 compliant. "
                        "This may cause undefined behaviour for the underlying database.",
                        TimestampNotRFCCompliant,
                    )

                subdict[prop][operator] = query_datetime

            return subdict

        return recursive_postprocessing(
            filter_, check_for_timestamp_field, replace_str_date_with_datetime
        )


def recursive_postprocessing(filter_, condition, replacement):
    """Recursively descend into the query, checking each dictionary
    (contained in a list, or as an entry in another dictionary) for
    the condition passed. If the condition is true, apply the
    replacement to the dictionary.

    Parameters:
        filter_ (list/dict): the filter_ to process.
        condition (callable): a function that returns True if the
            replacement function should be applied. It should take
            as arguments the property and expression from the filter_,
            as would be returned by iterating over `filter_.items()`.
        replacement (callable): a function that returns the processed
            dictionary. It should take as arguments the dictionary
            to modify, the property and the expression (as described
            above).

    Example:
        For the simple case of replacing one field name with
        another, the following functions could be used:

        ```python
        def condition(prop, expr):
            return prop == "field_name_old"

        def replacement(d, prop, expr):
            d["field_name_old"] = d.pop(prop)

        filter_ = recursive_postprocessing(
            filter_, condition, replacement
        )

        ```

    """
    if isinstance(filter_, list):
        result = [recursive_postprocessing(q, condition, replacement) for q in filter_]
        return result

    if isinstance(filter_, dict):
        # this could potentially lead to memory leaks if the filter_ is *heavily* nested
        _cached_filter = copy.deepcopy(filter_)
        for prop, expr in filter_.items():
            if condition(prop, expr):
                _cached_filter = replacement(_cached_filter, prop, expr)
            elif isinstance(expr, list):
                _cached_filter[prop] = [
                    recursive_postprocessing(q, condition, replacement) for q in expr
                ]
        return _cached_filter

    return filter_
