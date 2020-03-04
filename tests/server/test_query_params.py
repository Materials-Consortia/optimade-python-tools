# pylint: disable=relative-beyond-top-level,import-outside-toplevel
import unittest
from typing import Sequence

from optimade.server.config import CONFIG
from optimade.server import mappers
from optimade.server.entry_collections import CI_FORCE_MONGO

from .utils import SetClient

MONGOMOCK_OLD = False
MONGOMOCK_MSG = ""
if not CI_FORCE_MONGO and not CONFIG.use_real_mongo:
    import mongomock

    MONGOMOCK_OLD = tuple(
        int(val) for val in mongomock.__version__.split(".")[0:3]
    ) <= (3, 19, 0)
    MONGOMOCK_MSG = f"mongomock version {mongomock.__version__}<=3.19.0 is too old for this test, skipping..."


class IncludeTests(SetClient, unittest.TestCase):
    """Make sure `include` is handled correctly

    NOTE: Currently _only_ structures have relationships (references).
    """

    server = "regular"

    def check_response(
        self,
        request: str,
        expected_included_types: Sequence,
        expected_included_resources: Sequence,
        expected_relationship_types: Sequence = None,
    ):
        try:
            response = self.client.get(request)
            self.assertEqual(
                response.status_code, 200, msg=f"Request failed: {response.json()}"
            )

            response = response.json()
            response_data = (
                response["data"]
                if isinstance(response["data"], list)
                else [response["data"]]
            )

            included_resource_types = list({_["type"] for _ in response["included"]})
            self.assertEqual(
                sorted(expected_included_types),
                sorted(included_resource_types),
                msg=f"Expected relationship types: {expected_included_types}. "
                f"Does not match relationship types in response's included field: {included_resource_types}",
            )

            if expected_relationship_types is None:
                expected_relationship_types = expected_included_types
            relationship_types = set()
            for entry in response_data:
                relationship_types.update(set(entry.get("relationships", {}).keys()))
            self.assertEqual(
                sorted(expected_relationship_types),
                sorted(relationship_types),
                msg=f"Expected relationship types: {expected_relationship_types}. "
                f"Does not match relationship types found in response data: {relationship_types}",
            )

            included_resources = [_["id"] for _ in response["included"]]
            self.assertEqual(
                len(included_resources),
                len(expected_included_resources),
                msg=response["included"],
            )
            self.assertEqual(
                sorted(set(included_resources)), sorted(expected_included_resources)
            )

        except Exception as exc:
            print("Request attempted:")
            print(f"{self.client.base_url}{request}")
            raise exc

    def check_error_response(
        self,
        request,
        expected_status: int = 400,
        expected_title: str = "Bad Request",
        expected_detail: str = None,
    ):
        try:
            response = self.client.get(request)
            self.assertEqual(
                response.status_code,
                expected_status,
                msg=f"Request should have been an error with status code {expected_status}, "
                f"but instead {response.status_code} was received.\nResponse:\n{response.json()}",
            )
            response = response.json()
            self.assertEqual(len(response["errors"]), 1)
            self.assertEqual(response["meta"]["data_returned"], 0)

            error = response["errors"][0]
            self.assertEqual(str(expected_status), error["status"])
            self.assertEqual(expected_title, error["title"])

            if expected_detail is None:
                expected_detail = "Error trying to process rule "
                self.assertTrue(error["detail"].startswith(expected_detail))
            else:
                self.assertEqual(expected_detail, error["detail"])

        except Exception as exc:
            print("Request attempted:")
            print(f"{self.client.base_url}{request}")
            raise exc

    def test_default_value(self):
        """Default value for `include` is 'references'

        Test also that passing `include=` equals passing the default value
        """
        request = "/structures"
        expected_types = ["references"]
        expected_reference_ids = ["dijkstra1968", "maddox1988", "dummy/2019"]
        self.check_response(request, expected_types, expected_reference_ids)

        request = "/structures?include="
        self.check_response(request, expected_types, expected_reference_ids)

        # Single entry
        request = "/structures/mpf_1"
        expected_types = ["references"]
        expected_reference_ids = ["dijkstra1968"]
        self.check_response(request, expected_types, expected_reference_ids)

        request = "/structures/mpf_1?include="
        self.check_response(request, expected_types, expected_reference_ids)

    def test_empty_value(self):
        """An empty value should resolve in no relationships being returned under `included`"""
        request = '/structures?include=""'
        expected_types = []
        expected_reference_ids = []
        expected_data_relationship_types = ["references"]
        self.check_response(
            request,
            expected_types,
            expected_reference_ids,
            expected_data_relationship_types,
        )

        request = "/structures?include=''"
        self.check_response(
            request,
            expected_types,
            expected_reference_ids,
            expected_data_relationship_types,
        )

        # Single entry
        request = "/structures/mpf_1?include=''"
        self.check_response(
            request,
            expected_types,
            expected_reference_ids,
            expected_data_relationship_types,
        )

        request = "/structures/mpf_1?include=''"
        self.check_response(
            request,
            expected_types,
            expected_reference_ids,
            expected_data_relationship_types,
        )

    def test_default_value_single_entry(self):
        """For single entry. Default value for `include` is 'references'"""
        request = "/structures/mpf_1"
        expected_types = ["references"]
        expected_reference_ids = ["dijkstra1968"]
        self.check_response(request, expected_types, expected_reference_ids)

    def test_empty_value_single_entry(self):
        """For single entry. An empty value should resolve in no relationships being returned under `included`"""
        request = '/structures/mpf_1?include=""'
        expected_types = []
        expected_reference_ids = []
        expected_data_relationship_types = ["references"]
        self.check_response(
            request,
            expected_types,
            expected_reference_ids,
            expected_data_relationship_types,
        )

        request = "/structures/mpf_1?include=''"
        self.check_response(
            request,
            expected_types,
            expected_reference_ids,
            expected_data_relationship_types,
        )

    def test_wrong_relationship_type(self):
        """A wrong type should result in a `400 Bad Request` response"""
        from optimade.server.routers import ENTRY_COLLECTIONS

        wrong_type = "test"
        request = f"/structures?include={wrong_type}"
        error_detail = (
            f"'{wrong_type}' cannot be identified as a valid relationship type. "
            f"Known relationship types: {sorted(ENTRY_COLLECTIONS.keys())}"
        )
        self.check_error_response(request, expected_detail=error_detail)


