---
title: 'optimade-python-tools: a Python library for implementing and consuming materials data via OPTIMADE APIs'
tags:
  - Python
  - REST API
  - JSON:API
  - crystallography
  - density-functional theory
  - ab initio
  - materials discovery
  - databases
authors:
  - name: Matthew L. Evans
    orcid:  0000-0002-1182-9098
    affiliation: "1, 2"
  - name: Casper Andersen
    affiliation: 3
  - name: Shyam Dwaraknath
    affiliation: 4
  - name: Markus Scheidgen
    affiliation: 5
affiliations:
 - name: Theory of Condensed Matter Group, Cavendish Laboratory, University of Cambridge, J. J. Thomson Avenue, Cambridge, CB3 0HE, U.K.
   index: 1
 - name: Institut de la Matière Condensée et des Nanosciences, Université catholique de Louvain, Chemin des Étoiles 8, Louvain-la-Neuve 1348, Belgium
   index: 2
 - name: EPFL
   index: 3
 - name: LLBL
   index: 4
 - name: FHI
   index 5:

date: May 2021
bibliography: paper.bib
---

# Summary

<!--Follow similar spiel to OPTIMADE paper:-->
- advent of high-throughput computing, software and theory maturity, availability of compute power have lead to explosion of computational data.
- can be directly compared to high-quality measurements of crystal structures curated over many years
- this data is increasingly being made available via public APIs, such as...
- The OPTIMADE API specification was created to enable interoperability and machine-actionable APIs from multiple data providers

# Statement of need

In order to accommodate existing APIs, the OPTIMADE specification allows for flexibility in the specific data served but enforces its own simple, but domain-specific, filter language.
This flexibility could be daunting to database implementers and maintainers and could act to only increase the activation barrier to hosting an API.
`optimade-python-tools` catalyse the creation of APIs from existing and new data sources by providing a configurable and modular reference server implementation for hosting materials data in an OPTIMADE-compliant way.
The package leverages the modern Python libraries pydantic [@pydantic] and FastAPI [@FastAPI] to specify the data models and API routes defined in the OPTIMADE specification in a machine-readable OpenAPI format and allows for fast integration with databases that employ the popular MongoDB [@MongoDB] and Elasticsearch [@Elasticsearch] backends.

# Functionality

- define lark grammar for filter language
- abstracts transformations to database queries and provides concrete interfaces to common database backends
- defines data models for validation and serialization with machine-readable JSON schemas
- a reference web server using FastAPI and a corresponding OpenAPI specification that defines API endpoints and appropriately serializes responses
- an implementation validator that performs HTTP queries against remote OPTIMADE APIs, with test queries and expected responses generated dynamically based on the data served at the introspective endpoints `/info/` endpoints of the API.

# Use cases

OPT is used in production by three major data providers for atomistic modelling:

- The Materials Project uses `optimade-python-tools` alongside their existing API [@MAPI] and MongoDB database, providing access to highly-curated density-functional theory calculations across all known inorganic materials. `optimade-python-tools` handles filter parsing, database query generation and response validation by running the reference server implementation with minimal configuration.
- The NoMaD Repository and Archive integrates the `optimade-python-tools` server in an existing web app and uses the Elasticsearch implementation of the filtering module to allow access to 100M(?) published first-principles calculations submitted by users.
- Materials Cloud uses `optimade-python-tools` to provide domain-specific API access to published calculations that were created with AiiDa [@AiiDa] and archived on their system. In this case, each individual archive entry has its own database and separate API. The classes within `optimade-python-tools` have been extended to make use of AiiDa and its underlying PostgreSQL [@PostgreSQL] storage engine.

<!-- Could also mention clients/gateway/consortia infrastructure like the dashboard here?
OPT can also be used in client code; one application that the OPTIMADE specification enables is cross-origin queries. The-->

# Acknowledgements
