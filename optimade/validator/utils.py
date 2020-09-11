""" This class contains patched versions of the OPTIMADE models as
a workaround for the response field workaround of allowing responses
to contain bare dictionaries. These allow the validator to print detailed
validation responses.

"""

import time
import sys
import urllib.parse
import traceback as tb
from typing import List, Optional, Dict, Any

try:
    import simplejson as json
except ImportError:
    import json

import requests
from pydantic import Field, ValidationError

from optimade.models.optimade_json import Success
from optimade.models import (
    ResponseMeta,
    EntryResource,
    LinksResource,
    ReferenceResource,
    StructureResource,
)


class ResponseError(Exception):
    """ This exception should be raised for a manual hardcoded test failure. """


class InternalError(Exception):
    """This exception should be raised when validation throws an unexpected error.
    These should be counted separately from `ResponseError`'s and `ValidationError`'s.

    """


def print_warning(string, **kwargs):
    """ Print but angry. """
    print(f"\033[93m{string}\033[0m", **kwargs)


def print_notify(string, **kwargs):
    """ Print but louder. """
    print(f"\033[94m\033[1m{string}\033[0m", **kwargs)


def print_failure(string, **kwargs):
    """ Print but sad. """
    print(f"\033[91m\033[1m{string}\033[0m", **kwargs)


def print_success(string, **kwargs):
    """ Print but happy. """
    print(f"\033[92m\033[1m{string}\033[0m", **kwargs)


class Client:  # pragma: no cover
    def __init__(self, base_url: str, max_retries=5):
        """Initialises the Client with the given `base_url` without testing
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
        """Makes the given request, with a number of retries if being rate limited. The
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
    """Wrapper for test case functions, which pretty_prints any errors
    depending on verbosity level and returns only the response to the caller.

    Parameters:
        test_fn (callable): function that returns a response to pass to caller,
            and a message to print upon success. Should raise `ResponseError`,
            `ValidationError` or `ManualValidationError` if the test case has failed.
            The function can return `None` to indicate that the test was
            not appropriate and should be ignored.

    Keyword arguments:
        request (str): the request made by the wrapped function.
        optional (bool): whether or not to treat the test as optional.
        multistage (bool): if True, no output will be printed for this test,
            and it will not increment the success counter. Errors will be
            handled in the normal way. This can be used to avoid flooding
            the output for mutli-stage tests.

    """
    from functools import wraps

    @wraps(test_fn)
    def wrapper(
        validator, *args, request=None, optional=False, multistage=False, **kwargs
    ):
        try:
            try:
                if optional and not validator.run_optional_tests:
                    result = None
                    msg = "skipping optional"
                    return result

                out = test_fn(validator, *args, **kwargs)
                if out is not None:
                    result, msg = out
                else:
                    result = None
                    msg = ""
                    # if the test returned None, then we just ignore it
                    return result

            except json.JSONDecodeError as exc:
                msg = (
                    "Critical: unable to parse server response as JSON. "
                    f"Error: {exc.__class__.__name__}: {exc}"
                )
                raise exc
            except (ResponseError, ValidationError) as exc:
                msg = f"{exc.__class__.__name__}: {exc}"
                raise exc
            except Exception as exc:
                msg = f"{exc.__class__.__name__}: {exc}"
                raise InternalError(msg)

        except Exception as exc:
            result = exc
            traceback = tb.format_exc()

        finally:
            display_request = None
            try:
                display_request = validator.client.last_request
            except AttributeError:
                pass
            if display_request is None:
                display_request = validator.base_url
                if request is not None:
                    display_request += "/" + request

            request = display_request

            if not isinstance(result, Exception):
                if not multistage:
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
                    elif optional:
                        print(".", end="", flush=True)
                    else:
                        print_success(".", end="", flush=True)
            else:
                internal_error = False
                request = request.replace("\n", "")
                message = msg.split("\n")
                if validator.verbosity > 1:
                    # ValidationErrors from pydantic already include very detailed errors
                    # that get duplicated in the traceback
                    if not isinstance(result, ValidationError):
                        message += traceback.split("\n")

                if isinstance(result, InternalError):
                    internal_error = True
                    validator.internal_failure_count += 1
                    summary = f"!: {request} - {test_fn.__name__} - failed with internal error"
                    validator.internal_failure_messages.append((summary, message))
                else:
                    summary = f"✖: {request} - {test_fn.__name__} - failed with error"
                    if not optional:
                        validator.failure_count += 1
                        validator.failure_messages.append((summary, message))
                    else:
                        validator.optional_failure_count += 1
                        validator.optional_failure_messages.append((summary, message))

                if validator.verbosity > 0:
                    if internal_error:
                        print_notify(summary)
                        for line in message:
                            print_warning(f"\t{line}")
                    elif optional:
                        print(summary)
                        for line in message:
                            print(f"\t{line}")
                    else:
                        print_failure(summary)
                        for line in message:
                            print_warning(f"\t{line}")
                else:
                    if internal_error:
                        print_notify("!", end="", flush=True)
                    elif optional:
                        print("✖", end="", flush=True)
                    else:
                        print_failure("✖", end="", flush=True)

                # set failure result to None as this is expected by other functions
                result = None

                if validator.fail_fast and not optional:
                    validator.print_summary()
                    raise SystemExit

            # Reset the client request so that it can be properly
            # displayed if the next request fails
            validator.client.last_request = None

            return result

    return wrapper


class ValidatorLinksResponse(Success):
    meta: ResponseMeta = Field(...)
    data: List[LinksResource] = Field(...)


class ValidatorEntryResponseOne(Success):
    meta: ResponseMeta = Field(...)
    data: EntryResource = Field(...)
    included: Optional[List[Dict[str, Any]]] = Field(None)


class ValidatorEntryResponseMany(Success):
    meta: ResponseMeta = Field(...)
    data: List[EntryResource] = Field(...)
    included: Optional[List[Dict[str, Any]]] = Field(None)


class ValidatorReferenceResponseOne(ValidatorEntryResponseOne):
    data: ReferenceResource = Field(...)


class ValidatorReferenceResponseMany(ValidatorEntryResponseMany):
    data: List[ReferenceResource] = Field(...)


class ValidatorStructureResponseOne(ValidatorEntryResponseOne):
    data: StructureResource = Field(...)


class ValidatorStructureResponseMany(ValidatorEntryResponseMany):
    data: List[StructureResource] = Field(...)