class ResponseFieldTests(SetClient, unittest.TestCase):
    """Make sure response_fields is handled correctly"""

    server = "regular"

    get_mapper = {
        "links": mappers.LinksMapper,
        "references": mappers.ReferenceMapper,
        "structures": mappers.StructureMapper,
    }

    def check_response(self, request, expected_fields):
        try:
            response = self.client.get(request)
            self.assertEqual(
                response.status_code, 200, msg=f"Request failed: {response.json()}"
            )

            response = response.json()
            response_fields = set()
            for entry in response["data"]:
                response_fields.update(set(entry.keys()))
                response_fields.update(set(entry["attributes"].keys()))
            self.assertEqual(sorted(expected_fields), sorted(response_fields))
        except Exception as exc:
            print("Request attempted:")
            print(f"{self.client.base_url}{request}")
            raise exc

    def required_fields_test_helper(
        self, endpoint: str, known_unused_fields: set, response_fields: set
    ):
        """Utility function for creating required fields tests"""
        response_fields |= (
            self.get_mapper[endpoint].get_required_fields() - known_unused_fields
        )
        response_fields.add("attributes")
        request = f"/{endpoint}?response_fields={','.join(response_fields)}"
        self.check_response(request, response_fields)

    def test_required_fields_links(self):
        """Certain fields are REQUIRED, no matter the value of `response_fields`"""
        endpoint = "links"
        illegal_top_level_field = "relationships"
        non_used_top_level_fields = {"links"}
        non_used_top_level_fields.add(illegal_top_level_field)
        expected_fields = {"homepage", "base_url"}
        self.required_fields_test_helper(
            endpoint, non_used_top_level_fields, expected_fields
        )

    def test_required_fields_references(self):
        """Certain fields are REQUIRED, no matter the value of `response_fields`"""
        endpoint = "references"
        non_used_top_level_fields = {"links", "relationships"}
        expected_fields = {"year", "journal"}
        self.required_fields_test_helper(
            endpoint, non_used_top_level_fields, expected_fields
        )

    def test_required_fields_structures(self):
        """Certain fields are REQUIRED, no matter the value of `response_fields`"""
        endpoint = "structures"
        non_used_top_level_fields = {"links"}
        expected_fields = {"elements", "nelements"}
        self.required_fields_test_helper(
            endpoint, non_used_top_level_fields, expected_fields
        )


