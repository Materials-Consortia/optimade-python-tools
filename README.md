# OPTiMaDe Python tools

| Latest release | Build status | Activity |
|:--------------:|:------------:|:--------:|
| [![PyPI Version](https://img.shields.io/pypi/v/optimade?logo=pypi)](https://pypi.org/project/optimade/)<br>[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/optimade?logo=python)](https://pypi.org/project/optimade/)<br>[![OPTiMaDe](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/.ci/optimade-version.json&logo=json)](https://github.com/Materials-Consortia/OPTiMaDe/) | [![Build Status](https://img.shields.io/github/workflow/status/Materials-Consortia/optimade-python-tools/Testing,%20linting,%20and%20OpenAPI%20validation?logo=github)](https://github.com/Materials-Consortia/optimade-python-tools/actions?query=branch%3Amaster+)<br>[![codecov](https://codecov.io/gh/Materials-Consortia/optimade-python-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/Materials-Consortia/optimade-python-tools)<br>[![Heroku](https://heroku-badge.herokuapp.com/?app=optimade&root=optimade/info)](https://optimade.herokuapp.com/optimade/info) | [![Commit Activity](https://img.shields.io/github/commit-activity/m/Materials-Consortia/optimade-python-tools?logo=github)](https://github.com/Materials-Consortia/optimade-python-tools/pulse) |

The aim of OPTiMaDe is to develop a common API, compliant with the [JSON API 1.0](http://jsonapi.org/format/1.0/) specification.
This is to enable interoperability among databases that contain calculated properties of existing and hypothetical materials.

This repository contains a library of tools for implementing and consuming [OPTiMaDe](http://www.optimade.org) APIs using Python.

## Status

Both the OPTiMaDe specification and this repository are **under development**.

## Installation (Index Meta-Database)

This package may be used to setup and run an [OPTiMaDe index meta-database](https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.rst#index-meta-database).
Install the package via `pip install optimade[server]` and change the file [`server.cfg`](server.cfg) found in the root of the package.

The `server.cfg` file serves paths to a server runtime configuration file (either an `ini` or `json` file, see the [`config.ini` file](optimade/server/config.ini) for an example) and an index `/links`-endpoint data file.
The paths must be relative from your current working directory, where your `server.cfg` is located, or they must be absolute paths.

The index meta-database is set up to populate a `mongomock` in-memory database with resources from a static `json` file containing the `child` resources you, as a database provider, want to serve under this index meta-database.

Running the index meta-database is then as simple as writing `./run.sh index` in a terminal from the root of this package.
You can find it at the base URL: [`http://localhost:5001/index/optimade/`](http://localhost:5001/index/optimade/).

_Note_: `server.cfg` is loaded from the current working directory, from where you run `run.sh`.
E.g., if you have installed `optimade` on a Linux machine at `/home/USERNAME/optimade/optimade-python-tools` and you run the following:

```shell
:~$ ./optimade/optimade-python-tools/run.sh index
```

Then you need `server.cfg` to be located in your home folder containing either relative paths from its current location or absolute paths.

## Development installation & Contributing

Full installation instructions and contribution guidelines can be found in [CONTRIBUTING](CONTRIBUTING.md).

## Links

* [OPTiMaDe Specification](https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.rst), the human-readable specification that this library is based on.
* [OpenAPI](https://github.com/OAI/OpenAPI-Specification), the machine-readable format used to specify the OPTiMaDe API in [`openapi.json`](openapi.json).
* [Interactive documentation](https://petstore.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/openapi.json) generated from [`openapi.json`](openapi.json) (see also [interactive JSON editor](https://editor.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/openapi.json)).
* [pydantic](https://pydantic-docs.helpmanual.io/), the library used for generating the OpenAPI schema from [Python models](optimade/models).
* [FastAPI](https://fastapi.tiangolo.com/), the framework used for generating the reference implementation from the [`openapi.json`](openapi.json) specification.
* [lark](https://github.com/lark-parser/lark), the library used to parse the filter language in OPTiMaDe queries.
