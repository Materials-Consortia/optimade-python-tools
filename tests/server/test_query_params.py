# pylint: disable=relative-beyond-top-level
import unittest

from optimade.server.config import CONFIG

from .utils import SetClient


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
