<img width="10%" align="left" src="images/optimade_logo_180x180.svg">

# OPTIMADE Python tools

| Latest release | Build status | Activity |
|:--------------:|:------------:|:--------:|
| [![PyPI Version](https://img.shields.io/pypi/v/optimade?logo=pypi&logoColor=white)](https://pypi.org/project/optimade/)<br>[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/optimade?logo=python&logoColor=white)](https://pypi.org/project/optimade/)<br>[![OPTIMADE](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/optimade-version.json)](https://github.com/Materials-Consortia/OPTIMADE/) | [![Build Status](https://img.shields.io/github/workflow/status/Materials-Consortia/optimade-python-tools/CI%20tests?logo=github)](https://github.com/Materials-Consortia/optimade-python-tools/actions?query=branch%3Amaster+)<br>[![codecov](https://img.shields.io/codecov/c/github/Materials-Consortia/optimade-python-tools?logo=codecov&logoColor=white&token=UJAtmqkZZO)](https://codecov.io/gh/Materials-Consortia/optimade-python-tools)<br>[![Heroku App Status](https://heroku-shields.herokuapp.com/optimade??logo=heroku)](https://optimade.herokuapp.com) | [![Commit Activity](https://img.shields.io/github/commit-activity/m/Materials-Consortia/optimade-python-tools?logo=github)](https://github.com/Materials-Consortia/optimade-python-tools/pulse)<br>[![Last Commit](https://img.shields.io/github/last-commit/Materials-Consortia/optimade-python-tools/master?logo=github)](https://github.com/Materials-Consortia/optimade-python-tools/commits/master)<br>[![Contributors](https://badgen.net/github/contributors/Materials-Consortia/optimade-python-tools?icon=github)](https://github.com/Materials-Consortia/optimade-python-tools/graphs/contributors) |

The aim of OPTIMADE is to develop a common API, compliant with the [JSON:API 1.0](http://jsonapi.org/format/1.0/) specification.
This is to enable interoperability among databases that contain calculated properties of existing and hypothetical materials.

This repository contains a library of tools for implementing and consuming [OPTIMADE](https://www.optimade.org) APIs using Python.
Server implementations can make use of the supported MongoDB (v4) and Elasticsearch (v6) database backends, or plug in a custom backend implementation.
The package also contains a server validator tool, which may be called from the shell (`optimade-validator`) or used as a GitHub Action from [optimade-validator-action](https://github.com/Materials-Consortia/optimade-validator-action).

The release history and changelog can be found in [the changelog](CHANGELOG.md).

## Documentation

This document, guides, and the full module API documentation can be found online at [https://optimade.org/optimade-python-tools](https://optimade.org/optimade-python-tools).
In particular, documentation of the OPTIMADE API response data models (implemented here with [pydantic](https://github.com/samuelcolvin/pydantic)) can be found online under [OPTIMADE Data Models](https://optimade.org/optimade-python-tools/all_models).

## Installation

Detailed installation instructions for different use cases (e.g., using the library or running a server) can be found in [the installation documentation](INSTALL.md).

The latest stable version of this package can be obtained from [PyPI](https://pypi.org/project/optimade) `pip install optimade`.
The latest development version of this package can be installed from the master branch of this repository `git clone https://github.com/Materials-Consortia/optimade-python-tools`.

## Supported OPTIMADE versions

Each release of the `optimade` package from this repository only targets one version of the OPTIMADE specification, summarised in the table below.

| OPTIMADE API version | `optimade` version |
|:--------------------:|:------------------:|
| [v1.0.0](https://github.com/Materials-Consortia/OPTIMADE/blob/v1.0.0/optimade.rst) | [v0.12.9](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.9) |
| [v1.1.0](https://github.com/Materials-Consortia/OPTIMADE/blob/v1.1.0/optimade.rst) | [v0.16.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.0) |

## Contributing and Getting Help

All development of this package (bug reports, suggestions, feedback and pull requests) occurs in the [optimade-python-tools GitHub repository](https://github.com/Materials-Consortia/optimade-python-tools).
Contribution guidelines and tips for getting help can be found in the [contributing notes](CONTRIBUTING.md).

## How to cite

If you use this package to access or serve OPTIMADE data, we kindly request that you consider citing the following:

- Andersen *et al.*, OPTIMADE, an API for exchanging materials data, *Sci. Data* **8**, 217 (2021) [10.1038/s41597-021-00974-z](https://doi.org/10.1038/s41597-021-00974-z)
- Evans *et al.*, optimade-python-tools: a Python library for serving and consuming materials data via OPTIMADE APIs. *Journal of Open Source Software*, **6**(65), 3458 (2021) [10.21105/joss.03458](https://doi.org/10.21105/joss.03458)

## Links

- [OPTIMADE Specification](https://github.com/Materials-Consortia/OPTIMADE/blob/develop/optimade.rst), the human-readable specification that this library is based on.
- [optimade-validator-action](https://github.com/Materials-Consortia/optimade-validator-action), a GitHub action that can be used to validate implementations from a URL (using the validator from this repo).
- [OpenAPI](https://github.com/OAI/OpenAPI-Specification), the machine-readable format used to specify the OPTIMADE API in [`openapi.json`](openapi/openapi.json) and [`index_openapi.json`](openapi/index_openapi.json).
- [Interactive documentation](https://petstore.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/openapi/openapi.json) generated from [`openapi.json`](openapi/openapi.json) (see also [interactive JSON editor](https://editor.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/openapi/openapi.json)).
- [pydantic](https://pydantic-docs.helpmanual.io/), the library used for generating the OpenAPI schema from [Python models](https://www.optimade.org/optimade-python-tools/all_models/).
- [FastAPI](https://fastapi.tiangolo.com/), the framework used for generating the reference implementation expressed by the [`openapi.json`](openapi/openapi.json) specification.
- [lark](https://github.com/lark-parser/lark), the library used to parse the filter language in OPTIMADE queries.
