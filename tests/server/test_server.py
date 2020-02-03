# pylint: disable=no-member,wrong-import-position,import-outside-toplevel
import unittest
import abc

from starlette.testclient import TestClient

from optimade.validator import ImplementationValidator

from optimade.models import (
    ReferenceResponseMany,
    ReferenceResponseOne,
    ReferenceResource,
    StructureResponseMany,
    StructureResponseOne,
    EntryInfoResponse,
    InfoResponse,
    LinksResponse,
)

from optimade.server.main import app
from optimade.server.routers import info, links, references, structures

# We need to remove the /optimade prefixes in order to have the tests run correctly.
app.include_router(info.router)
app.include_router(links.router)
app.include_router(references.router)
app.include_router(structures.router)
# need to explicitly set base_url, as the default "http://testserver"
# does not validate as pydantic AnyUrl model
CLIENT = TestClient(app, base_url="http://example.org/optimade")


class EndpointTests(abc.ABC):
    """ Abstract base class for common tests between endpoints. """

    request_str = None
    response_cls = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client = CLIENT

        self.response = self.client.get(self.request_str)
        self.json_response = self.response.json()
        self.assertEqual(
            self.response.status_code,
            200,
            msg=f"Request failed: {self.response.json()}",
        )

    def test_meta_response(self):
        self.assertTrue("meta" in self.json_response)
        meta_required_keys = [
            "query",
            "api_version",
            "time_stamp",
            "data_returned",
            "more_data_available",
            "provider",
        ]
        meta_optional_keys = ["data_available", "implementation"]

        self.check_keys(meta_required_keys, self.json_response["meta"])
        self.check_keys(meta_optional_keys, self.json_response["meta"])

    def test_serialize_response(self):
        self.assertTrue(
            self.response_cls is not None, msg="Response class unset for this endpoint"
        )
        self.response_cls(**self.json_response)  # pylint: disable=not-callable

    def check_keys(self, keys, response_subset):
        for key in keys:
            self.assertTrue(
                key in response_subset,
                msg="{} missing from response {}".format(key, response_subset),
            )


class InfoEndpointTests(EndpointTests, unittest.TestCase):

    request_str = "/info"
    response_cls = InfoResponse

    def test_info_endpoint_attributes(self):
        self.assertTrue("data" in self.json_response)
        self.assertEqual(self.json_response["data"]["type"], "info")
        self.assertEqual(self.json_response["data"]["id"], "/")
        self.assertTrue("attributes" in self.json_response["data"])
        attributes = [
            "api_version",
            "available_api_versions",
            "formats",
            "entry_types_by_format",
            "available_endpoints",
        ]
        self.check_keys(attributes, self.json_response["data"]["attributes"])


class InfoStructuresEndpointTests(EndpointTests, unittest.TestCase):

    request_str = "/info/structures"
    response_cls = EntryInfoResponse

    def test_info_structures_endpoint_data(self):
        self.assertTrue("data" in self.json_response)
        data_keys = ["description", "properties", "formats", "output_fields_by_format"]
        self.check_keys(data_keys, self.json_response["data"])


class InfoReferencesEndpointTests(EndpointTests, unittest.TestCase):
    request_str = "/info/references"
    response_cls = EntryInfoResponse


class LinksEndpointTests(EndpointTests, unittest.TestCase):
    request_str = "/links"
    response_cls = LinksResponse


class ReferencesEndpointTests(EndpointTests, unittest.TestCase):
    request_str = "/references"
    response_cls = ReferenceResponseMany


class SingleReferenceEndpointTests(EndpointTests, unittest.TestCase):
    test_id = "dijkstra1968"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne


class StructuresEndpointTests(EndpointTests, unittest.TestCase):

    request_str = "/structures"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        self.assertTrue("meta" in self.json_response)
        self.assertEqual(self.json_response["meta"]["data_available"], 17)
        self.assertEqual(self.json_response["meta"]["more_data_available"], False)
        self.assertTrue("data" in self.json_response)
        self.assertEqual(
            len(self.json_response["data"]),
            self.json_response["meta"]["data_available"],
        )

    def test_get_next_responses(self):
        total_data = self.json_response["meta"]["data_available"]
        page_limit = 5

        response = self.client.get(self.request_str + f"?page_limit={page_limit}")
        json_response = response.json()
        self.assertEqual(
            self.response.status_code,
            200,
            msg=f"Request failed: {self.response.json()}",
        )

        cursor = json_response["data"].copy()
        self.assertTrue(json_response["meta"]["more_data_available"])
        more_data_available = True
        next_request = json_response["links"]["next"]

        while more_data_available:
            next_response = self.client.get(next_request).json()
            next_request = next_response["links"]["next"]
            cursor.extend(next_response["data"])
            more_data_available = next_response["meta"]["more_data_available"]
            if more_data_available:
                self.assertEqual(len(next_response["data"]), page_limit)
            else:
                self.assertEqual(len(next_response["data"]), total_data % page_limit)


class StructuresEndpointAliasedTests(EndpointTests, unittest.TestCase):

    request_str = "/structures/"
    response_cls = StructureResponseMany


