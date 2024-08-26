"""
Convert an OPTIMADE structure, in the format of
[`StructureResource`][optimade.models.structures.StructureResource]
to an ASE `Atoms` object.

This conversion function relies on the ASE code.

For more information on the ASE code see [their documentation](https://wiki.fysik.dtu.dk/ase/).
"""

from optimade.adapters.exceptions import ConversionError
from optimade.adapters.structures.utils import (
    elements_ratios_from_species_at_sites,
    species_from_species_at_sites,
)
from optimade.models import Species as OptimadeStructureSpecies
from optimade.models import StructureFeatures
from optimade.models import StructureResource as OptimadeStructure
from optimade.models.structures import StructureResourceAttributes
from optimade.models.utils import anonymize_formula, reduce_formula

EXTRA_FIELD_PREFIX = "ase"

try:
    from ase import Atom, Atoms
except (ImportError, ModuleNotFoundError):
    from warnings import warn

    from optimade.adapters.warnings import AdapterPackageNotFound

    Atoms = type("Atoms", (), {})
    ASE_NOT_FOUND = "ASE not found, cannot convert structure to an ASE Atoms"


__all__ = ("get_ase_atoms", "from_ase_atoms")


def get_ase_atoms(optimade_structure: OptimadeStructure) -> Atoms:
    """Get ASE `Atoms` from OPTIMADE structure.

    Caution:
        Cannot handle partial occupancies (this includes vacancies).

    Parameters:
        optimade_structure: OPTIMADE structure.

    Returns:
        ASE `Atoms` object.

    """
    if "optimade.adapters" in repr(globals().get("Atoms")):
        warn(ASE_NOT_FOUND, AdapterPackageNotFound)
        return None

    attributes = optimade_structure.attributes

    # Cannot handle partial occupancies
    if StructureFeatures.DISORDER in attributes.structure_features:
        raise ConversionError(
            "ASE cannot handle structures with partial occupancies, sorry."
        )

    species = attributes.species
    # If species is missing, infer data from species_at_sites
    if not species:
        species = species_from_species_at_sites(attributes.species_at_sites)  # type: ignore[arg-type]

    optimade_species: dict[str, OptimadeStructureSpecies] = {_.name: _ for _ in species}

    # Since we've made sure there are no species with more than 1 chemical symbol,
    # asking for index 0 will always work.
    if "X" in [specie.chemical_symbols[0] for specie in optimade_species.values()]:
        raise ConversionError(
            "ASE cannot handle structures with unknown ('X') chemical symbols, sorry."
        )

    atoms = []
    for site_number in range(attributes.nsites):  # type: ignore[arg-type]
        species_name = attributes.species_at_sites[site_number]  # type: ignore[index]
        site = attributes.cartesian_site_positions[site_number]  # type: ignore[index]

        current_species = optimade_species[species_name]

        # Argument above about chemical symbols also holds here
        mass = None
        if current_species.mass:
            mass = current_species.mass[0]

        atoms.append(
            Atom(symbol=current_species.chemical_symbols[0], position=site, mass=mass)
        )

    info = {}
    for key in attributes.model_dump().keys():
        if key.startswith("_"):
            ase_key = key
            if key.startswith(f"_{EXTRA_FIELD_PREFIX}_"):
                ase_key = "".join(key.split(f"_{EXTRA_FIELD_PREFIX}_")[1:])
            info[ase_key] = getattr(attributes, key)

    return Atoms(
        symbols=atoms,
        cell=attributes.lattice_vectors,
        pbc=attributes.dimension_types,
        info=info if info else None,
    )


def from_ase_atoms(atoms: Atoms) -> StructureResourceAttributes:
    """Convert an ASE `Atoms` object into an OPTIMADE `StructureResourceAttributes` model.

    Parameters:
        atoms: The ASE `Atoms` object to convert.

    Returns:
        An OPTIMADE `StructureResourceAttributes` model, which can be converted to a raw Python
            dictionary with `.model_dump()` or to JSON with `.model_dump_json()`.

    """
    if not isinstance(atoms, Atoms):
        raise RuntimeError(
            f"Cannot convert type {type(atoms)} into an OPTIMADE `StructureResourceAttributes` model."
        )

    attributes = {}
    attributes["cartesian_site_positions"] = atoms.positions.tolist()
    attributes["lattice_vectors"] = atoms.cell.tolist()
    attributes["species_at_sites"] = atoms.get_chemical_symbols()
    attributes["elements_ratios"] = elements_ratios_from_species_at_sites(
        attributes["species_at_sites"]
    )
    attributes["species"] = species_from_species_at_sites(
        attributes["species_at_sites"]
    )
    attributes["dimension_types"] = [int(_) for _ in atoms.pbc.tolist()]
    attributes["nperiodic_dimensions"] = sum(attributes["dimension_types"])
    attributes["nelements"] = len(attributes["species"])
    attributes["elements"] = sorted([_.name for _ in attributes["species"]])
    attributes["nsites"] = len(attributes["species_at_sites"])

    attributes["chemical_formula_descriptive"] = atoms.get_chemical_formula()
    attributes["chemical_formula_reduced"] = reduce_formula(
        atoms.get_chemical_formula()
    )
    attributes["chemical_formula_anonymous"] = anonymize_formula(
        attributes["chemical_formula_reduced"],
    )
    attributes["last_modified"] = None
    attributes["immutable_id"] = None
    attributes["structure_features"] = []

    for key in atoms.info:
        optimade_key = key.lower()
        if not key.startswith(f"_{EXTRA_FIELD_PREFIX}"):
            optimade_key = f"_{EXTRA_FIELD_PREFIX}_{optimade_key}"
        attributes[optimade_key] = atoms.info[key]

    return StructureResourceAttributes(**attributes)
