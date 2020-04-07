import ast

from optimade.adapters.exceptions import ConversionError
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
    """ Get AiiDA StructureData from OPTIMADE structure
    :param optimade_structure: OPTIMADE structure
    :return: StructureData
    """
    if globals().get("StructureData", None) is None:
        warn(AIIDA_NOT_FOUND)
        return None

    # AiiDA cannot handle unknown positions
    for site in optimade_structure.attributes.cartesian_site_positions:
        if None in site:
            raise ConversionError(
                "AiiDA cannot be used to convert structures with unknown positions."
            )

    attributes = optimade_structure.attributes

    # Handle any None values in lattice_vectors (turn Null into 1.0)
    lattice_vectors = str(attributes.lattice_vectors)
    adjust_cell = False
    if "None" in lattice_vectors:
        adjust_cell = True
        lattice_vectors = lattice_vectors.replace("None", "1.0")
    lattice_vectors = ast.literal_eval(lattice_vectors)
    structure = StructureData(cell=lattice_vectors)

    # Add Kinds
    for kind in attributes.species:
        symbols = []
        concentration = []
        for index, chemical_symbol in enumerate(kind.chemical_symbols):
            # NOTE: The non-chemical element identifier "X" is identical to how AiiDA handles this,
            # so it will be treated the same as any other true chemical identifier.
            if chemical_symbol == "vacancy":
                # Skip. This is how AiiDA handles vacancies;
                # to not include them, while keeping the concentration in a site less than 1.
                continue
            else:
                symbols.append(chemical_symbol)
                concentration.append(kind.concentration[index])

        # AiiDA needs a definition for the mass, and for it to be > 0
        # mass is OPTIONAL for OPTIMADE structures
        mass = kind.mass if kind.mass else 1

        structure.append_kind(
            Kind(symbols=symbols, weights=concentration, mass=mass, name=kind.name)
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

    if adjust_cell:
        structure._adjust_default_cell(
            pbc=[bool(dim.value) for dim in attributes.dimension_types]
        )

    return structure
