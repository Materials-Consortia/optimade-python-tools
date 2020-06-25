import os
import re
import sys
from typing import Tuple
from pathlib import Path
import json

from invoke import task

from jsondiff import diff


TOP_DIR = Path(__file__).parent.resolve()


def update_file(filename: str, sub_line: Tuple[str, str], strip: str = None):
    """Utility function for tasks to read, update, and write files"""
    with open(filename, "r") as handle:
        lines = [
            re.sub(sub_line[0], sub_line[1], line.rstrip(strip)) for line in handle
        ]

    with open(filename, "w") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


@task
def generate_openapi(_):
    """Update OpenAPI schema in file 'local_openapi.json'"""
    from optimade.server.main import app

    if not TOP_DIR.joinpath("openapi").exists():
        os.mkdir(TOP_DIR.joinpath("openapi"))
    with open(TOP_DIR.joinpath("openapi/local_openapi.json"), "w") as f:
        json.dump(app.openapi(), f, indent=2)
        print("", file=f)  # Empty EOL


@task
def generate_index_openapi(_):
    """Update OpenAPI schema in file 'local_index_openapi.json'"""
    from optimade.server.main_index import app as app_index

    if not TOP_DIR.joinpath("openapi").exists():
        os.mkdir(TOP_DIR.joinpath("openapi"))
    with open(TOP_DIR.joinpath("openapi/local_index_openapi.json"), "w") as f:
        json.dump(app_index.openapi(), f, indent=2)
        print("", file=f)  # Empty EOL


@task(pre=[generate_openapi, generate_index_openapi])
def check_openapi_diff(_):
    """Checks the Generated OpenAPI spec against what is stored in the repo"""
    with open(TOP_DIR.joinpath("openapi/openapi.json")) as handle:
        openapi = json.load(handle)

    with open(TOP_DIR.joinpath("openapi/local_openapi.json")) as handle:
        local_openapi = json.load(handle)

    with open(TOP_DIR.joinpath("openapi/index_openapi.json")) as handle:
        index_openapi = json.load(handle)

    with open(TOP_DIR.joinpath("openapi/local_index_openapi.json")) as handle:
        local_index_openapi = json.load(handle)

    openapi_diff = diff(openapi, local_openapi)
    if openapi_diff != {}:
        print(
            "Error: Generated OpenAPI spec for test server did not match committed version.\n"
            "Run 'invoke update-openapijson' and re-commit.\n"
            f"Diff:\n{openapi_diff}"
        )
        sys.exit(1)

    openapi_index_diff = diff(index_openapi, local_index_openapi)
    if openapi_index_diff != {}:
        print(
            "Error: Generated OpenAPI spec for Index meta-database did not match committed version.\n"
            "Run 'invoke update-openapijson' and re-commit.\n"
            f"Diff:\n{openapi_index_diff}"
        )
        sys.exit(1)


@task(pre=[generate_openapi, generate_index_openapi])
def update_openapijson(c):
    """Updates the stored OpenAPI spec to what the server returns"""
    c.run(
        f"cp {TOP_DIR.joinpath('openapi/local_openapi.json')} {TOP_DIR.joinpath('openapi/openapi.json')}"
    )
    c.run(
        f"cp {TOP_DIR.joinpath('openapi/local_index_openapi.json')} {TOP_DIR.joinpath('openapi/index_openapi.json')}"
    )

    print("Updated OpenAPI JSON specifications")


@task(help={"ver": "OPTIMADE Python tools version to set"}, post=[update_openapijson])
def setver(_, ver=""):
    """Sets the OPTIMADE Python Tools Version"""

    match = re.fullmatch(r"v?([0-9]+\.[0-9]+\.[0-9]+)", ver)
    if not match or (match and len(match.groups()) != 1):
        print(
            "Error: Please specify version as 'Major.Minor.Patch' or 'vMajor.Minor.Patch'"
        )
        sys.exit(1)
    ver = match.group(1)

    update_file(
        TOP_DIR.joinpath("optimade/__init__.py"),
        (r'__version__ = ".*"', f'__version__ = "{ver}"'),
    )

    print("Bumped version to {}".format(ver))


@task(help={"version": "OPTIMADE API version to set"}, post=[update_openapijson])
def set_optimade_ver(_, ver=""):
    """ Sets the OPTIMADE API Version """
    if not ver:
        print("Error: Please specify --ver='Major.Minor.Patch(-rc|a|b.NUMBER)'")
        sys.exit(1)

    match = re.fullmatch(r"v?([0-9]+\.[0-9]+\.[0-9]+(-(rc|a|b)+\.[0-9]+)?)", ver)
    if not match or (match and len(match.groups()) != 3):
        print(
            "Error: ver MUST be expressed as 'Major.Minor.Patch(-rc|a|b.NUMBER)'. It may be prefixed by 'v'."
        )
        sys.exit(1)
    ver = match.group(1)

    update_file(
        TOP_DIR.joinpath("optimade/__init__.py"),
        ("__api_version__ = .+", f'__api_version__ = "{ver}"'),
    )

    for regex, version in (
        ("[0-9]+", ver.split(".")[0]),
        ("[0-9]+.[0-9]+", ".".join(ver.split(".")[:2])),
        ("[0-9]+.[0-9]+.[0-9]+", ver),
    ):
        update_file(
            TOP_DIR.joinpath("README.md"),
            (f"example/v{regex}", f"example/v{version}"),
            strip="\n",
        )

    update_file(
        TOP_DIR.joinpath("optimade-version.json"),
        (r'"message": "v.+",', f'"message": "v{ver}",'),
    )

    update_file(
        TOP_DIR.joinpath("INSTALL.md"),
        (r"/v[0-9]+(\.[0-9]+){2}(-(rc|a|b)+\.[0-9]+)?", f"/v{ver.split('.')[0]}"),
    )

    print(f"Bumped OPTIMADE API version to {ver}")


@task
def parse_spec_for_filters(_):
    """Parses specification to generate validator filters"""
    import requests

    filter_path = TOP_DIR.joinpath("optimade/validator/data/filters.txt")
    optional_filter_path = TOP_DIR.joinpath(
        "optimade/validator/data/optional_filters.txt"
    )

    specification_flines = (
        requests.get(
            "https://raw.githubusercontent.com/Materials-Consortia/OPTIMADE/develop/optimade.rst"
        )
        .content.decode("utf-8")
        .split("\n")
    )

    filters = []
    optional_filters = []
    optional_triggers = ("OPTIONAL",)
    for line in specification_flines:
        if ":filter:" in line:
            for _split in line.replace("filter=", "").split(":filter:")[1:]:
                _filter = _split.split("`")[1].strip()
                if any(trigger in line for trigger in optional_triggers):
                    optional_filters.append(_filter)
                else:
                    filters.append(_filter)

    with open(filter_path, "w") as handle:
        for _filter in filters:
            handle.write(_filter + "\n")

    with open(optional_filter_path, "w") as handle:
        for _filter in optional_filters:
            handle.write(_filter + "\n")


@task
def get_markdown_spec(ctx):
    print("Attempting to run pandoc...")
    ctx.run(
        "pandoc "
        "-f rst -t markdown_strict "
        "--wrap=preserve --columns=50000 "
        "https://raw.githubusercontent.com/Materials-Consortia/OPTIMADE/develop/optimade.rst "
        "> optimade.md"
    )
