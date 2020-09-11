""" This module contains a validator class that can be pointed
at an OPTIMADE implementation and validated against the pydantic
models in this package.

"""
# pylint: disable=import-outside-toplevel

import sys
import logging
import random
import urllib.parse
from typing import Union, Tuple, Any

try:
    import simplejson as json
except ImportError:
    import json

import requests
from fastapi.testclient import TestClient

from optimade.models import DataType, EntryInfoResponse
from optimade.validator.utils import (
    Client,
    test_case,
    print_failure,
    print_notify,
    print_success,
    print_warning,
    ResponseError,
    ValidatorEntryResponseOne,
    ValidatorEntryResponseMany,
)

from optimade.validator.config import VALIDATOR_CONFIG as CONF

VERSIONS_REGEXP = r"/v[0-9]+(\.[0-9]+){,2}"


class ImplementationValidator:
    """
    Class to call test functions on a particular OPTIMADE implementation.

    Uses the pydantic models in `optimade.models` to validate the
    response from the server and crawl through the available endpoints.

    Caution:
        Only works for current version of the specification as defined
        by `optimade.models`.

    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        client: Union[Client, TestClient] = None,
        base_url: str = None,
        verbosity: int = 0,
        page_limit: int = 5,
        max_retries: int = 5,
        run_optional_tests: bool = True,
        fail_fast: bool = False,
        as_type: str = None,
        index: bool = False,
    ):
        """Set up the tests to run, based on constants in this module
        for required endpoints.

        """

        self.verbosity = verbosity
        self.max_retries = max_retries
        self.page_limit = page_limit
        self.index = index
        self.run_optional_tests = run_optional_tests
        self.fail_fast = fail_fast

        if as_type is None:
            self.as_type_cls = None
        elif self.index:
            if as_type not in CONF.response_classes_index.keys():
                raise RuntimeError(
                    f"Provided as_type='{as_type}' not allowed for an Index meta-database."
                )
            self.as_type_cls = CONF.response_classes_index[as_type]
        elif as_type in ("structure", "reference"):
            self.as_type_cls = CONF.response_classes[f"{as_type}s/"]
        else:
            self.as_type_cls = CONF.response_classes[as_type]

        if client is None and base_url is None:
            raise RuntimeError(
                "Need at least a URL or a client to initialize validator."
            )
        if base_url and client:
            raise RuntimeError("Please specify at most one of base_url or client.")
        if client:
            self.client = client
            self.base_url = self.client.base_url
        else:
            while base_url.endswith("/"):
                base_url = base_url[:-1]
            self.base_url = base_url
            self.client = Client(base_url, max_retries=self.max_retries)

        self._setup_log()

        self.response_classes = (
            CONF.response_classes_index if self.index else CONF.response_classes
        )

        # some simple checks on base_url
        self.base_url_parsed = urllib.parse.urlparse(self.base_url)
        # only allow filters/endpoints if we are working in "as_type" mode
        if self.as_type_cls is None and self.base_url_parsed.query:
            raise SystemExit("Base URL not appropriate: should not contain a filter.")

        # if valid is True on exit, script returns 0 to shell
        # if valid is False on exit, script returns 1 to shell
        # if valid is None on exit, script returns 2 to shell, indicating an internal failure
        self.valid = None

        self._test_id_by_type = {}
        self._entry_info_by_type = {}

        self.success_count = 0
        self.failure_count = 0
        self.internal_failure_count = 0
        self.optional_success_count = 0
        self.optional_failure_count = 0
        self.failure_messages = []
        self.internal_failure_messages = []
        self.optional_failure_messages = []

    def _setup_log(self):
        """ Define stdout log based on given verbosity. """
        self._log = logging.getLogger("optimade").getChild("validator")
        self._log.handlers = []
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s | %(levelname)8s: %(message)s")
        )
        self._log.addHandler(stdout_handler)
        if self.verbosity == 0:
            self._log.setLevel(logging.WARNING)
        elif self.verbosity == 1:
            self._log.setLevel(logging.INFO)
        else:
            self._log.setLevel(logging.DEBUG)

    def validate_implementation(self):
        """ Run all the test cases of the implementation, or the single type test. """

        # If a single "as type" has been set, only run that test
        if self.as_type_cls is not None:
            self._log.debug(
                "Validating response of %s with model %s",
                self.base_url,
                self.as_type_cls,
            )
            self.test_as_type()
            self.valid = not bool(self.failure_count)
            return

        # Test entire implementation
        print(f"Testing entire implementation at {self.base_url}...")
        self._log.debug("Testing base info endpoint of %s", "info")

        # Save base info to construct new queries
        info_endp = CONF.info_endpoint
        base_info = self.test_info_or_links_endpoints(info_endp)
        if not base_info:
            raise RuntimeError("Unable to understand base info, cannot continue.")

        self.base_info = base_info.dict()
        self.provider_prefix = self.base_info["meta"].get("provider", {}).get("prefix")

        # Run some tests on the versions endpoint
        versions_endp = CONF.versions_endpoint
        self.test_versions_endpoint(versions_endp)
        self.test_bad_version_returns_553()

        self.available_json_endpoints = self.get_available_endpoints(base_info)
        # set the response class for all `/info/entry` endpoints
        for endp in self.available_json_endpoints:
            self.response_classes[f"{info_endp}/{endp}"] = EntryInfoResponse

        # Test that entry info endpoints deserialize correctly
        for endp in self.available_json_endpoints:
            entry_info_endpoint = f"{info_endp}/{endp}"
            self._log.debug("Testing expected info endpoint %s", entry_info_endpoint)
            entry_info = self.test_info_or_links_endpoints(entry_info_endpoint)
            if entry_info:
                self._entry_info_by_type[endp] = entry_info.dict()

        # Use the _entry_info_by_type to construct filters on the relevant endpoints
        for endp in self.available_json_endpoints:
            self.recurse_through_endpoint(endp)

        # Test that the results from multi-entry-endpoints obey e.g. page limits
        # and that all entries can be deserialized with the patched models
        #
        # These methods also set the test_ids for each type of entry, which are validated
        # in the next loop.
        for endp in self.available_json_endpoints:
            self._log.debug("Testing multiple entry endpoint of %s", endp)
            self.test_multi_entry_endpoint(f"{endp}?page_limit={self.page_limit}")

        # Test that the single IDs scraped earlier work with the single entry endpoint
        for endp in self.available_json_endpoints:
            self._log.debug("Testing single entry request of type %s", endp)
            self.test_single_entry_endpoint(endp)

        # Test that the links endpoint can be serialized correctly
        links_endp = CONF.links_endpoint
        self._log.debug("Testing %s endpoint", links_endp)
        self.test_info_or_links_endpoints(links_endp)

        self.valid = not (bool(self.failure_count) or bool(self.internal_failure_count))

        self.print_summary()

    def recurse_through_endpoint(self, endp):
        """For a given endpoint (`endp`), get the entry type
        and supported fields, testing that all mandatory fields
        are supported, then test queries on every property according
        to the reported type, with optionality decided by the
        specification-level support level for that field.

        """
        entry_info = self._entry_info_by_type.get(endp)
        _impl_properties = self.check_entry_info(entry_info, endp)

        chosen_entry = self.get_archetypical_entry(endp)

        if not entry_info:
            raise ResponseError(
                f"Unable to generate filters for endpoint {endp}: entry info not found."
            )

        for prop in _impl_properties:
            # check support level of property
            prop_type = _impl_properties[prop]["type"]
            sortable = _impl_properties[prop]["sortable"]
            optional = prop not in CONF.entry_properties[endp]["MUST"]

            if optional and not self.run_optional_tests:
                continue

            self.construct_queries_for_property(
                prop,
                prop_type,
                sortable,
                endp,
                chosen_entry,
                request=f"; testing queries for {endp}->{prop}",
                optional=optional,
            )

    def check_entry_info(self, entry_info, endp):
        """Checks that `entry_info` contains all the required properties,
        and returns the property list for the endpoint.

        """
        properties = entry_info["data"]["properties"]
        self.test_must_properties(
            properties, endp, request="; checking entry info for required properties"
        )

        return properties

    @test_case
    def test_must_properties(self, properties, endp):
        """Check that the entry info lists all properties with the "MUST"
        support level for this endpoint.

        """
        must_props = CONF.entry_properties[endp]["MUST"]
        must_props_supported = set(prop for prop in properties if prop in must_props)
        missing = must_props - must_props_supported
        if len(missing) != 0:
            raise ResponseError(
                f"Some 'MUST' properties were missing from info/{endp}: {missing}"
            )

        return True, "Found all required properties in entry info for endpoint {endp}"

    @test_case
    def get_archetypical_entry(self, endp):
        """Get a random entry from the first page of results for this
        endpoint.

        """
        response = self.get_endpoint(endp)
        data_returned = response.json()["meta"]["data_returned"]
        if data_returned < 1:
            raise ResponseError(f"No data returned from endpoint {endp}.")
        response = self.get_endpoint(
            f"{endp}?page_offset={random.randint(0, data_returned-1)}"
        )
        archetypical_entry = response.json()["data"][0]
        return (
            archetypical_entry,
            f"set archetypical entry for {endp} with ID {archetypical_entry['id']}.",
        )

    @test_case
    def construct_queries_for_property(
        self,
        prop,
        prop_type,
        sortable,
        endp,
        chosen_entry,
        provider=False,
    ):

        # Explicitly handle top level keys that do not have types in info
        if prop == "type":
            if chosen_entry["type"] == endp:
                return True, f"Successfully validatated {prop}"
            else:
                raise ResponseError(
                    f"Chosen entry of endpoint '/{endp}' had unexpected type '{chosen_entry['type']}'."
                )

        if prop == "id":
            prop_type = DataType.STRING

        if prop_type is None:
            raise ResponseError(
                f"Cannot validate queries on {prop} as field type was not reported in /info/{endp}"
            )

        # this is the case of a provider field
        if prop not in (
            CONF.entry_properties[endp]["MUST"]
            | CONF.entry_properties[endp]["SHOULD"]
            | CONF.entry_properties[endp]["OPTIONAL"]
        ):
            if self.provider_prefix is None:
                raise ResponseError(
                    f"Found unknown field {prop} and no provider prefix was provided in `/info`"
                )
            elif not prop.startswith(f"_{self.provider_prefix}"):
                raise ResponseError(
                    f'Found unknown field {prop} that did not start with provider prefix "_{self.provider_prefix}"'
                )
            else:
                return True, f"Found provider field {prop}, will not test queries."

        return self._construct_single_property_filters(
            prop, prop_type, sortable, endp, chosen_entry
        )

    @staticmethod
    def _format_test_value(test_value, prop_type, operator):
        """ Format the test value according to the type of the property. """

        if prop_type == DataType.LIST:
            if operator in ("HAS ALL", "HAS ANY"):
                _vals = sorted(set(test_value))
                if isinstance(test_value[0], str):
                    _vals = [f'"{val}"' for val in _vals]
                else:
                    _vals = [f"{val}" for val in _vals]
                _test_value = ",".join(_vals)
            else:
                if isinstance(test_value[0], str):
                    _test_value = f'"{test_value[0]}"'
                else:
                    _test_value = test_value[0]

        elif prop_type == DataType.STRING:
            _test_value = f'"{test_value}"'

        else:
            _test_value = test_value

        return _test_value

    def _construct_single_property_filters(
        self, prop, prop_type, sortable, endp, chosen_entry
    ):
        """This method constructs appropriate queries using all operators
        for a certain field and applies some tests:

        - inclusive operators return compatible entries, e.g. `>=` always returns
        at least the results of `=`.
        - exclusive operators never return contradictory entries, e.g.
        `nsites=1` never returns the same entries as `nsites!=1`), modulo
        pagination.

        """
        if prop == "id":
            test_value = chosen_entry["id"]
        else:
            test_value = chosen_entry["attributes"].get(prop, "missing")

        if test_value in ("missing", None):
            if prop in CONF.entry_properties[endp]["OPTIONAL"]:
                return None
            else:
                raise ResponseError(f"chosen entry had no value for '{prop}'")

        if prop_type == DataType.LIST:
            if not test_value or (
                isinstance(test_value[0], dict) or isinstance(test_value[0], list)
            ):
                self._log.warning(
                    f"Not testing queries on field {prop} of type {prop_type} with nested dictionary/list entries.",
                )
                return

        if prop_type in (DataType.DICTIONARY, DataType.TIMESTAMP):
            self._log.warning(
                f"Not testing queries on field {prop} of type {prop_type}."
            )
            return

        num_data_returned = {}

        inclusive_operators = CONF.inclusive_operators[prop_type]
        exclusive_operators = CONF.exclusive_operators[prop_type]

        for operator in inclusive_operators | exclusive_operators:
            # Need to pre-format list and string test values for the query
            _test_value = self._format_test_value(test_value, prop_type, operator)

            query = f"{prop} {operator} {_test_value}"
            response = self.get_endpoint(
                f"{endp}?filter={query}", multistage=True
            ).json()
            num_data_returned[operator] = response["meta"]["data_returned"]

            # Numeric and string comparisons must work both ways...
            if prop_type in (
                DataType.STRING,
                DataType.INTEGER,
                DataType.FLOAT,
                DataType.TIMESTAMP,
            ) and operator not in (
                "CONTAINS",
                "STARTS",
                "STARTS WITH",
                "ENDS",
                "ENDS WITH",
            ):
                reversed_operator = operator.replace("<", ">")
                if "<" in operator:
                    reversed_operator = operator.replace("<", ">")
                elif ">" in operator:
                    reversed_operator = operator.replace(">", "<")

                # Don't try to reverse string comparison as it is ill-defined
                if prop_type == DataType.STRING and any(
                    comp in operator for comp in ("<", ">")
                ):
                    continue

                reversed_query = f"{_test_value} {reversed_operator} {prop}"
                reversed_response = self.get_endpoint(
                    f"{endp}?filter={reversed_query}",
                    multistage=True,
                ).json()

                if (
                    reversed_response["meta"]["data_returned"]
                    != response["meta"]["data_returned"]
                ):
                    raise ResponseError(
                        f"Query {query} did not work both ways around: {reversed_query}, "
                        "returning different results each time."
                    )

            excluded = operator in exclusive_operators
            # if we have all results on this page, check that the blessed ID is in the response
            if response["meta"]["data_returned"] <= len(response["data"]):
                if excluded and (
                    chosen_entry["id"] in set(entry["id"] for entry in response["data"])
                ):
                    raise ResponseError(
                        f"Objects {excluded} were not necessarily excluded by {query}"
                    )

            # check that at least the archetypical structure was returned
            if not excluded:
                if num_data_returned[operator] < 1:
                    raise ResponseError(
                        f"Supposedly inclusive query '{query}' did not include original object ID {chosen_entry['id']} "
                        f"(with field '{prop} = {test_value}') potentially indicating a problem with filtering on this field."
                    )

        if prop in CONF.unique_properties:
            if num_data_returned["="] == 0:
                raise ResponseError(
                    f"Unable to filter field 'id' for equality, no data was returned for {query}."
                )
            if num_data_returned["="] > 1:
                raise ResponseError(
                    f"Filter for an individual 'id' returned {num_data_returned['=']} results, when only 1 was expected."
                )

        return True, f"{prop} passed filter tests"

    def print_summary(self):
        if self.failure_messages:
            print("\n\nFAILURES")
            print("========\n")
            for message in self.failure_messages:
                print_failure(message[0])
                for line in message[1]:
                    print_warning("\t" + line)

        if self.optional_failure_messages:
            print("\n\nOPTIONAL TEST FAILURES")
            print("======================\n")
            for message in self.optional_failure_messages:
                print_notify(message[0])
                for line in message[1]:
                    print_warning("\t" + line)

        if self.internal_failure_messages:
            print("\n\nINTERNAL FAILURES")
            print("=================\n")
            print(
                "There were internal valiator failures associated with this run.\n"
                "If this problem persists, please report it at:\n"
                "https://github.com/Materials-Consortia/optimade-python-tools/issues/new.\n"
            )

            for message in self.internal_failure_messages:
                print_warning(message[0])
                for line in message[1]:
                    print_warning("\t" + line)

        if self.valid or (not self.valid and not self.fail_fast):
            final_message = f"\n\nPassed {self.success_count} out of {self.success_count + self.failure_count + self.internal_failure_count} tests."
            if not self.valid:
                print_failure(final_message)
            else:
                print_success(final_message)

            if self.run_optional_tests and not self.fail_fast:
                print(
                    f"Additionally passed {self.optional_success_count} out of "
                    f"{self.optional_success_count + self.optional_failure_count} optional tests."
                )

    def test_info_or_links_endpoints(self, request_str):
        """ Runs the test cases for the info endpoints. """
        response = self.get_endpoint(request_str)
        if response:
            deserialized = self.deserialize_response(
                response,
                self.response_classes[request_str],
                request=request_str,
            )
            if not deserialized:
                return response
            return deserialized
        return False

    def test_single_entry_endpoint(self, request_str):
        """ Runs the test cases for the single entry endpoints. """
        _type = request_str.split("?")[0]
        response_cls_name = _type + "/"
        if response_cls_name in self.response_classes:
            response_cls = self.response_classes[response_cls_name]
        else:
            self._log.warning(
                "Deserializing single entry response %s with generic response rather than defined endpoint.",
                _type,
            )
            response_cls = ValidatorEntryResponseOne
        if _type in self._test_id_by_type:
            test_id = self._test_id_by_type[_type]
            response = self.get_endpoint(f"{_type}/{test_id}")
            if response:
                self.deserialize_response(response, response_cls, request=request_str)

    def test_multi_entry_endpoint(self, request_str):
        """Runs the test cases for the multi entry endpoints.

        TODO: deserialization is currently classed as an optional
        test until our models are robust to support levels.

        """
        response = self.get_endpoint(request_str)
        _type = request_str.split("?")[0]
        if _type in self.response_classes:
            response_cls = self.response_classes[_type]
        else:
            self._log.warning(
                "Deserializing multi entry response from %s with generic response rather than defined endpoint.",
                _type,
            )
            response_cls = ValidatorEntryResponseMany

        self.test_page_limit(response)

        deserialized = self.deserialize_response(
            response, response_cls, request=request_str, optional=True
        )

        if deserialized:
            self.get_single_id_from_multi_endpoint(deserialized, request=request_str)

    def test_as_type(self):
        response = self.get_endpoint("")
        if response:
            self._log.debug("Deserialzing response as type %s", self.as_type_cls)
            self.deserialize_response(response, self.as_type_cls)

    @test_case
    def test_page_limit(self, response, check_next_link: int = 5) -> (bool, str):
        """Test that a multi-entry endpoint obeys the page limit by
        following pagination links up to a depth of `check_next_link`.

        Parameters:
            response (requests.Response): the response to test for page limit
                compliance.

        Keyword arguments:
            check_next_link (int): maximum recursion depth for following
                pagination links.

        Raises:
            ResponseError: if test fails in a predictable way.

        Returns:
            True if the test was successful, with a string describing the success.

        """
        try:
            response = response.json()
        except (AttributeError, json.JSONDecodeError):
            raise ResponseError("Unable to test endpoint page limit.")

        try:
            num_entries = len(response["data"])
        except (KeyError, TypeError):
            raise ResponseError(
                "Response under `data` field was missing or had wrong type."
            )

        if num_entries > self.page_limit:
            raise ResponseError(
                f"Endpoint did not obey page limit: {num_entries} entries vs {self.page_limit} limit"
            )

        try:
            more_data_available = response["meta"]["more_data_available"]
        except KeyError:
            raise ResponseError("Field `meta->more_data_available` was missing.")

        if more_data_available and check_next_link:
            try:
                next_link = response["links"]["next"]
                if isinstance(next_link, dict):
                    next_link = next_link["href"]
            except KeyError:
                raise ResponseError(
                    "Endpoint suggested more data was available but provided no valid links->next link."
                )

            if not isinstance(next_link, str):
                raise ResponseError(
                    f"Unable to parse links->next {next_link!r} as a link."
                )

            self._log.debug("Following pagination link to %r.", next_link)
            next_response = self.get_endpoint(next_link)
            check_next_link = bool(check_next_link - 1)
            self.test_page_limit(
                next_response,
                check_next_link=check_next_link,
                multistage=check_next_link,
            )

        return (
            True,
            f"Endpoint obeyed page limit of {self.page_limit} by returning {num_entries} entries.",
        )

    @test_case
    def get_single_id_from_multi_endpoint(self, deserialized):
        """Scrape an ID from the multi-entry endpoint to use as query
        for single entry endpoint.

        """
        if deserialized and deserialized.data:
            self._test_id_by_type[deserialized.data[0].type] = deserialized.data[0].id
            self._log.debug(
                "Set type %s test ID to %s",
                deserialized.data[0].type,
                deserialized.data[0].id,
            )
        else:
            raise ResponseError(
                "No entries found under endpoint to scrape ID from. "
                "This may be caused by previous errors, if e.g. the endpoint failed deserialization."
            )
        return (
            self._test_id_by_type[deserialized.data[0].type],
            f"successfully scraped test ID from {deserialized.data[0].type} endpoint",
        )

    @test_case
    def deserialize_response(
        self, response: requests.models.Response, response_cls: Any, request: str = None
    ) -> Tuple[Any, str]:
        """Try to create the appropriate pydantic model from the response.

        Parameters:
            response: the response to try to deserialize.
            response_cls: the class to use for deserialization.

        Keyword arguments:
            request: optional string that will be displayed as the attempted
                request in the validator output.

        Raises:
            ResponseError: if the object fails deserialization, or if the
                request failed altogether.

        Returns:
            the deserialized object and a human-readable summary

        """
        if not response:
            raise ResponseError("Request failed")
        try:
            json_response = response.json()
        except json.JSONDecodeError:
            raise ResponseError(
                f"Unable to decode response as JSON. Response: {response}"
            )

        self._log.debug(
            f"Deserializing {json.dumps(json_response, indent=2)} as model {response_cls}"
        )

        return (
            response_cls(**json_response),
            "deserialized correctly as object of type {}".format(response_cls),
        )

    @test_case
    def get_available_endpoints(self, base_info):
        """ Try to get `entry_types_by_format` even if base info response could not be validated. """
        for _ in [0]:
            available_json_entry_endpoints = []
            try:
                available_json_entry_endpoints = (
                    base_info.data.attributes.entry_types_by_format.get("json")
                )
                break
            except Exception:
                self._log.warning(
                    "Info endpoint failed serialization, trying to manually extract entry_types_by_format."
                )

            if not base_info.json():
                raise ResponseError(
                    "Unable to get entry types from base info endpoint. "
                    "This may most likely be attributed to a wrong request to the info endpoint."
                )

            try:
                available_json_entry_endpoints = base_info.json()["data"]["attributes"][
                    "entry_types_by_format"
                ]["json"]
                break
            except (KeyError, TypeError):
                raise ResponseError(
                    "Unable to get entry_types_by_format from unserializable base info response {}.".format(
                        base_info
                    )
                )
        else:
            raise ResponseError(
                "Unable to find any JSON entry types in entry_types_by_format"
            )

        if self.index and available_json_entry_endpoints != []:
            raise ResponseError(
                "No entry endpoint are allowed for an Index meta-database"
            )

        for non_entry_endpoint in CONF.non_entry_endpoints:
            if non_entry_endpoint in available_json_entry_endpoints:
                raise ResponseError(
                    f'Illegal entry "{non_entry_endpoint}" was found in entry_types_by_format"'
                )
        return (
            available_json_entry_endpoints,
            "successfully found available entry types in baseinfo",
        )

    @test_case
    def get_endpoint(
        self, request_str: str, expected_status_code: int = 200, optional: bool = False
    ) -> Tuple[requests.Response, str]:
        """Gets the response from the endpoint specified by `request_str`.
        function is wrapped by the `test_case` decorator

        Parameters:
            request_str (str): the request to make to the client.

        Keyword arguments:
            expected_status_code (int): if the request responds with a different
                status code to this one, raise a ResponseError.
            optional (bool): whether the success of this test is optional.

        Returns:
            requests.Response: the response to the request (the `test_case` decorator
                swallows the success message returned in this function directly).

        """

        request_str = request_str.replace("\n", "")
        response = self.client.get(request_str)

        if response.status_code != expected_status_code:
            message = (
                f"Request to '{request_str}' returned HTTP code {response.status_code}."
            )
            message += "\nError(s):"
            for error in response.json().get("errors", []):
                message += f'\n  {error.get("title", "N/A")}: {error.get("detail", "N/A")} ({error.get("source", {}).get("pointer", "N/A")})'
            raise ResponseError(message)

        return response, f"received expected response: {response}."
