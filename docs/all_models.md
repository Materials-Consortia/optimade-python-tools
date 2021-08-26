# OPTIMADE Data Models

This page provides unfolded documentation for specifically for the `optimade.models` submodule, where all of the OPTIMADE (and JSON:API)-defined data models are located.

For example, the three OPTIMADE entry types, `structures`, `references` and `links`, are defined primarily through the corresponding attribute models:

- [`StructureResourceAttributes`](#optimade.models.structures.StructureResourceAttributes)
- [`ReferenceResourceAttributes`](#optimade.models.references.ReferenceResourceAttributes)
- [`LinksResourceAttributes`](#optimade.models.links.LinksResourceAttributes)

As well as validating data types when creating instances of these models, this package defines several OPTIMADE-specific validators that ensure consistency between fields (e.g., the value of `nsites` matches the number of positions provided in `cartesian_site_positions`).

::: optimade.models
