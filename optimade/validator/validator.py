""" This module contains a validator class that can be pointed
at an OPTIMADE implementation and validated against the pydantic
models in this package.

"""
# pylint: disable=import-outside-toplevel

import time
import requests
import sys
import logging
import urllib.parse

try:
    import simplejson as json
except ImportError:
    import json

from typing import Union

from pydantic import ValidationError
from fastapi.testclient import TestClient

from optimade.models import InfoResponse, EntryInfoResponse, IndexInfoResponse

from .data import MANDATORY_FILTER_EXAMPLES, OPTIONAL_FILTER_EXAMPLES
from .validator_model_patches import (
    ValidatorLinksResponse,
    ValidatorEntryResponseOne,
    ValidatorEntryResponseMany,
    ValidatorReferenceResponseOne,
    ValidatorReferenceResponseMany,
    ValidatorStructureResponseOne,
    ValidatorStructureResponseMany,
)


BASE_INFO_ENDPOINT = "info"
LINKS_ENDPOINT = "links"
REQUIRED_ENTRY_ENDPOINTS = ["references", "structures"]

ENDPOINT_MANDATORY_QUERIES = {
    "structures": MANDATORY_FILTER_EXAMPLES,
    "references": [],
}

ENDPOINT_OPTIONAL_QUERIES = {
    "structures": OPTIONAL_FILTER_EXAMPLES,
    "references": [],
}

RESPONSE_CLASSES = {
    "references": ValidatorReferenceResponseMany,
    "references/": ValidatorReferenceResponseOne,
    "structures": ValidatorStructureResponseMany,
    "structures/": ValidatorStructureResponseOne,
    "info": InfoResponse,
    "links": ValidatorLinksResponse,
}
RESPONSE_CLASSES.update(
    {f"info/{entry}": EntryInfoResponse for entry in REQUIRED_ENTRY_ENDPOINTS}
)

REQUIRED_ENTRY_ENDPOINTS_INDEX = []
RESPONSE_CLASSES_INDEX = {"info": IndexInfoResponse, "links": ValidatorLinksResponse}


def print_warning(string, **kwargs):
    """ Print but angry. """
    print(f"\033[93m{string}\033[0m", **kwargs)


def print_failure(string, **kwargs):
    """ Print but sad. """
    print(f"\033[91m\033[4m{string}\033[0m", **kwargs)


def print_success(string, **kwargs):
    """ Print but happy. """
    print(f"\033[92m\033[1m{string}\033[0m", **kwargs)


class ResponseError(Exception):
    """ This exception should be raised for a manual hardcoded test failure. """


class Client:  # pragma: no cover
    def __init__(self, base_url: str, max_retries=5):
        """ Initialises the Client with the given `base_url` without testing
        if it is valid.

        Parameters:
            base_url (str): the base URL of the optimade implementation, including
            request protocol (e.g. `'http://'`) and API version number if necessary.
            Examples:
                - `'http://example.org/optimade/v1'`,
                - `'www.crystallography.net/cod-test/optimade/v0.10.0/'`
            Note: A maximum of one slash ("/") is allowed as the last character.

        """
        self.base_url = base_url
        self.last_request = None
        self.response = None
        self.max_retries = max_retries

    def get(self, request: str):
        """ Makes the given request, with a number of retries if being rate limited. The
        request will be prepended with the `base_url` unless the request appears to be an
        absolute URL (i.e. starts with `http://` or `https://`).

        Parameters:
            request (str): the request to make against the base URL of this client.

        Returns:
            response (requests.models.Response): the response from the server.

        Raises:
            SystemExit: if there is no response from the server, or if the URL is invalid.
            ResponseError: if the server does not respond with a non-429 status code within
                the `MAX_RETRIES` attempts.

        """
        if urllib.parse.urlparse(request, allow_fragments=True).scheme:
            self.last_request = request
        else:
            if request and not request.startswith("/"):
                request = f"/{request}"
            self.last_request = f"{self.base_url}{request}"

        status_code = None
        retries = 0
        # probably a smarter way to do this with requests, but their documentation 404's...
        while retries < self.max_retries:
            retries += 1
            try:
                self.response = requests.get(self.last_request)
            except requests.exceptions.ConnectionError:
                sys.exit(f"No response from server at {self.last_request}")
            except requests.exceptions.MissingSchema:
                sys.exit(
                    f"Unable to make request on {self.last_request}, did you mean http://{self.last_request}?"
                )
            status_code = self.response.status_code
            if status_code != 429:
                break

            print("Hit rate limit, sleeping for 1 s...")
            time.sleep(1)

        else:
            raise ResponseError("Hit max (manual) retries on request.")

        return self.response


