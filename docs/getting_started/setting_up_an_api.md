# Setting up an OPTIMADE API

These notes describe how to set up and customize an OPTIMADE API based on the reference server in this package for some existing crystal structure data.

To follow this guide, you will need to have a working development installation, as described in the [installation instructions](../INSTALL.md#full-development-installation).
Complete examples of APIs that use this package are described in the [Use Cases](./use_cases.md) section.

## Setting up the database

The `optimade` reference server requires a data source per OPTIMADE entry type (`structures`, `references`, `links`).
In the simplest case, these can be configured as named MongoDB collections with a defined MongoDB URI and database name (see below), but they can also be set up as custom subclasses of [`EntryCollection`][optimade.server.entry_collections.entry_collections.EntryCollection] that could simply read from a static file.
In the reference server, these data sources, or collections, are created in the submodule for the corresponding routers/endpoints.

Here, we shall use the built-in MongoDB collections for each entry type, by simply specifying the appropriate options in the [configuration](../configuration.md), namely [`"database_backend": "mongodb"`][optimade.server.config.ServerConfig.database_backend], [`"mongo_uri": "mongodb://localhost:27017"`][optimade.server.config.ServerConfig.mongo_uri], [`"mongo_database": "optimade"`][optimade.server.config.ServerConfig.mongo_database] and the collection names for each entry type ([`"structures_collection": "structures"`][optimade.server.config.ServerConfig.structures_collection] etc.).
These notes will now assume that you have a MongoDB instance running and you have created a database that matches your [`"mongo_database"`][optimade.server.config.ServerConfig.mongo_database] config option.

If you disable inserting test data (with the [`"insert_test_data": false`][optimade.server.config.ServerConfig.insert_test_data] configuration option), you can test your API/database connection by running the web server with `uvicorn optimade.server.main:app --port 5000` and visiting the (hopefully empty) structures endpoint at `localhost:5000/v1/structures` (or your chosen base URL).

!!! note
    As of version v0.16, the other supported database backend is Elasticsearch.
    If you are interested in using another backend, or would like it to be supported in the `optimade` package, please raise an issue on [GitHub](https://github.com/Materials-Consortia/optimade-python-tools/issues/new) and visit the notes on implementing new [filter transformers](./filtering.md#developing-new-filter-transformers).

## Mapping non-OPTIMADE data

There are two ways to work with data that does not exactly match the OPTIMADE specification, both of which require configuring a subclass of [`BaseResourceMapper`][optimade.server.mappers.entries.BaseResourceMapper] that converts your stored data format into an OPTIMADE-compliant entry.
The two options are:

- Use the mapper to dynamically convert the data stored in the database, and the filters on that data, to an OPTIMADE format when responding to API requests.
- Apply the mapper to your entries before ingestion and use it to create a secondary database that stores the converted entries (e.g., normalized data), or equivalently, adding all the required OPTIMADE fields inside the existing entries (e.g., denormalized data)

The main consideration when choosing these options is not necessarily how closely your data matches the OPTIMADE format, but instead how readily the OPTIMADE filtering of that document can be mapped into the corresponding database query.
This could require writing or extending the [`BaseFilterTransformer`][optimade.filtertransformers.base_transformer.BaseTransformer] class, which takes an OPTIMADE filter string and converts it into a backend-specific query.

For example, if your database stores chemical formulae with extraneous "1"'s, e.g., SiO<sub>2</sub> is represented as `"Si1O2"`, then the incoming OPTIMADE filter (which asserts that elements must be alphabetical, and "1"'s must be omitted) for `chemical_formula_reduced="O2Si"` will also need to be transformed so that the corresponding database query matches the stored string, which in this case can be done easily.
Instead, if you are storing chemical formulae as an unreduced count per simulation cell, e.g., `"Si4O8"`, then it is impossible to remap the filter `chemical_formula_reduced="O2Si"` such that it matches all structures with the correct formula unit (e.g., `"SiO2"`, `"Si2O4"`, ...).
This would then instead require option 2 above, namely either the addition of auxiliary fields that store the correct (or mappable) OPTIMADE format in the database, or the creation of a secondary database that returns the pre-converted structures.

In the simplest case, the mapper classes can be used to define aliases between fields in the database and the OPTIMADE field name; these can be configured via the [`aliases`][optimade.server.config.ServerConfig.aliases] option as a dictionary mapping stored in a dictionary under the appropriate endpoint name, e.g. `"aliases": {"structures": {"chemical_formula_reduced": "my_chem_form"}}`, or defined as part of a custom mapper class.

In either option, you should now be able to insert your data into the corresponding MongoDB (or otherwise) collection.

## Serving custom fields/properties

According to the OPTIMADE specification, any field not standardized in the specification must be prefixed with an appropriate "provider prefix" (e.g., "`_aflow`" for [AFLOW](https://aflow.org) and "`_cod`" for [COD](https://crystallography.net)).
This prefix is intended to be unique across all [OPTIMADE providers](https://github.com/Materials-Consortia/providers) to enable filters to work across different implementations.
The prefix can be set in the [configuration](../configuration.md) as part of the [`provider`][optimade.server.config.ServerConfig.provider] option.

Once the prefix has been set, custom fields can be listed by endpoint in the [`provider_fields`][optimade.server.config.ServerConfig.provider_fields] configuration option.
Filters that use the prefixed form of these fields will then be passed through to the underlying database without the prefix, and then the prefix will be reinstated in the response.

!!! example
    Example JSON config file fragment for adding two fields to each of the `structures` and `references` endpoints, that will be served as, e.g., `_exmpl_cell_volume` if the `provider.prefix` is configured.
    ```json
        "provider_fields": {
            "structures": ["cell_volume", "total_energy"],
            "references": ["orcid", "num_citations"],
        }
    ```

It is recommended that you provide a description, type and unit for each custom field that can be returned at the corresponding `/info/<entry_type>` endpoint.
This can be achieved by providing a dictionary per field at [`provider_fields`][optimade.server.config.ServerConfig.provider_fields], rather than a simple list.

!!! example
    Example JSON config file fragment for adding a description, type and unit for the custom `_exmpl_cell_volume` field, which will cause it to be added to the `/info/structures` endpoint.
    ```json
        "provider_fields": {
            "structures": [
                {"name": "cell_volume", "description": "The volume of the cell per formula unit.", "units": "Ao3", "type": "float"},
                "total_energy"
            ],
            "references": ["orcid", "num_citations"],
        }
    ```

### More advanced usage

The pydantic models can also be extended with your custom fields.
This can be useful for validation, and for generating custom OpenAPI schemas for your implementation.
To do this, the underlying `EntryResourceAttributes` model will need to be sub-classed, the pydantic fields added to that class, and the server adjusted to make use of those models in responses.
In this case, it may be easier to write a custom endpoint for your entry type, that copies the existing reference endpoint.

Your custom model will need to be registered in three places:

1. The data collection.
1. The resource mapper class used by the collection.
1. The [`ENTRY_INFO_SCHEMAS`][optimade.server.schemas.ENTRY_INFO_SCHEMAS] dictionary.

Finally, the model must be instructed to use the prefixed (aliased) fields when generating its schemas.

Pulling all of this together:

```python
from optimade.server.schemas import ENTRY_INFO_SCHEMAS
from optimade.models import (
    StructureResource, StructureResourceAttributes, OptimadeField
)


class MyStructureResourceAttributes(StructureResourceAttributes):
     my_custom_field: str = OptimadeField(
        "default value",
        description="This is a custom field",
    )

    class Config:
        """Add a pydantic `Config` that defines the alias generator,
        based on our configured `provider_fields`.

        """
        @classmethod
        def alias_generator(cls, name: str) -> str:
            if name in CONFIG.provider_fields.get("structures", []):
                return f"_{CONFIG.provider.prefix}_{name}"
            return name


class MyStructureResource(StructureResource):
    attributes: MyStructureResourceAttributes


ENTRY_INFO_SCHEMAS["structures"] = MyStructureResource.schema
```

Currently, the reference server is not flexible enough to use custom response classes via configuration only (there is an open issue tracking this [#929](https://github.com/Materials-Consortia/optimade-python-tools/issues/929)), so instead the code will need to be forked and modified for your implementation.

## Validating your implementation

With the database collections, mappers, aliases and provider configured, you can try running the web server (with e.g., `uvicorn optimade.server.main:app`, if your app is in the same file as the reference server) and validating it as an OPTIMADE API, following the [validation guide](./validation.md).

## Registering as a provider

If you host your API at a persistent URL, you should consider registering as an OPTIMADE provider, which will add you to the federated list used by users and clients to discover data.
Instructions for how to do this can be found at in the [Materials-Consortia/providers](https://github.com/Materials-Consortia/providers) repository.
