from .entries import ResourceMapper

__all__ = ("StructureMapper",)


class StructureMapper(ResourceMapper):

    ENDPOINT = "structures"
    ALIASES = (
        ("id", "task_id"),
        ("chemical_formula_descriptive", "pretty_formula"),
        ("chemical_formula_reduced", "pretty_formula"),
        ("chemical_formula_anonymous", "formula_anonymous"),
    )