def test_case(test_fn):
    """ Wrapper for test case functions, which pretty_prints any errors
    depending on verbosity level and returns only the response to the caller.

    Parameters:
        test_fn (callable): function that returns a response to pass to caller,
            and a message to print upon success. Should raise `ResponseError`,
            `ValidationError` or `ManualValidationError` if the test case has failed.

    Keyword arguments:
        optional (bool): whether or not to treat the test as optional.

    """
    from functools import wraps

    @wraps(test_fn)
    def wrapper(validator, *args, optional=False, **kwargs):
        try:
            result, msg = test_fn(validator, *args, **kwargs)
        except json.JSONDecodeError as exc:
            result = None
            msg = (
                "Critical: unable to parse server response as JSON. "
                f"Error: {type(exc).__name__}: {exc}"
            )
        except (ResponseError, ValidationError) as exc:
            result = None
            msg = f"{type(exc).__name__}: {exc}"

        try:
            request = validator.client.last_request
        except AttributeError:
            request = validator.base_url

        if result is not None:
            if not optional:
                validator.success_count += 1
            else:
                validator.optional_success_count += 1
            message = f"✔: {request} - {msg}"
            if validator.verbosity > 0:
                if optional:
                    print(message)
                else:
                    print_success(message)
            else:
                if optional:
                    print(".", end="", flush=True)
                else:
                    print_success(".", end="", flush=True)
        else:
            if not optional:
                validator.failure_count += 1
            else:
                validator.optional_failure_count += 1
            request = request.replace("\n", "")
            message = f"{msg}".split("\n")
            summary = f"✖: {request} - {test_fn.__name__} - failed with error"
            validator.failure_messages.append((summary, message))
            if validator.verbosity > 0:
                if optional:
                    print(summary)
                    for line in message:
                        print(f"\t{line}")
                else:
                    print_failure(summary)
                    for line in message:
                        print_warning(f"\t{line}")
            else:
                if optional:
                    print("✖", end="", flush=True)
                else:
                    print_failure("✖", end="", flush=True)

        return result

    return wrapper


