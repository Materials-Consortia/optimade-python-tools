"""
Convert an OPTIMADE structure, in the format of
[`StructureResource`][optimade.models.structures.StructureResource]
to a pymatgen `Molecule` or `Structure` object.

This conversion function relies on the [pymatgen](https://github.com/materialsproject/pymatgen) package.

For more information on the pymatgen code see [their documentation](https://pymatgen.org).
"""
from typing import Dict, List, Optional, Union

from optimade.adapters.structures.utils import (
    species_from_species_at_sites,
    valid_lattice_vector,
)
from optimade.models import Species as OptimadeStructureSpecies
from optimade.models import StructureResource as OptimadeStructure
from optimade.models import StructureResourceAttributes

try:
    from pymatgen.core import Composition, Lattice, Molecule, Structure

except (ImportError, ModuleNotFoundError):
    from warnings import warn

    from optimade.adapters.warnings import AdapterPackageNotFound

    Structure = type("Structure", (), {})
    Molecule = type("Molecule", (), {})
    Composition = type("Composition", (), {})
    PYMATGEN_NOT_FOUND = "Pymatgen not found, cannot convert structure to a pymatgen Structure or Molecule"


__all__ = (
    "get_pymatgen",
    "from_pymatgen",
)


def get_pymatgen(optimade_structure: OptimadeStructure) -> Union[Structure, Molecule]:
    """Get pymatgen `Structure` or `Molecule` from OPTIMADE structure.

    This function will return either a pymatgen `Structure` or `Molecule` based
    on the periodicity or periodic dimensionality of OPTIMADE structure.

    For structures that are periodic in one or more dimensions, a pymatgen `Structure` is returned when valid lattice_vectors are given.
    This means, if the any of the values in the [`dimension_types`][optimade.models.structures.StructureResourceAttributes.dimension_types]
    attribute is `1`s or if [`nperiodic_dimesions`][optimade.models.structures.StructureResourceAttributes.nperiodic_dimensions] > 0.

    Otherwise, a pymatgen `Molecule` is returned.

    Parameters:
        optimade_structure: OPTIMADE structure.

    Returns:
        A pymatgen `Structure` or `Molecule` based on the periodicity of the
        OPTIMADE structure.

    """
    if "optimade.adapters" in repr(globals().get("Structure")):
        warn(PYMATGEN_NOT_FOUND, AdapterPackageNotFound)
        return None

    if valid_lattice_vector(optimade_structure.attributes.lattice_vectors) and (  # type: ignore[arg-type]
        optimade_structure.attributes.nperiodic_dimensions > 0  # type: ignore[operator]
        or any(optimade_structure.attributes.dimension_types)  # type: ignore[arg-type]
    ):
        return _get_structure(optimade_structure)

    return _get_molecule(optimade_structure)


def _get_structure(optimade_structure: OptimadeStructure) -> Structure:
    """Create pymatgen Structure from OPTIMADE structure"""

    attributes = optimade_structure.attributes

    return Structure(
        lattice=Lattice(attributes.lattice_vectors, attributes.dimension_types),
        species=_pymatgen_species(
            nsites=attributes.nsites,  # type: ignore[arg-type]
            species=attributes.species,
            species_at_sites=attributes.species_at_sites,  # type: ignore[arg-type]
        ),
        coords=attributes.cartesian_site_positions,
        coords_are_cartesian=True,
    )


def _get_molecule(optimade_structure: OptimadeStructure) -> Molecule:
    """Create pymatgen Molecule from OPTIMADE structure"""

    attributes = optimade_structure.attributes

    return Molecule(
        species=_pymatgen_species(
            nsites=attributes.nsites,  # type: ignore[arg-type]
            species=attributes.species,  # type: ignore[arg-type]
            species_at_sites=attributes.species_at_sites,  # type: ignore[arg-type]
        ),
        coords=attributes.cartesian_site_positions,
    )


