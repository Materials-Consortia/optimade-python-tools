from optimade.models import StructureResource as OptimadeStructure

try:
    from aiida.orm.nodes.data.structure import StructureData, Kind, Site
except (ImportError, ModuleNotFoundError):
    from warnings import warn

    StructureData = None
    AIIDA_NOT_FOUND = (
        "AiiDA not found, cannot convert structure to an AiiDA StructureData"
    )


__all__ = ("get_aiida_structure_data",)


def get_aiida_structure_data(optimade_structure: OptimadeStructure) -> StructureData:
    """ Get StructureData from OPTIMADE structure
    :param optimade_structure: OPTIMADE structure
    :return: StructureData
    """
    if globals().get("StructureData", None) is None:
        warn(AIIDA_NOT_FOUND)
        return None

    attributes = optimade_structure.attributes
    structure = StructureData(cell=attributes.lattice_vectors)

    # Add Kinds
    for kind in attributes.species:
        # NOTE: This should technically never happen,
        # since we are permanently adding to the filter
        # that we do not want structures with "disorder" or "unknown_positions"
        symbols = []
        for chemical_symbol in kind.chemical_symbols:
            if chemical_symbol == "vacancy":
                symbols.append("X")
            else:
                symbols.append(chemical_symbol)

        structure.append_kind(
            Kind(
                symbols=symbols,
                weights=kind.concentration,
                mass=kind.mass,
                name=kind.name,
            )
        )

    # Add Sites
    for index in range(attributes.nsites):
        # range() to ensure 1-to-1 between kind and site
        structure.append_site(
            Site(
                kind_name=attributes.species_at_sites[index],
                position=attributes.cartesian_site_positions[index],
            )
        )

    return structure
