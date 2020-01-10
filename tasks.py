import re

from invoke import task

from optimade import __version__


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
    with open("optimade/__init__.py", "r") as f:
        lines = [
            re.sub("__version__ = .+", '__version__ = "{}"'.format(new_ver), l.rstrip())
            for l in f
        ]
    with open("optimade/__init__.py", "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

    with open("setup.py", "r") as f:
        lines = [
            re.sub("version=([^,]+),", 'version="{}",'.format(new_ver), l.rstrip())
            for l in f
        ]
    with open("setup.py", "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

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

    c.run("cp openapi/local_openapi.json openapi/openapi.json")
    c.run("cp openapi/local_index_openapi.json openapi/index_openapi.json")


@task
def set_optimade_ver(_, ver=""):
    if not ver:
        raise Exception("Please specify --ver='Major.Minor.Patch'")
    with open("optimade/__init__.py", "r") as f:
        lines = [
            re.sub(
                "__api_version__ = .+", '__api_version__ = "{}"'.format(ver), l.rstrip()
            )
            for l in f
        ]
    with open("optimade/__init__.py", "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

    with open(".ci/optimade-version.json", "r") as f:
        lines = [
            re.sub('"message": .+', '"message": "v{}",'.format(ver), l.rstrip())
            for l in f
        ]
    with open(".ci/optimade-version.json", "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

    print("Bumped OPTiMaDe version to {}".format(ver))
