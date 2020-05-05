import os
import re
import sys
from typing import Tuple
from pathlib import Path
import json

from invoke import task

from jsondiff import diff
from optimade.server import __version__

TOP_DIR = Path(__file__).parent.resolve()


def update_file(filename: str, sub_line: Tuple[str, str], strip: str = None):
    """Utility function for tasks to read, update, and write files"""
    with open(filename, "r") as handle:
        lines = [re.sub(sub_line[0], sub_line[1], l.rstrip(strip)) for l in handle]

    with open(filename, "w") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


@task
def setver(_, patch=False, new_ver=""):
    if (not patch and not new_ver) or (patch and new_ver):
        raise Exception(
            "Either use --patch or specify e.g. --new-ver='Major.Minor.Patch(a|b|rc)?[0-9]+'"
        )
    if patch:
        v = [int(x) for x in __version__.split(".")]
        v[2] += 1
        new_ver = ".".join(map(str, v))

    update_file(
        TOP_DIR.joinpath("optimade/__init__.py"),
        ("__version__ = .+", f'__version__ = "{new_ver}"'),
    )
    update_file(
        TOP_DIR.joinpath("setup.py"), ("version=([^,]+),", f'version="{new_ver}",')
    )

    print("Bumped version to {}".format(new_ver))


@task
def update_openapijson(c):
    # pylint: disable=import-outside-toplevel
    from optimade.server.main import app, update_schema
    from optimade.server.main_index import (
        app as app_index,
        update_schema as update_schema_index,
    )

    update_schema(app)
    update_schema_index(app_index)

    c.run(
        f"cp {TOP_DIR.joinpath('openapi/local_openapi.json')} {TOP_DIR.joinpath('openapi/openapi.json')}"
    )
    c.run(
        f"cp {TOP_DIR.joinpath('openapi/local_index_openapi.json')} {TOP_DIR.joinpath('openapi/index_openapi.json')}"
    )


@task
def set_optimade_ver(_, ver=""):
    if not ver:
        raise Exception("Please specify --ver='Major.Minor.Patch'")
    if not re.match("[0-9]+.[0-9]+.[0-9]+", ver):
        raise Exception("ver MUST be expressed as 'Major.Minor.Patch'")

    update_file(
        TOP_DIR.joinpath("optimade/__init__.py"),
        ("__api_version__ = .+", f'__api_version__ = "{ver}"'),
    )
    update_file(
        TOP_DIR.joinpath(".ci/optimade-version.json"),
        ('"message": .+', f'"message": "v{ver}",'),
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
        TOP_DIR.joinpath(".github/workflows/validator_action.yml"),
        ("/v[0-9]+", f"/v{ver.split('.')[0]}"),
    )
    update_file(
        TOP_DIR.joinpath("README.md"), ("v[0-9]+", f"v{ver.split('.')[0]}"), strip="\n"
    )
    update_file(TOP_DIR.joinpath("action.yml"), ("/v[0-9]+", f"/v{ver.split('.')[0]}"))
    update_file(
        TOP_DIR.joinpath("optimade/validator/github_action/entrypoint.sh"),
        (
            "'[0-9]+' '[0-9]+.[0-9]+' '[0-9]+.[0-9]+.[0-9]+'",
            f"'{ver.split('.')[0]}' '{'.'.join(ver.split('.')[:2])}' '{ver}'",
        ),
    )
    update_file(
        TOP_DIR.joinpath("INSTALL.md"), (r"/v[0-9]+(\.[0-9]+){2}", f"/v{version}")
    )

    print(f"Bumped OPTIMADE version to {ver}")


@task
def parse_spec_for_filters(_):
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

    with open(filter_path, "w") as f:
        for _filter in filters:
            f.write(_filter + "\n")

    with open(optional_filter_path, "w") as f:
        for _filter in optional_filters:
            f.write(_filter + "\n")


@task
def generate_openapi(_):
    """Update OpenAPI schema in file 'local_openapi.json'"""
    from optimade.server.main import app

    if not TOP_DIR.joinpath("openapi").exists():
        os.mkdir(TOP_DIR.joinpath("openapi"))
    with open(TOP_DIR.joinpath("openapi/local_openapi.json"), "w") as f:
        json.dump(app.openapi(), f, indent=2)

    """Update OpenAPI schema in file 'local_index_openapi.json'"""
    from optimade.server.main_index import app as app_index

    if not TOP_DIR.joinpath("openapi").exists():
        os.mkdir(TOP_DIR.joinpath("openapi"))
    with open(TOP_DIR.joinpath("openapi/local_index_openapi.json"), "w") as f:
        json.dump(app_index.openapi(), f, indent=2)


@task(generate_openapi)
def check_openapi_diff(_):
    with open(TOP_DIR.joinpath("openapi/openapi.json")) as f:
        openapi = json.load(f)

    with open(TOP_DIR.joinpath("openapi/local_openapi.json")) as f:
        local_openapi = json.load(f)

    with open(TOP_DIR.joinpath("openapi/index_openapi.json")) as f:
        index_openapi = json.load(f)

    with open(TOP_DIR.joinpath("openapi/local_index_openapi.json")) as f:
        local_index_openapi = json.load(f)

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
