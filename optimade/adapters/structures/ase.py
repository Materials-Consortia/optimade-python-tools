from typing import Dict
from warnings import warn

from optimade.models import Species as OptimadeStructureSpecies
from optimade.models import StructureResource as OptimadeStructure

from optimade.adapters.exceptions import ConversionError

try:
    from ase import Atoms, Atom
except (ImportError, ModuleNotFoundError):
    Atoms = None
    ASE_NOT_FOUND = "ASE not found, cannot convert structure to an ASE Atoms"


__all__ = ("get_ase_atoms",)


def get_ase_atoms(optimade_structure: OptimadeStructure) -> Atoms:
    """ Get ASE Atoms from OPTIMADE structure

    NOTE: Cannot handle partial occupancies (this includes vacancies)

    :param optimade_structure: OPTIMADE structure
    :return: ASE.Atoms
    """
    if globals().get("Atoms", None) is None:
        warn(ASE_NOT_FOUND)
        return None

    attributes = optimade_structure.attributes

    # Cannot handle partial occupancies
    if "disorder" in attributes.structure_features:
        raise ConversionError(
            "ASE cannot handle structures with partial occupancies, sorry."
        )

    species: Dict[str, OptimadeStructureSpecies] = {
        species.name: species for species in attributes.species
    }

    # Since we've made sure there are no species with more than 1 chemical symbol,
    # asking for index 0 will always work.
    if "X" in [specie.chemical_symbols[0] for specie in species.values()]:
        raise ConversionError(
            "ASE cannot handle structures with unknown ('X') chemical symbols, sorry."
        )

    atoms = []
    for site_number in range(attributes.nsites):
        species_name = attributes.species_at_sites[site_number]
        site = attributes.cartesian_site_positions[site_number]

        current_species = species[species_name]

        atoms.append(
            Atom(symbol=species_name, position=site, mass=current_species.mass)
        )

    return Atoms(
        symbols=atoms, cell=attributes.lattice_vectors, pbc=attributes.dimension_types
    )