def _pymatgen_species(
    nsites: int,
    species: Optional[List[OptimadeStructureSpecies]],
    species_at_sites: List[str],
) -> List[Dict[str, float]]:
    """
    Create list of {"symbol": "concentration"} per site for values to pymatgen species parameters.
    Remove vacancies, if they are present.
    """
    if not species:
        # If species is missing, infer data from species_at_sites
        species = species_from_species_at_sites(species_at_sites)

    optimade_species = {_.name: _ for _ in species}

    pymatgen_species = []
    for site_number in range(nsites):
        species_name = species_at_sites[site_number]
        current_species = optimade_species[species_name]

        chemical_symbols = []
        concentration = []
        for index, symbol in enumerate(current_species.chemical_symbols):
            if symbol == "vacancy":
                # Skip. This is how pymatgen handles vacancies;
                # to not include them, while keeping the concentration in a site less than 1.
                continue
            else:
                chemical_symbols.append(symbol)
                concentration.append(current_species.concentration[index])

        pymatgen_species.append(dict(zip(chemical_symbols, concentration)))

    return pymatgen_species


def from_pymatgen(pmg_structure: Structure) -> StructureResourceAttributes:
    """Convert a pymatgen `Structure` (3D) into an OPTIMADE `StructureResourceAttributes` model.

    Parameters:
        pmg_structure: The pymatgen `Structure` to convert.

    Returns:
        An OPTIMADE `StructureResourceAttributes` model, which can be converted to a raw Python
            dictionary with `.dict()` or to JSON with `.json()`.

    """

    if not isinstance(pmg_structure, Structure):
        raise RuntimeError(
            f"Cannot convert type {type(pmg_structure)} into an OPTIMADE `StructureResourceAttributes` model."
        )

    attributes = {}
    attributes["cartesian_site_positions"] = pmg_structure.lattice.get_cartesian_coords(
        pmg_structure.frac_coords
    ).tolist()
    attributes["lattice_vectors"] = pmg_structure.lattice.matrix.tolist()
    attributes["species_at_sites"] = [_.symbol for _ in pmg_structure.species]
    attributes["species"] = [
        {"name": _.symbol, "chemical_symbols": [_.symbol], "concentration": [1]}
        for _ in set(pmg_structure.composition.elements)
    ]
    attributes["dimension_types"] = [int(_) for _ in pmg_structure.lattice.pbc]
    attributes["nperiodic_dimensions"] = sum(attributes["dimension_types"])
    attributes["nelements"] = len(pmg_structure.composition.elements)
    attributes["chemical_formula_anonymous"] = _pymatgen_anonymized_formula_to_optimade(
        pmg_structure.composition
    )
    attributes["elements"] = sorted(
        [_.symbol for _ in pmg_structure.composition.elements]
    )
    attributes["chemical_formula_reduced"] = _pymatgen_reduced_formula_to_optimade(
        pmg_structure.composition
    )
    attributes["chemical_formula_descriptive"] = pmg_structure.composition.formula
    attributes["elements_ratios"] = [
        pmg_structure.composition.get_atomic_fraction(e) for e in attributes["elements"]
    ]
    attributes["nsites"] = len(attributes["species_at_sites"])

    attributes["last_modified"] = None
    attributes["immutable_id"] = None
    attributes["structure_features"] = []

    return StructureResourceAttributes(**attributes)


def _pymatgen_anonymized_formula_to_optimade(composition: Composition) -> str:
    """Construct an OPTIMADE `chemical_formula_anonymous` from a pymatgen `Composition`."""
    import re

    from optimade.models.utils import anonymous_element_generator

    return "".join(
        [
            "".join(x)
            for x in zip(
                anonymous_element_generator(),
                reversed(re.split("[A-Z]", composition.anonymized_formula)[1:]),
            )
        ]
    )


def _pymatgen_reduced_formula_to_optimade(composition: Composition) -> str:
    """Construct an OPTIMADE `chemical_formula_reduced` from a pymatgen `Composition`."""
    import numpy

    numbers = [int(_) for _ in composition.to_reduced_dict.values()]
    gcd = numpy.gcd.reduce(numbers)
    return "".join(
        _
        + f"{int(composition.to_reduced_dict[_]) // gcd if composition.to_reduced_dict[_] // gcd > 1 else ''}"
        for _ in sorted([_.symbol for _ in composition.elements])
    )
