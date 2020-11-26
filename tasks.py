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
    """Sets the OPTIMADE Python tools version"""
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

    update_file(
        TOP_DIR.joinpath("docs/static/default_config.json"),
        (r'"version": ".*",', f'"version": "{ver}",'),
    )

    print("Bumped version to {}".format(ver))


@task(help={"ver": "OPTIMADE API version to set"}, post=[update_openapijson])
def set_optimade_ver(_, ver=""):
    """Sets the OPTIMADE API Version"""
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
def get_markdown_spec(ctx):
    """Convert the develop OPTIMADE specification from `rst` to `md`."""
    print("Attempting to run pandoc...")
    ctx.run(
        "pandoc "
        "-f rst -t markdown_strict "
        "--wrap=preserve --columns=50000 "
        "https://raw.githubusercontent.com/Materials-Consortia/OPTIMADE/develop/optimade.rst "
        "> optimade.md"
    )


@task(
    help={
        "pre-clean": "Remove the 'api_reference' sub directory prior to (re)creation."
    }
)
def create_api_reference_docs(_, pre_clean=False):
    """Create the API Reference in the documentation"""
    import shutil

    def write_file(full_path: Path, content: str):
        """Write file with `content` to `full_path`"""
        if full_path.exists():
            with open(full_path, "r") as handle:
                cached_content = handle.read()
            if content == cached_content:
                del cached_content
                return
            del cached_content
        with open(full_path, "w") as handle:
            handle.write(content)

    optimade_dir = TOP_DIR.joinpath("optimade")
    docs_dir = TOP_DIR.joinpath("docs/api_reference")

    unwanted_subdirs = ("__pycache__", "data", "grammar", "static")

    pages_template = 'title: "{name}"\n'
    md_template = "# {name}\n\n::: {py_path}\n"
    models_template = (
        md_template + f"{' ' * 4}rendering:\n{' ' * 6}show_if_no_docstring: true\n"
    )

    if docs_dir.exists() and pre_clean:
        shutil.rmtree(docs_dir, ignore_errors=True)
        if docs_dir.exists():
            raise RuntimeError(f"{docs_dir} should have been removed!")
    docs_dir.mkdir(exist_ok=True)

    for dirpath, dirnames, filenames in os.walk(optimade_dir):
        for unwanted_dir in unwanted_subdirs:
            if unwanted_dir in dirnames:
                # Avoid walking into or through unwanted directories
                dirnames.remove(unwanted_dir)

        relpath = Path(dirpath).relative_to(optimade_dir)

        # Create `.pages`
        if str(relpath) == ".":
            write_file(
                full_path=docs_dir.joinpath(".pages"),
                content=pages_template.format(name="API Reference"),
            )
            continue

        docs_sub_dir = docs_dir.joinpath(relpath)
        docs_sub_dir.mkdir(exist_ok=True)
        write_file(
            full_path=docs_sub_dir.joinpath(".pages"),
            content=pages_template.format(name=str(relpath).split("/")[-1]),
        )

        # Create markdown files
        for filename in filenames:
            if re.match(r".*\.py$", filename) is None or filename == "__init__.py":
                # Not a Python file: We don't care about it!
                # Or filename is `__init__.py`: We don't want it!
                continue

            basename = filename[: -len(".py")]
            py_path = f"optimade/{relpath}/{basename}".replace("/", ".")
            md_filename = filename.replace(".py", ".md")

            # For models we want to include EVERYTHING, even if it doesn't have a doc-string
            template = models_template if str(relpath) == "models" else md_template

            write_file(
                full_path=docs_sub_dir.joinpath(md_filename),
                content=template.format(name=basename, py_path=py_path),
            )


@task(help={"fname": "The JSON file containing the OpenAPI schema to validate"})
def swagger_validator(_, fname):
    """This task can be used in the CI to test the generated OpenAPI schemas
    with the online swagger validator.

    Returns:
        Non-zero exit code if validation fails, otherwise returns `0`.

    """

    import requests

    def print_error(string):
        for line in string.split("\n"):
            print(f"\033[31m{line}\033[0m")

    swagger_url = "https://validator.swagger.io/validator/debug"
    with open(fname, "r") as f:
        schema = json.load(f)
    response = requests.post(swagger_url, json=schema)

    if response.status_code != 200:
        print_error(f"Server returned status code {response.status_code}.")
        sys.exit(1)

    try:
        json_response = response.json()
    except json.JSONDecodeError:
        print_error(f"Unable to parse validator response as JSON: {response}")
        sys.exit(1)

    if json_response:
        print_error(f"Schema file {fname} did not pass validation.\n")
        print_error(json.dumps(response.json(), indent=2))
        sys.exit(1)
