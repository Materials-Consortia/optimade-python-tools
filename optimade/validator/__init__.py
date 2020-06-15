""" This module contains the ImplementationValidator class and corresponding command line tools. """
# pylint: disable=import-outside-toplevel
from .validator import ImplementationValidator

__all__ = ["ImplementationValidator", "validate"]


def validate():
    import argparse
    import sys
    import os
    import traceback

    parser = argparse.ArgumentParser(
        prog="optimade_validator",
        description="""Tests OPTIMADE implementations for compliance with the optimade-python-tools models.

    - To test an entire implementation (at say example.com/optimade/v1) for all required/available endpoints:

        $ optimade_validator http://example.com/optimade/v1

    - To test a particular response of an implementation against a particular model:

        $ optimade_validator http://example.com/optimade/v1/structures/id=1234 --as_type structure

    - To test a particular response of an implementation against a particular model:

        $ optimade_validator http://example.com/optimade/v1/structures --as_type structures
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "base_url",
        nargs="?",
        default="http://localhost:5000/v0",
        help=(
            "The base URL of the OPTIMADE implementation to point at, "
            "e.g. 'http://example.com/optimade/v1' or 'http://localhost:5000/v1"
        ),
    )
    parser.add_argument(
        "--verbosity", "-v", type=int, default=0, help="The verbosity of the output"
    )
    parser.add_argument(
        "--as_type",
        "-a",
        type=str,
        help=(
            "Validate the request URL with the provided type, rather than scanning the entire implementation e.g. "
            "optimade_validator `http://example.com/optimade/v1/structures/0 --as_type structures`"
        ),
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help=(
            "Flag for whether the specified OPTIMADE implementation is an Index meta-database or not. [default=False]"
        ),
    )

    args = vars(parser.parse_args())

    if os.environ.get("OPTIMADE_VERBOSITY") is not None:
        try:
            args["verbosity"] = int(os.environ.get("OPTIMADE_VERBOSITY", 0))
        except (TypeError, ValueError):
            pass

    valid_types = [
        "info",
        "info/references",
        "info/structures",
        "links",
        "references",
        "reference",
        "structures",
        "structure",
    ]
    if args["as_type"] is not None and args["as_type"] not in valid_types:
        sys.exit(f"{args['as_type']} is not a valid type, must be one of {valid_types}")

    validator = ImplementationValidator(
        base_url=args["base_url"],
        verbosity=args["verbosity"],
        as_type=args["as_type"],
        index=args["index"],
    )

    try:
        validator.main()
    # catch and print internal exceptions, exiting with non-zero error code
    except Exception:
        traceback.print_exc()

    if validator.valid is None:
        sys.exit(2)
    elif not validator.valid:
        sys.exit(1)
