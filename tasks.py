import os
import re
import sys
from typing import Tuple
from pathlib import Path
import json

from invoke import task

from jsondiff import diff

try:
    from optimade import __api_version__
except ImportError:
    raise ImportError("optimade needs to be installed prior to running invoke tasks")


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


@task(help={"ver": "OPTIMADE Python tools version to set"})
def setver(_, ver=""):
    """Sets the OPTIMADE Python Tools Version"""

    match = re.match("v?([0-9]+.[0-9]+.[0-9]+)", ver)
    if len(match.groups()) != 1:
        print("Please specify version as 'Major.Minor.Patch' or 'vMajor.Minor.Patch'")
        sys.exit(1)

    new_ver = match.group(1)
    update_file(
        TOP_DIR.joinpath("setup.py"), ("version=([^,]+),", f'version="{new_ver}",')
    )

    print("Bumped version to {}".format(match.group(1)))


@task(help={"version": "OPTIMADE API version to set"})
def set_optimade_ver(_, ver=""):
    """ Sets the OPTIMADE API Version """
    if not ver:
        raise Exception("Please specify --ver='Major.Minor.Patch'")
    if not re.match("[0-9]+.[0-9]+.[0-9]+", ver):
        raise Exception("ver MUST be expressed as 'Major.Minor.Patch'")

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
        TOP_DIR.joinpath("README.md"), ("v[0-9]+", f"v{ver.split('.')[0]}"), strip="\n"
    )

    update_file(
        TOP_DIR.joinpath("INSTALL.md"), (r"/v[0-9]+(\.[0-9]+){2}", f"/v{version}")
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
            "Generated OpenAPI spec for test server did not match committed version.\n"
            "Run 'invoke update-openapijson' and re-commit.\n"
            f"Diff:\n{openapi_diff}"
        )
        sys.exit(1)

    openapi_index_diff = diff(index_openapi, local_index_openapi)
    if openapi_index_diff != {}:
        print(
            "Generated OpenAPI spec for Index meta-database did not match committed version.\n"
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


@task
def update_api_shield(_):
    """Updates the Github OPTIMADE API Shield"""
    shield = {
        "schemaVersion": 1,
        "label": "OPTIMADE",
        "message": f"v{__api_version__}",
        "color": "yellowgreen",
        "logoSvg": "<svg version='1' xmlns='http://www.w3.org/2000/svg' viewBox='0 0 55 55'><line x1='27' y1='14.5' x2='38.0' y2='7.94744111674' stroke='#9ed700' stroke-width='1.15' /><line x1='37.8253175473' y1='33.25' x2='38.0' y2='46.0525588833' stroke='#00acd9' stroke-width='1.15' /><line x1='16.1746824527' y1='33.25' x2='5' y2='27' stroke='#7a2dd0' stroke-width='1.15' /><line x1='49' y1='27' x2='38.0' y2='46.0525588833' stroke='#00acd9' stroke-width='1.15' /><line x1='38.0' y1='46.0525588833' x2='16.0' y2='46.0525588833' stroke='#e8e8e8' stroke-width='2' /><line x1='16.0' y1='46.0525588833' x2='5' y2='27' stroke='#7a2dd0' stroke-width='1.15' /><line x1='5' y1='27' x2='16.0' y2='7.94744111674' stroke='#e8e8e8' stroke-width='2' /><line x1='16.0' y1='7.94744111674' x2='38.0' y2='7.94744111674' stroke='#9ed700' stroke-width='1.15' /><line x1='38.0' y1='7.94744111674' x2='49' y2='27' stroke='#e8e8e8' stroke-width='2' /><circle cx='49' cy='27' r='3.5' fill='#00acd9' /><circle cx='38.0' cy='46.0525588833' r='3.5' fill='#00acd9' /><circle cx='16.0' cy='46.0525588833' r='3.5' fill='#7a2dd0' /><circle cx='5' cy='27' r='3.5' fill='#7a2dd0' /><circle cx='16.0' cy='7.94744111674' r='3.5' fill='#9ed700' /><circle cx='38.0' cy='7.94744111674' r='3.5' fill='#9ed700' /><line x1='27' y1='39.5' x2='16.1746824527' y2='33.25' stroke='#ff414d' stroke-width='1' /><line x1='16.1746824527' y1='33.25' x2='16.1746824527' y2='20.75' stroke='#ff414d' stroke-width='1' /><line x1='16.1746824527' y1='20.75' x2='27' y2='14.5' stroke='#ff414d' stroke-width='1' /><line x1='27' y1='14.5' x2='37.8253175473' y2='20.75' stroke='#ff414d' stroke-width='1' /><line x1='37.8253175473' y1='20.75' x2='37.8253175473' y2='33.25' stroke='#ff414d' stroke-width='1' /><line x1='37.8253175473' y1='33.25' x2='27' y2='39.5' stroke='#ff414d' stroke-width='1' /><circle cx='27' cy='39.5' r='2.5' fill='#ff414d' /><circle cx='16.1746824527' cy='33.25' r='2.5' fill='#ff414d' /><circle cx='16.1746824527' cy='20.75' r='2.5' fill='#ff414d' /><circle cx='27' cy='14.5' r='2.5' fill='#ff414d' /><circle cx='37.8253175473' cy='20.75' r='2.5' fill='#ff414d' /><circle cx='37.8253175473' cy='33.25' r='2.5' fill='#ff414d' /></svg>",
    }

    shields_json = Path(__file__).parent.resolve().joinpath("optimade-version.json")

    with open(shields_json, "w") as handle:
        json.dump(shield, handle, indent=2)
        handle.write("\n")  # Add newline cause Py JSON does not
