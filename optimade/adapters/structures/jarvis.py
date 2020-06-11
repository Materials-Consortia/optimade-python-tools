from warnings import warn
from optimade.models import StructureResource as OptimadeStructure
from optimade.adapters.exceptions import ConversionError
from optimade.adapters.structures.utils import pad_positions

try:
    from jarvis.core.atoms import Atoms
except (ImportError, ModuleNotFoundError):
    Atoms = None
    JARVIS_NOT_FOUND = "jarvis-tools package not found, cannot convert structure to a JARVIS Atoms. Visit https://github.com/usnistgov/jarvis"


__all__ = ("get_jarvis_atoms",)


def get_jarvis_atoms(optimade_structure: OptimadeStructure) -> Atoms:
    """ Get jarvis Atoms from OPTIMADE structure

    NOTE: Cannot handle partial occupancies

    :param optimade_structure: OPTIMADE structure
    :return: jarvis.core.Atoms
    """
    if globals().get("Atoms", None) is None:
        warn(JARVIS_NOT_FOUND)
        return None

    attributes = optimade_structure.attributes

    # Cannot handle partial occupancies
    if "disorder" in attributes.structure_features:
        raise ConversionError(
            "jarvis-tools cannot handle structures with partial occupancies."
        )

    cartesian_site_positions, _ = pad_positions(attributes.cartesian_site_positions)

    return Atoms(
        lattice_mat=attributes.lattice_vectors,
        elements=[specie.name for specie in attributes.species],
        coords=cartesian_site_positions,
        cartesian=True,
    )
