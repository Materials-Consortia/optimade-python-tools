[![Build Status](https://travis-ci.org/Materials-Consortia/optimade-python-tools.svg?branch=master)](https://travis-ci.org/Materials-Consortia/optimade-python-tools)

The aim of OPTiMaDe is to develop a common API, compliant with the
[JSON API 1.0](http://jsonapi.org/format/1.0/) spec, to enable interoperability
among databases that contain calculated properties of existing and hypothetical
materials.

This repository contains a library of tools for implementing and consuming
[OPTiMaDe](http://www.optimade.org) APIs in Python.

### Status
Both the OPTiMaDe specification and this repository are **under development**.

### Links

 * [OPTiMaDe Specification](https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.rst), the human-readable specification that this library is based on
 * [OpenAPI](https://github.com/OAI/OpenAPI-Specification), the machine-readable format used to specify the OPTiMaDe API in [`openapi.json`](openapi.json)
 * [Interactive documentation](https://petstore.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/openapi.json#/operation/get_structures_structures_get) generated from [`openapi.json`](openapi.json) (see also [interactive JSON editor](https://editor.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/openapi.json#/operation/get_structures_structures_get))
 * [pydantic](https://pydantic-docs.helpmanual.io/), the library used for generating the OpenAPI schema from [python models](optimade/server/models)
 * [FastAPI](https://fastapi.tiangolo.com/), the framework used for generating the reference implementation from the [`openapi.json`](openapi.json) specification.
 * [lark](https://github.com/lark-parser/lark), the library used to parse the filter language in OPTiMaDe queries

### Developing

See [CONTRIBUTING](CONTRIBUTING.md).
