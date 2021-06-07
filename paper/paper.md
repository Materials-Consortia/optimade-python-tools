---
title: '`optimade-python-tools`: a Python library for implementing and consuming materials data via OPTIMADE APIs'
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
    orcid: 0000-0002-2547-155X
    affiliation: 3
  - name: Shyam Dwaraknath
    orcid: 0000-0003-0289-2607
    affiliation: 4
  - name: Markus Scheidgen
    orcid: 0000-0002-8038-2277
    affiliation: 5
  - name: Ádám Fekete
    orcid: 0000-0002-6263-897X
    affiliation: "1, 6, 8"
  - name: Donald Winston
    orcid: 0000-0002-8424-0604
    affiliation: "4, 7"
affiliations:
 - name: Institut de la Matière Condensée et des Nanosciences, Université catholique de Louvain, Chemin des Étoiles 8, Louvain-la-Neuve 1348, Belgium
   index: 1
 - name: Theory of Condensed Matter Group, Cavendish Laboratory, University of Cambridge, J. J. Thomson Avenue, Cambridge, CB3 0HE, U.K.
   index: 2
 - name: EPFL
   index: 3
 - name: Lawrence Berkeley National Laboratory, Berkeley, CA, USA
   index: 4
 - name: FHI
   index: 5
 - name: Namur
   index: 6
 - name: Polyneme LLC
   index: 7
 - name: KCL
   index: 8

date: June 2021
bibliography: paper.bib
---

# Summary

<!--Follow similar spiel to OPTIMADE paper:-->
<!--- advent of high-throughput computing, software and theory maturity, availability of compute power have lead to explosion of computational data.-->
<!--- can be directly compared to high-quality measurements of crystal structures curated over many years-->
<!--- this data is increasingly being made available via public APIs, such as...-->
<!--- The OPTIMADE API specification was created to enable interoperability and machine-actionable APIs from multiple data providers-->

In recent decades, improvements in algorithms, hardware, and theory have enabled crystalline materials to be studied at the atomistic level with great accuracy and speed.
To enable dissemination, reproducibility, and reuse, many digital crystal structure databases have been created and curated, ready for comparison with existing infrastructure storing structural characterizations of real crystals.
These databases have been made available with bespoke application programming interfaces (APIs) to allow for automated and often open access to the underlying data.
Such esoteric APIs incur maintenance and usability costs upon both the data providers and consumers, who may not be software specialists.

The OPTIMADE API specification [@andersen2021optimade; @OPTIMADE_spec], released in July 2020, aimed to reduce these costs by designing a common API for use across a consortium of collaborating materials databases.
Whilst based on the robust JSON:API standard [@JSONAPI], the OPTIMADE API specification presents several domain-specific features and requirements that can be tricky to implement for non-specialist teams.
The package presented here, `optimade-python-tools`, provides a modular reference server implementation and a set of associated tools to accelerate the development process for data providers, toolmakers and end-users themselves.

# Statement of need

In order to accommodate existing materials database APIs, the OPTIMADE specification allows for flexibility in the specific data served but enforces a simple, but domain-specific, filter language on well-defined resources.
This flexibility could be daunting to database implementers and maintainers and could act to increase the activation barrier to hosting an API.
`optimade-python-tools` aims to catalyse the creation of APIs from existing and new data sources by providing a configurable and modular reference server implementation for hosting materials data in an OPTIMADE-compliant way.
The package leverages the modern Python libraries pydantic [@pydantic] and FastAPI [@FastAPI] to specify the data models and API routes defined in the OPTIMADE specification, additionally providing a schemas following the OpenAPI format [@OpenAPI].
Two storage back-ends are supported out of the box, with full filter support for databases that employ the popular MongoDB [@MongoDB] or Elasticsearch [@Elasticsearch] frameworks.

# Functionality

The modular functionality of `optimade-python-tools` can be broken down by the different stages of a user query to the reference server.
Consider the following query URL:

```
optimade.example.org/v1/structures?filter=chemical_formula_anonymous="ABC"
```

This query should match any crystal structures in the database with a composition that consists of any three elements in a 1:1:1 ratio. The "anatomy" of this query is displayed in Figure \ref{fig:query}.

1. After routing the query to the appropriate `/structures/` endpoint adhering to `v1` of the specification, the filter string `chemical_formula_anonymous="ABC"` is tokenized and parsed into an abstract tree by a `FilterParser` object using the Lark parsing library [@Lark] against the Extended Backus-Naur Form (EBNF) grammar defined by the specification.
2. The abstract tree is then transformed by a `FilterTransformer` object into a database query specific to the configured back-end for the server.
This transformation can include aliasing and custom transformations such that the underlying database format can be accommodates.
3. The results from the database query are then deserialized by `EntryResourceMapper` objects into the OPTIMADE-defined data models and then re-serialized into JSON before being served to the user over HTTP.

![Anatomy of an OPTIMADE query handled by the library.\label{fig:query}](./query.pdf)

Beyond this query functionality, the package also provides:

- A fuzzy implementation validator that performs HTTP queries against remote OPTIMADE APIs, with test queries and expected responses generated dynamically based on the data served at the introspective `/info/` endpoints of the API implementation.
- Entry "adapters" that can convert between OPTIMADE-compliant entries and the data models of the popular Python libraries `pymatgen` [@pymatgen] and `ase` (the Atomic Simulation Environment) [@ASE].

# Use cases

The package is currently used in production by three major data providers for atomistic data:

- The Materials Project uses `optimade-python-tools` alongside their existing API [@MAPI] and MongoDB database, providing access to highly-curated density-functional theory calculations across all known inorganic materials. `optimade-python-tools` handles filter parsing, database query generation and response validation by running the reference server implementation with minimal configuration.
- The NoMaD Repository and Archive integrates the `optimade-python-tools` server in an existing web app and uses the Elasticsearch implementation of the filtering module to allow access to 100M(?) published first-principles calculations submitted by users.
- Materials Cloud uses `optimade-python-tools` to provide domain-specific API access to published calculations that were created with AiiDa [@AiiDa] and archived on their system. In this case, each individual archive entry has its own database and separate API. The classes within `optimade-python-tools` have been extended to make use of AiiDa and its underlying PostgreSQL [@PostgreSQL] storage engine.

<!-- Could also mention clients/gateway/consortia infrastructure like the dashboard here?
OPT can also be used in client code; one application that the OPTIMADE specification enables is cross-origin queries. The-->

# Acknowledgements

M.E. would like to acknowledge the EPSRC Centre for Doctoral Training in Computational Methods for Materials Science for funding under grant number EP/L015552/1 and support from the European Union's Horizon 2020 research and innovation program under the European Union's Grant agreement No. 951786 (NOMAD CoE).