class ImplementationValidator:
    """ Class to call test functions on a particular OPTIMADE
    implementation.

    Uses the pydantic models in `optimade.models` to validate the
    response from the server and crawl through the available endpoints.

    Drawbacks:
        - only works for current version of the specification as defined
        by `optimade.models`.

    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        client: Union[Client, TestClient] = None,
        base_url: str = None,
        verbosity: int = 0,
        page_limit: int = 5,
        max_retries: int = 5,
        as_type: str = None,
        index: bool = False,
    ):
        """ Set up the tests to run, based on constants in this module
        for required endpoints.

        """

        self.verbosity = verbosity
        self.max_retries = max_retries
        self.page_limit = page_limit
        self.index = index

        if as_type is None:
            self.as_type_cls = None
        elif self.index:
            if as_type not in RESPONSE_CLASSES_INDEX.keys():
                raise RuntimeError(
                    f"Provided as_type='{as_type}' not allowed for an Index meta-database."
                )
            self.as_type_cls = RESPONSE_CLASSES_INDEX[as_type]
        elif as_type in ("structure", "reference"):
            self.as_type_cls = RESPONSE_CLASSES[f"{as_type}s/"]
        else:
            self.as_type_cls = RESPONSE_CLASSES[as_type]

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

        self.test_id_by_type = {}
        self._setup_log()
        self.expected_entry_endpoints = (
            REQUIRED_ENTRY_ENDPOINTS_INDEX if self.index else REQUIRED_ENTRY_ENDPOINTS
        )
        self.test_entry_endpoints = set(self.expected_entry_endpoints)
        self.endpoint_mandatory_queries = (
            {} if self.index else ENDPOINT_MANDATORY_QUERIES
        )

        self.endpoint_optional_queries = {} if self.index else ENDPOINT_OPTIONAL_QUERIES

        self.response_classes = (
            RESPONSE_CLASSES_INDEX if self.index else RESPONSE_CLASSES
        )

        # some simple checks on base_url
        base_url = urllib.parse.urlparse(self.base_url)
        # only allow filters/endpoints if we are working in "as_type" mode
        if self.as_type_cls is None and (
            base_url.query
            or any(endp in base_url.path for endp in self.expected_entry_endpoints)
        ):
            raise SystemExit(
                "Base URL not appropriate: should not contain an endpoint or filter."
            )

        # if valid is True on exit, script returns 0 to shell
        # if valid is False on exit, script returns 1 to shell
        # if valid is None on exit, script returns 2 to shell, indicating an internal failure
        self.valid = None

        self.success_count = 0
        self.failure_count = 0
        self.optional_success_count = 0
        self.optional_failure_count = 0
        self.failure_messages = []

    def _setup_log(self):
        """ Define stdout log based on given verbosity. """
        self._log = logging.getLogger(__name__)
        self._log.handlers = []
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s | %(levelname)8s: %(message)s")
        )
        self._log.addHandler(stdout_handler)
        if self.verbosity == 0:
            self._log.setLevel(logging.CRITICAL)
        elif self.verbosity == 1:
            self._log.setLevel(logging.INFO)
        else:
            self._log.setLevel(logging.DEBUG)

    def main(self):
        """ Run all the test cases of the implementation, or the single type test. """

        # if single type has been set, only run that test
        if self.as_type_cls is not None:
            self._log.info(
                "Validating response of %s with model %s",
                self.base_url,
                self.as_type_cls,
            )
            self.test_as_type()
            self.valid = not bool(self.failure_count)
            return

        # test entire implementation
        print(f"Testing entire implementation at {self.base_url}...")
        print("\nMandatory tests:")
        self._log.debug("Testing base info endpoint of %s", BASE_INFO_ENDPOINT)
        base_info = self.test_info_or_links_endpoints(BASE_INFO_ENDPOINT)
        self.get_available_endpoints(base_info)

        for endp in self.test_entry_endpoints:
            entry_info_endpoint = f"{BASE_INFO_ENDPOINT}/{endp}"
            self._log.debug("Testing expected info endpoint %s", entry_info_endpoint)
            self.test_info_or_links_endpoints(entry_info_endpoint)

        for endp in self.test_entry_endpoints:
            self._log.debug("Testing multiple entry endpoint of %s", endp)
            self.test_multi_entry_endpoint(f"{endp}?page_limit={self.page_limit}")

        for endp in self.test_entry_endpoints:
            self._log.debug("Testing single entry request of type %s", endp)
            self.test_single_entry_endpoint(endp)

        for endp in self.endpoint_mandatory_queries:
            # skip empty endpoint query lists
            if self.endpoint_mandatory_queries[endp]:
                self._log.debug("Testing mandatory query syntax on endpoint %s", endp)
                self.test_query_syntax(endp, self.endpoint_mandatory_queries[endp])

        self._log.debug("Testing %s endpoint", LINKS_ENDPOINT)
        self.test_info_or_links_endpoints(LINKS_ENDPOINT)

        self.valid = not bool(self.failure_count)

        print("\nOptional tests:")
        for endp in self.endpoint_optional_queries:
            # skip empty endpoint query lists
            if self.endpoint_mandatory_queries[endp]:
                self._log.debug("Testing optional query syntax on endpoint %s", endp)
                self.test_query_syntax(
                    endp, self.endpoint_optional_queries[endp], optional=True
                )

        if not self.valid:
            print("\n\nFAILURES\n")
            for message in self.failure_messages:
                print_failure(message[0])
                for line in message[1]:
                    print_warning("\t" + line)

        final_message = f"\n\nPassed {self.success_count} out of {self.success_count + self.failure_count} tests."
        if not self.valid:
            print_failure(final_message)
        else:
            print_success(final_message)

        print(
            f"Additionally passed {self.optional_success_count} out of "
            f"{self.optional_success_count + self.optional_failure_count} optional tests."
        )

    def test_info_or_links_endpoints(self, request_str):
        """ Runs the test cases for the info endpoints. """
        response = self.get_endpoint(request_str)
        if response:
            deserialized = self.deserialize_response(
                response, self.response_classes[request_str]
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
        if _type in self.test_id_by_type:
            test_id = self.test_id_by_type[_type]
            response = self.get_endpoint(f"{_type}/{test_id}")
            if response:
                self.deserialize_response(response, response_cls)

    def test_multi_entry_endpoint(self, request_str):
        """ Runs the test cases for the multi entry endpoints. """
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
        deserialized = self.deserialize_response(response, response_cls)
        self.test_page_limit(response)
        self.get_single_id_from_multi_endpoint(deserialized)

    def test_as_type(self):
        response = self.get_endpoint("")
        if response:
            self._log.debug("Deserialzing response as type %s", self.as_type_cls)
            self.deserialize_response(response, self.as_type_cls)

    @test_case
    def test_page_limit(self, response, check_next_link=True):
        """ Test that a multi-entry endpoint obeys the page limit.

        Parameters:
            response (requests.Response): the response to test for page limit
                compliance.

        Keyword arguments:
            check_next (bool): whether or not to recursively follow and test any
                pagination links provided under `links->next`.

        Raises:
            ResponseError: if test fails in a predictable way.

        Returns:
            bool, str: True if the test was successful, with a string describing
                the success.

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

        if more_data_available:
            try:
                next_link = response["links"]["next"]
            except KeyError:
                raise ResponseError(
                    "Endpoint suggested more data was available but provided no links->next link."
                )

            next_response = self.get_endpoint(next_link)
            self.test_page_limit(next_response, check_next_link=False)

        return (
            True,
            f"Endpoint obeyed page limit of {self.page_limit} by returning {num_entries} entries.",
        )

    @test_case
    def get_single_id_from_multi_endpoint(self, deserialized):
        """ Scrape an ID from the multi-entry endpoint to use as query
        for single entry endpoint.

        """
        if deserialized and deserialized.data:
            self.test_id_by_type[deserialized.data[0].type] = deserialized.data[0].id
            self._log.debug(
                "Set type %s test ID to %s",
                deserialized.data[0].type,
                deserialized.data[0].id,
            )
        else:
            raise ResponseError("No entries found under endpoint to scrape ID from.")
        return (
            self.test_id_by_type[deserialized.data[0].type],
            f"successfully scraped test ID from {deserialized.data[0].type} endpoint",
        )

    @test_case
    def deserialize_response(self, response: requests.models.Response, response_cls):
        """ Try to create the appropriate pydantic model from the response. """
        if not response:
            raise ResponseError("Request failed")
        return (
            response_cls(**response.json()),
            "deserialized correctly as object of type {}".format(response_cls),
        )

    @test_case
    def get_available_endpoints(self, base_info):
        """ Try to get `entry_types_by_format` even if base info response could not be validated. """
        for _ in [0]:
            available_json_entry_endpoints = []
            try:
                available_json_entry_endpoints = base_info.data.attributes.entry_types_by_format.get(
                    "json"
                )
                break
            except Exception:
                self._log.warning(
                    "Info endpoint failed serialization, trying to manually extract entry_types_by_format."
                )

            if not base_info.json():
                raise ResponseError(
                    "Unable to get entry types from base info endpoint. "
                    f"This may most likely be attributed to a wrong request to the '{BASE_INFO_ENDPOINT}' endpoint."
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

        self.test_entry_endpoints |= set(available_json_entry_endpoints)
        for non_entry_endpoint in ("info", "links"):
            if non_entry_endpoint in self.test_entry_endpoints:
                raise ResponseError(
                    f'Illegal entry "{non_entry_endpoint}" was found in entry_types_by_format"'
                )
        return (
            available_json_entry_endpoints,
            "successfully found available entry types in baseinfo",
        )

    @test_case
    def get_endpoint(self, request_str, optional=False):
        """ Gets the response from the endpoint specified by `request_str`. """

        request_str = request_str.replace("\n", "")
        response = self.client.get(request_str)

        if response.status_code != 200:
            error_titles = [
                error.get("title", "") for error in response.json().get("errors", [])
            ]
            error_details = [
                error.get("detail", "") for error in response.json().get("errors", [])
            ]
            message = f"Request to '{request_str}' returned HTTP code {response.status_code}. Errors:\n"
            for error_title, error_detail in zip(error_titles, error_details):
                message += f"{error_title}: {error_details}"
            raise ResponseError(message)

        return response, "request successful."

    def test_query_syntax(self, endpoint, endpoint_queries, optional=False):
        """ Execute a list of valid queries agains the endpoint and assert
        that no errors are raised.

        Parameters:
            endpoint (str): the endpoint to query (e.g. "structures").
            endpoint_queries (list): the list of valid mandatory queries
                for that endpoint, where the queries do not include the
                "?filter=" prefix, e.g. ['elements HAS "Na"'].

        Keyword arguments:
            optional (bool): treat the success of the queries as optional.

        """

        valid_queries = [f"{endpoint}?filter={query}" for query in endpoint_queries]
        for query in valid_queries:
            self.get_endpoint(query, optional=optional)
