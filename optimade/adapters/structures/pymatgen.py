from typing import Union, Dict, List

from optimade.models import Species as OptimadeStructureSpecies
from optimade.models import StructureResource as OptimadeStructure
from optimade.models.structures import Periodicity

try:
    from pymatgen import Structure, Molecule

except (ImportError, ModuleNotFoundError):
    from warnings import warn

    Structure = None
    Molecule = None
    PYMATGEN_NOT_FOUND = "Pymatgen not found, cannot convert structure to a pymatgen Structure or Molecule"


__all__ = ("get_pymatgen_structure",)


def get_pymatgen_structure(
    optimade_structure: OptimadeStructure,
) -> Union[Structure, Molecule]:
    """ Get pymatgen Structure or Molecule from OPTIMADE structure

    :param optimade_structure: OPTIMADE structure
    :return: pymatgen.Structure , pymatgen.Molecule
    """
    if globals().get("Structure", None) is None:
        warn(PYMATGEN_NOT_FOUND)
        return None

    if optimade_structure.attributes.dimension_types == (Periodicity.PERIODIC,) * 3:
        return _get_structure(optimade_structure)

    return _get_molecule(optimade_structure)


def _get_structure(optimade_structure: OptimadeStructure) -> Structure:
    """Create pymatgen Structure from OPTIMADE structure"""

    attributes = optimade_structure.attributes

    return Structure(
        lattice=attributes.lattice_vectors,
        species=_pymatgen_species(
            nsites=attributes.nsites,
            species=attributes.species,
            species_at_sites=attributes.species_at_sites,
        ),
        coords=attributes.cartesian_site_positions,
        coords_are_cartesian=True,
    )


def _get_molecule(optimade_structure: OptimadeStructure) -> Molecule:
    """Create pymatgen Molecule from OPTIMADE structure"""

    attributes = optimade_structure.attributes

    return Molecule(
        species=_pymatgen_species(
            nsites=attributes.nsites,
            species=attributes.species,
            species_at_sites=attributes.species_at_sites,
        ),
        coords=attributes.cartesian_site_positions,
    )


def _pymatgen_species(
    nsites: int, species: List[OptimadeStructureSpecies], species_at_sites: List[str]
) -> List[Dict[str, float]]:
    """
    Create list of {"symbol": "concentration"} per site for values to pymatgen species parameters
    """

    optimade_species = {_.name: _ for _ in species}

    pymatgen_species = []
    for site_number in range(nsites):
        species_name = species_at_sites[site_number]
        current_species = optimade_species[species_name]

        pymatgen_species.append(
            dict(zip(current_species.chemical_symbols, current_species.concentration))
        )

    return pymatgen_species
