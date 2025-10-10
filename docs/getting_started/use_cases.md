# Example use cases

## Serving a single database

The [Materials Project](https://materialsproject.org) uses `optimade-python-tools` alongside their existing API and MongoDB database, providing [OPTIMADE-compliant access](https://optimade.materialsproject.org) to highly-curated density-functional theory calculations across all known inorganic materials.

`optimade-python-tools` handles filter parsing, database query generation and response validation by running the reference server implementation with minimal configuration.

[_odbx_](https://odbx.science), a small database of results from crystal structure prediction calculations, follows a similar approach.
This implementation is open source, available on GitHub at [ml-evs/odbx.science](https://github.com/ml-evs/odbx.science).

## Serving multiple databases

[Materials Cloud](https://materialscloud.org) uses `optimade-python-tools` as a library to provide an OPTIMADE API entries to 1) their main databases create with the [AiiDA](https://aiida.net) Python framework; and 2) to user-contributed data via the Archive platform. Separate OPTIMADE API apps are started for each database, mounted as separate endpoints to a parent FastAPI instance. For converting the underying data to the OPTIMADE format, the [optimade-maker](https://github.com/materialscloud-org/optimade-maker) toolkit is used.

## Extending an existing API

[NOMAD](https://nomad-lab.eu/) uses `optimade-python-tools` as a library to add OPTIMADE API endpoints to an existing web app.
Their implementation uses the Elasticsearch database backend to filter on millions of structures from aggregated first-principles calculations provided by their users and partners.
NOMAD also uses the package to implement a GUI search bar that accepts the OPTIMADE filter language.
NOMAD uses the release versions of the `optimade-python-tools` package, performing all customisation via configuration and sub-classing.
The NOMAD OPTIMADE API implementation is available in the [NOMAD FAIR GitLab repository](https://gitlab.mpcdf.mpg.de/nomad-lab/nomad-FAIR).

This use case is demonstrated in the example [Integrate OPTIMADE with an existing web application](../deployment/integrated.md).
