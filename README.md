# OPTiMaDe Python tools

| Latest release | Build status | Activity |
|:--------------:|:------------:|:--------:|
| [![PyPI Version](https://img.shields.io/pypi/v/optimade?logo=pypi)](https://pypi.org/project/optimade/)<br>[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/optimade?logo=python)](https://pypi.org/project/optimade/)<br>[![OPTiMaDe](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/.ci/optimade-version.json&logo=json)](https://github.com/Materials-Consortia/OPTiMaDe/) | [![Build Status](https://img.shields.io/github/workflow/status/Materials-Consortia/optimade-python-tools/Testing,%20linting,%20and%20OpenAPI%20validation?logo=github)](https://github.com/Materials-Consortia/optimade-python-tools/actions?query=branch%3Amaster+)<br>[![codecov](https://codecov.io/gh/Materials-Consortia/optimade-python-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/Materials-Consortia/optimade-python-tools)<br>[![Heroku](https://heroku-badge.herokuapp.com/?app=optimade&root=v0/info)](https://optimade.herokuapp.com/v0/info) | [![Commit Activity](https://img.shields.io/github/commit-activity/m/Materials-Consortia/optimade-python-tools?logo=github)](https://github.com/Materials-Consortia/optimade-python-tools/pulse) |

The aim of OPTiMaDe is to develop a common API, compliant with the [JSON API 1.0](http://jsonapi.org/format/1.0/) specification.
This is to enable interoperability among databases that contain calculated properties of existing and hypothetical materials.

This repository contains a library of tools for implementing and consuming [OPTiMaDe](https://www.optimade.org) APIs using Python.
It also contains a server validator tool, which may be called from the shell or used as a GitHub Action.

## Status

Both the OPTiMaDe specification and this repository are **under development**.

The latest stable version can be obtained from [PyPI](https://pypi.org/project/optimade) `pip install optimade` or by cloning the master branch of this repository `git clone git@github.com:Materials-Consortia/optimade-python-tools`.

## Installation

Installation instructions, for both the index meta-database, and for the main API can be found in [INSTALL.md](INSTALL.md).

## Contributing

Contribution guidelines and tips can be found in [CONTRIBUTING.md](CONTRIBUTING.md).

## GitHub Action - OPTiMaDe validator

This action runs `optimade_validator` from this repository on a running server.

### Example usage

To run `optimade_validator` for an index meta-database at `http://gh_actions_host:5001/v0` do the following:  
Within the same job, first, start a server, e.g., using the `docker-compose.yml` setup from this repository, and then add the step

```yml
uses: Materials-Consortia/optimade-python-tools@master
with:
  port: 5001
  path: /v0
  index: yes
```

To run `optimade_validator` for a regular OPTiMaDe _deployed_ implementation, testing all possible versioned base URLs:

- `https://example.org:443/optimade/example/v0`
- `https://example.org:443/optimade/example/v0.10`
- `https://example.org:443/optimade/example/v0.10.1`

```yml
uses: Materials-Consortia/optimade-python-tools@master
with:
  protocol: https
  domain: example.org
  port: 443
  path: /optimade/example
  all versioned paths: True
```

### Inputs

#### `protocol`

**Optional** Protocol for the OPTiMaDe URL.  
**Default**: `http`

#### `domain`

**Optional** Domain for the OPTiMaDe URL (defaults to the GitHub Actions runner host).  
**Default**: `gh_actions_host`

#### `port`

**Optional** Port for the OPTiMaDe URL.  
**Default**: `5000`

#### `path`

**Optional** Path for the OPTiMaDe (versioned) base URL - MUST start with `/`  
_Note_: If `all versioned paths` is `true`, this MUST be un-versioned, e.g., `/optimade` or `/`, otherwise it MUST be versioned, e.g., the default value.  
**Default**: `/v0`

#### `all versioned paths`

**Optional** Whether to test all possible versioned base URLs:

- /vMAJOR
- /vMAJOR.MINOR
- /vMAJOR.MINOR.PATCH

If this is `'true'`, the input `'path'` MUST exempt the version part (e.g., `'/optimade'` instead of `'/optimade/v0'`).  
If this is `'false'`, the input `'path'` MUST include the version part (e.g., `'/optimade/v0'` instead of `'/optimade'`).  
**Default**: `false`

#### `index`

**Optional** Whether or not this is an index meta-database.  
**Default**: `false`

## Links

- [OPTiMaDe Specification](https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.rst), the human-readable specification that this library is based on.
- [OpenAPI](https://github.com/OAI/OpenAPI-Specification), the machine-readable format used to specify the OPTiMaDe API in [`openapi.json`](openapi.json).
- [Interactive documentation](https://petstore.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/openapi.json) generated from [`openapi.json`](openapi.json) (see also [interactive JSON editor](https://editor.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/openapi.json)).
- [pydantic](https://pydantic-docs.helpmanual.io/), the library used for generating the OpenAPI schema from [Python models](optimade/models).
- [FastAPI](https://fastapi.tiangolo.com/), the framework used for generating the reference implementation from the [`openapi.json`](openapi.json) specification.
- [lark](https://github.com/lark-parser/lark), the library used to parse the filter language in OPTiMaDe queries.
