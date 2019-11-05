from .validator import ImplementationValidator

__all__ = ["ImplementationValidator", "validate"]


def validate():
    import argparse
    import sys
    import traceback

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "base_url",
        nargs="?",
        default="http://localhost:5000",
        help=(
            "The base URL of the OPTiMaDe implementation to point at, "
            "e.g. 'http://example.com/optimade' or 'http://localhost:5000"
        ),
    )
    parser.add_argument(
        "--verbosity", "-v", type=int, default=0, help="The verbosity of the output"
    )
    args = vars(parser.parse_args())

    validator = ImplementationValidator(
        base_url=args["base_url"], verbosity=args["verbosity"]
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