class FilterTests(SetClient, unittest.TestCase):

    server = "regular"

    def test_custom_field(self):
        request = '/structures?filter=_exmpl__mp_chemsys="Ac"'
        expected_ids = ["mpf_1"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_id(self):
        request = "/structures?filter=id=mpf_2"
        expected_ids = ["mpf_2"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_geq(self):
        request = "/structures?filter=nelements>=9"
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_gt(self):
        request = "/structures?filter=nelements>8"
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_rhs_comparison(self):
        request = "/structures?filter=8<nelements"
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_gt_none(self):
        request = "/structures?filter=nelements>9"
        expected_ids = []
        self._check_response(request, expected_ids, len(expected_ids))

    def test_list_has(self):
        request = '/structures?filter=elements HAS "Ti"'
        expected_ids = ["mpf_3803", "mpf_3819"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_page_limit(self):
        request = '/structures?filter=elements HAS "Ac"&page_limit=2'
        expected_ids = ["mpf_1", "mpf_2"]
        expected_return = 6
        self._check_response(request, expected_ids, expected_return)

        request = '/structures?page_limit=2&filter=elements HAS "Ac"'
        expected_ids = ["mpf_1", "mpf_2"]
        expected_return = 6
        self._check_response(request, expected_ids, expected_return)

    def test_page_limit_max(self):
        request = f"/structures?page_limit={CONFIG.page_limit_max + 1}"
        self._check_error_response(
            request,
            expected_status=403,
            expected_title="HTTPException",
            expected_detail=f"Max allowed page_limit is {CONFIG.page_limit_max}, you requested {CONFIG.page_limit_max + 1}",
        )

    def test_value_list_operator(self):
        request = "/structures?filter=dimension_types HAS < 1"
        self._check_error_response(
            request,
            expected_status=501,
            expected_title="NotImplementedError",
            expected_detail="set_op_rhs not implemented for use with OPERATOR. Given: [Token(HAS, 'HAS'), Token(OPERATOR, '<'), 1]",
        )

    def test_has_any_operator(self):
        request = "/structures?filter=dimension_types HAS ANY > 1"
        self._check_error_response(
            request,
            expected_status=501,
            expected_title="NotImplementedError",
            expected_detail="OPERATOR > inside value_list [Token(OPERATOR, '>'), 1] not implemented.",
        )

    def test_list_has_all(self):
        request = '/structures?filter=elements HAS ALL "Ba","F","H","Mn","O","Re","Si"'
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids, len(expected_ids))

        request = '/structures?filter=elements HAS ALL "Re","Ti"'
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_list_has_any(self):
        request = '/structures?filter=elements HAS ANY "Re","Ti"'
        expected_ids = ["mpf_3819", "mpf_3803"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_list_length_basic(self):
        request = "/structures?filter=elements LENGTH = 9"
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids, len(expected_ids))

        request = "/structures?filter=elements LENGTH 9"
        self._check_response(request, expected_ids, len(expected_ids))

    def test_list_length(self):
        request = "/structures?filter=elements LENGTH >= 9"
        error_detail = "Operator >= not implemented for LENGTH filter."
        self._check_error_response(
            request,
            expected_status=501,
            expected_title="NotImplementedError",
            expected_detail=error_detail,
        )
        # expected_ids = ["mpf_3819"]
        # self._check_response(request, expected_ids, len(expected_ids))

        request = "/structures?filter=structure_features LENGTH > 0"
        error_detail = "Operator > not implemented for LENGTH filter."
        self._check_error_response(
            request,
            expected_status=501,
            expected_title="NotImplementedError",
            expected_detail=error_detail,
        )
        # expected_ids = []
        # self._check_response(request, expected_ids, len(expected_ids))

    @unittest.skipIf(MONGOMOCK_OLD, MONGOMOCK_MSG)
    def test_list_has_only(self):
        """ Test HAS ONLY query on elements.

        This test fails with mongomock<=3.19.0 when $size is 1, but works with a real mongo.

        TODO: this text and skip condition should be removed once mongomock>3.19.0 has been released, which should
        contain the bugfix for this: https://github.com/mongomock/mongomock/pull/597.

        """

        request = '/structures?filter=elements HAS ONLY "Ac", "Mg"'
        expected_ids = ["mpf_23"]
        self._check_response(request, expected_ids, len(expected_ids))

        request = '/structures?filter=elements HAS ONLY "Ac"'
        expected_ids = ["mpf_1"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_list_correlated(self):
        request = '/structures?filter=elements:elements_ratios HAS "Ag":"0.2"'
        self._check_error_response(
            request, expected_status=501, expected_title="NotImplementedError"
        )
        # expected_ids = ["mpf_259"]
        # self._check_response(request, expected_ids, len(expected_ids))

    def test_is_known(self):
        request = "/structures?filter=nsites IS KNOWN AND nsites>=44"
        expected_ids = ["mpf_551", "mpf_3803", "mpf_3819"]
        self._check_response(request, expected_ids, len(expected_ids))

        request = "/structures?filter=lattice_vectors IS KNOWN AND nsites>=44"
        expected_ids = ["mpf_551", "mpf_3803", "mpf_3819"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_aliased_is_known(self):
        request = "/structures?filter=id IS KNOWN AND nsites>=44"
        expected_ids = ["mpf_551", "mpf_3803", "mpf_3819"]
        self._check_response(request, expected_ids, len(expected_ids))

        request = "/structures?filter=chemical_formula_reduced IS KNOWN AND nsites>=44"
        expected_ids = ["mpf_551", "mpf_3803", "mpf_3819"]
        self._check_response(request, expected_ids, len(expected_ids))

        request = (
            "/structures?filter=chemical_formula_descriptive IS KNOWN AND nsites>=44"
        )
        expected_ids = ["mpf_551", "mpf_3803", "mpf_3819"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_aliased_fields(self):
        request = '/structures?filter=chemical_formula_anonymous="A"'
        expected_ids = ["mpf_1", "mpf_200"]
        self._check_response(request, expected_ids, len(expected_ids))

        request = '/structures?filter=chemical_formula_anonymous CONTAINS "A2BC"'
        expected_ids = ["mpf_2", "mpf_3", "mpf_110"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_string_contains(self):
        request = '/structures?filter=chemical_formula_descriptive CONTAINS "c2Ag"'
        expected_ids = ["mpf_3", "mpf_2"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_string_start(self):
        request = (
            '/structures?filter=chemical_formula_descriptive STARTS WITH "Ag2CSNCl"'
        )
        expected_ids = ["mpf_259"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_string_end(self):
        request = '/structures?filter=chemical_formula_descriptive ENDS WITH "NClO4"'
        expected_ids = ["mpf_259"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_list_has_and(self):
        request = '/structures?filter=elements HAS "Ac" AND nelements=1'
        expected_ids = ["mpf_1"]
        self._check_response(request, expected_ids, len(expected_ids))

    def test_not_or_and_precedence(self):
        request = '/structures?filter=NOT elements HAS "Ac" AND nelements=1'
        expected_ids = ["mpf_200"]
        self._check_response(request, expected_ids, len(expected_ids))

        request = '/structures?filter=nelements=1 AND NOT elements HAS "Ac"'
        expected_ids = ["mpf_200"]
        self._check_response(request, expected_ids, len(expected_ids))

        request = '/structures?filter=NOT elements HAS "Ac" AND nelements=1 OR nsites=1'
        expected_ids = ["mpf_1", "mpf_200"]
        self._check_response(request, expected_ids, len(expected_ids))

        request = '/structures?filter=elements HAS "Ac" AND nelements>1 AND nsites=1'
        expected_ids = []
        self._check_response(request, expected_ids, len(expected_ids))

    def test_brackets(self):
        request = '/structures?filter=elements HAS "Ac" AND nelements=1 OR nsites=1'
        expected_ids = ["mpf_200", "mpf_1"]
        self._check_response(request, expected_ids, len(expected_ids))

        request = '/structures?filter=(elements HAS "Ac" AND nelements=1) OR (elements HAS "Ac" AND nsites=1)'
        expected_ids = ["mpf_1"]
        self._check_response(request, expected_ids, len(expected_ids))

    def _check_response(self, request, expected_ids, expected_return):
        try:
            response = self.client.get(request)
            self.assertEqual(
                response.status_code, 200, msg=f"Request failed: {response.json()}"
            )
            response = response.json()
            response_ids = [struct["id"] for struct in response["data"]]
            self.assertEqual(sorted(expected_ids), sorted(response_ids))
            self.assertEqual(response["meta"]["data_returned"], expected_return)
        except Exception as exc:
            print("Request attempted:")
            print(f"{self.client.base_url}{request}")
            raise exc

    def _check_error_response(
        self,
        request,
        expected_status: int = 500,
        expected_title: str = None,
        expected_detail: str = None,
    ):
        try:
            response = self.client.get(request)
            self.assertEqual(
                response.status_code,
                expected_status,
                msg=f"Request should have been an error with status code {expected_status}, "
                f"but instead {response.status_code} was received.\nResponse:\n{response.json()}",
            )
            response = response.json()
            self.assertEqual(len(response["errors"]), 1)
            self.assertEqual(response["meta"]["data_returned"], 0)

            error = response["errors"][0]
            self.assertEqual(str(expected_status), error["status"])
            self.assertEqual(expected_title, error["title"])

            if expected_detail is None:
                expected_detail = "Error trying to process rule "
                self.assertTrue(error["detail"].startswith(expected_detail))
            else:
                self.assertEqual(expected_detail, error["detail"])

        except Exception as exc:
            print("Request attempted:")
            print(f"{self.client.base_url}{request}")
            raise exc