class SingleStructureEndpointTests(EndpointTests, unittest.TestCase):

    test_id = "mpf_1"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        self.assertTrue("data" in self.json_response)
        self.assertEqual(self.json_response["data"]["id"], self.test_id)
        self.assertEqual(self.json_response["data"]["type"], "structures")
        self.assertTrue("attributes" in self.json_response["data"])
        self.assertTrue(
            "_exmpl__mp_chemsys" in self.json_response["data"]["attributes"]
        )


class MissingSingleStructureEndpointTests(EndpointTests, unittest.TestCase):

    test_id = "mpf_random_string_that_is_not_in_test_data"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        self.assertTrue("data" in self.json_response)
        self.assertTrue("meta" in self.json_response)
        self.assertEqual(self.json_response["data"], None)
        self.assertEqual(self.json_response["meta"]["data_returned"], 0)
        self.assertEqual(self.json_response["meta"]["more_data_available"], False)


class SingleStructureWithRelationshipsTests(EndpointTests, unittest.TestCase):

    test_id = "mpf_1"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        self.assertTrue("data" in self.json_response)
        self.assertEqual(self.json_response["data"]["id"], self.test_id)
        self.assertEqual(self.json_response["data"]["type"], "structures")
        self.assertTrue("attributes" in self.json_response["data"])
        self.assertTrue("relationships" in self.json_response["data"])
        self.assertDictEqual(
            self.json_response["data"]["relationships"],
            {"references": {"data": [{"type": "references", "id": "dijkstra1968"}]}},
        )
        self.assertTrue("included" in self.json_response)
        self.assertEqual(
            len(self.json_response["data"]["relationships"]["references"]["data"]),
            len(self.json_response["included"]),
        )

        ReferenceResource(**self.json_response["included"][0])


class MultiStructureWithSharedRelationshipsTests(EndpointTests, unittest.TestCase):

    request_str = f"/structures?filter=id=mpf_1 OR id=mpf_2"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        # mpf_1 and mpf_2 both contain the same reference relationship, so response should not duplicate it
        self.assertTrue("data" in self.json_response)
        self.assertEqual(len(self.json_response["data"]), 2)
        self.assertTrue("included" in self.json_response)
        self.assertEqual(len(self.json_response["included"]), 1)


class MultiStructureWithRelationshipsTests(EndpointTests, unittest.TestCase):

    request_str = f"/structures?filter=id=mpf_1 OR id=mpf_23"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        # mpf_4 contains no relationships, which shouldn't break anything
        self.assertTrue("data" in self.json_response)
        self.assertEqual(len(self.json_response["data"]), 2)
        self.assertTrue("included" in self.json_response)
        self.assertEqual(len(self.json_response["included"]), 1)


class MultiStructureWithOverlappingRelationshipsTests(EndpointTests, unittest.TestCase):

    request_str = f"/structures?filter=id=mpf_1 OR id=mpf_3"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        self.assertTrue("data" in self.json_response)
        self.assertEqual(len(self.json_response["data"]), 2)
        self.assertTrue("included" in self.json_response)
        self.assertEqual(len(self.json_response["included"]), 2)


class ServerTestWithValidator(unittest.TestCase):
    def test_with_validator(self):
        validator = ImplementationValidator(client=CLIENT)
        validator.main()
        self.assertTrue(validator.valid)


class SingleStructureEndpointEmptyTest(EndpointTests, unittest.TestCase):

    test_id = "non_existent_id"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        self.assertTrue("data" in self.json_response)
        self.assertEqual(self.json_response["data"], None)


class FilterTests(unittest.TestCase):

    client = CLIENT

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
        from optimade.server.config import CONFIG

        request = f"/structures?page_limit={CONFIG.page_limit_max + 1}"
        self._check_error_response(
            request,
            expected_status=403,
            expected_title="HTTPException",
            expected_detail=f"Max allowed page_limit is {CONFIG.page_limit_max}, you requested {CONFIG.page_limit_max + 1}",
        )

    def test_list_has_all(self):
        request = '/structures?filter=elements HAS ALL "Ba","F","H","Mn","O","Re","Si"'
        self._check_error_response(
            request, expected_status=501, expected_title="NotImplementedError"
        )
        # expected_ids = ["mpf_3819"]
        # self._check_response(request, expected_ids, len(expected_ids))

        request = '/structures?filter=elements HAS ALL "Re","Ti"'
        self._check_error_response(
            request, expected_status=501, expected_title="NotImplementedError"
        )
        # expected_ids = ["mpf_3819"]
        # self._check_response(request, expected_ids, len(expected_ids))

    def test_list_has_any(self):
        request = '/structures?filter=elements HAS ANY "Re","Ti"'
        self._check_error_response(
            request, expected_status=501, expected_title="NotImplementedError"
        )
        # expected_ids = ["mpf_3819"]
        # self._check_response(request, expected_ids, len(expected_ids))

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

    def test_list_has_only(self):
        request = '/structures?filter=elements HAS ONLY "Ac"'
        self._check_error_response(
            request, expected_status=501, expected_title="NotImplementedError"
        )
        # expected_ids = ["mpf_1"]
        # self._check_response(request, expected_ids, len(expected_ids))

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
