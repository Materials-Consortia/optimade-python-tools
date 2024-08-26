<!-- markdownlint-disable MD033 -->
<!-- markdownlint-disable-next-line MD041 -->
<div align="center" style="padding-bottom: 1em;">
<img width="100px" align="center" src="https://matsci.org/uploads/default/original/2X/b/bd2f59b3bf14fb046b74538750699d7da4c19ac1.svg">
</div>

# <div align="center">OPTIMADE Python tools</div>

<div align="center">

<a href="https://doi.org/10.21105/joss.03458"><img alt="JOSS DOI" src="https://img.shields.io/badge/JOSS-10.21105%2Fjoss.03458-blueviolet"></a>
</div>

<div align="center">

<table>
<thead align="center">
<tr><th align="center">Latest release</th><th align="center">Build status</th><th align="center">Activity</th></tr>
</thead>

<tbody>
<tr>
  <td align="center">
    <a href="https://pypi.org/project/optimade"><img alt="PyPI version" src="https://img.shields.io/pypi/v/optimade?logo=pypi&logoColor=white"></a><br>
    <a href="https://pypi.org/project/optimade"><img alt="PyPI - Python Version"  src="https://img.shields.io/pypi/pyversions/optimade?logo=python&logoColor=white"></a><br>
    <a href="https://github.com/Materials-Consortia/OPTIMADE"><img alt="OPTIMADE version" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/optimade-version.json"></a>
  </td>
  <td align="center">
    <a href="https://github.com/Materials-Consortia/optimade-python-tools/actions?query=branch%3Amaster+"><img alt="Build Status" src="https://img.shields.io/github/actions/workflow/status/Materials-Consortia/optimade-python-tools/ci.yml?logo=github"></a><br>
    <a href="https://optimade.org/optimade-python-tools"><img alt="Docs" src="https://img.shields.io/github/actions/workflow/status/Materials-Consortia/optimade-python-tools/ci_cd_updated_master.yml?label=docs&logo=github"></a><br>
    <a href="https://codecov.io/gh/Materials-Consortia/optimade-python-tools"><img alt="Codecov" src="https://img.shields.io/codecov/c/github/Materials-Consortia/optimade-python-tools?logo=codecov&logoColor=white&token=UJAtmqkZZO"></a><br>
  </td>
  <td align="center">
    <a href="https://github.com/Materials-Consortia/optimade-python-tools/pulse"><img alt="Commit Activity" src="https://img.shields.io/github/commit-activity/m/Materials-Consortia/optimade-python-tools?logo=github"></a><br>
    <a href="https://github.com/Materials-Consortia/optimade-python-tools/commits/master"><img alt="Last Commit" src="https://img.shields.io/github/last-commit/Materials-Consortia/optimade-python-tools/master?logo=github"></a><br>
    <a href="https://github.com/Materials-Consortia/optimade-python-tools/graphs/contributors"><img alt="Contributors" src="https://badgen.net/github/contributors/Materials-Consortia/optimade-python-tools?icon=github"></a>
  </td>
</tr>
</tbody>
</table>

</div>

The aim of [OPTIMADE](https://optimade.org) is to develop a common API, compliant with the [JSON:API 1.0](http://jsonapi.org/format/1.0/) specification.
This is to enable interoperability among databases that serve crystal structures and calculated properties of existing and hypothetical materials.

This repository contains a library of tools for implementing and consuming [OPTIMADE APIs](https://www.optimade.org) using Python:

1. [pydantic](https://github.com/pydantic/pydantic) data models for all [OPTIMADE entry types](https://www.optimade.org/optimade-python-tools/latest/all_models/) and endpoint responses, and a [Lark](https://github.com/lark-parser/lark) [EBNF grammar](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form) implementation for the OPTIMADE filter language.
1. Adapters to map OPTIMADE data to and from many commonly used atomistic Python frameworks (e.g., [pymatgen](https://pymatgen.org/), [ASE](https://wiki.fysik.dtu.dk/ase/)) and crystallographic file types (e.g., [CIF](https://www.iucr.org/resources/cif)), using the `optimade.adapters` module.
1. A configurable reference server implementation that can make use of either MongoDB or Elasticsearch database backends out-of-the-box, and is readily extensible to other backends. Try it out on the [demo site](https://optimade.fly.dev)! The OpenAPI schemas of the server are used to construct the [OPTIMADE schemas](https://schemas.optimade.org/) site.
1. An [OPTIMADE client](https://www.optimade.org/optimade-python-tools/latest/getting_started/client/) (`optimade-get`) that can query multiple [OPTIMADE providers](https://optimade.org/providers-dashboard) concurrently with a given filter, at the command-line or from Python code.
1. A fuzzy API validator tool, which may be called from the shell (`optimade-validator`) or used as a GitHub Action from [optimade-validator-action](https://github.com/Materials-Consortia/optimade-validator-action); this validator is used to construct the [providers dashboard](https://optimade.org/providers-dashboard).


## Documentation

This document, guides, and the full module API documentation can be found online at [https://optimade.org/optimade-python-tools](https://optimade.org/optimade-python-tools).
In particular, documentation of the OPTIMADE API response data models (implemented here with [pydantic](https://github.com/pydantic/pydantic)) can be found online under [OPTIMADE Data Models](https://optimade.org/optimade-python-tools/latest/all_models).

The release history and changelog can be found in [the changelog](CHANGELOG.md).

## Installation

Detailed installation instructions for different use cases (e.g., using the library or running a server) can be found in [the installation documentation](INSTALL.md).

The latest stable version of this package can be obtained from [PyPI](https://pypi.org/project/optimade):

```shell
pip install optimade
```

The latest development version of this package can be obtained from the master branch of this repository:

```shell
git clone https://github.com/Materials-Consortia/optimade-python-tools
```

## Supported OPTIMADE versions

Each release of the `optimade` package from this repository only targets one version of the OPTIMADE specification, summarised in the table below.

<div align="center">

<table>

<thead>
    <tr>
        <th align="center">OPTIMADE API version</th>
        <th align="center"><code>optimade</code> requirements</th>
    </tr>
</thead>

<tbody>
    <tr>
        <td align="center"><a href="https://github.com/Materials-Consortia/OPTIMADE/blob/v1.0.0/optimade.rst">v1.0.0</a></td>
        <td align="center"><code>optimade<=0.12.9</code></td>  
    </tr>
    <tr>
        <td align="center"><a href="https://github.com/Materials-Consortia/OPTIMADE/blob/v1.1.0/optimade.rst">v1.1.0</a></td>
        <td align="center"><code>optimade~=0.16</code></td>
    </tr>
</tbody>
</table>
</div>

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
- [Lark](https://github.com/lark-parser/lark), the library used to parse the filter language in OPTIMADE queries.
