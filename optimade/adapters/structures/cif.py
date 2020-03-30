import re
from typing import Dict

from optimade.models import Species as OptimadeStructureSpecies
from optimade.models import StructureResource as OptimadeStructure

from optimade.adapters.structures.utils import cell_to_cellpar


__all__ = ("get_cif",)


def get_cif(  # pylint: disable=too-many-locals,too-many-branches
    optimade_structure: OptimadeStructure, formatting: str = "default"
) -> str:
    """ Get CIF file as string from OPTIMADE structure

    Based on `ase.io.cif:write_cif()`.

    :param optimade_structure: OPTIMADE structure
    :param formatting: What formatting to use for the CIF file data keys.
        Can be either "mp" or "default".
    :param encoding: Encoding used for the string. CIF files use "latin-1" as standard.
        If encoding is "str", a Python str object will be returned.
    :return: str
    """
    cif = """#
# Created from an OPTIMADE structure.
#
# See https://www.optimade.org and/or
# https://github.com/Materials-Consortia/OPTIMADE for more information.
#
"""

    cif += f"data_{optimade_structure.id}\n\n"

    attributes = optimade_structure.attributes

    if formatting == "mp":
        comp_name = attributes.chemical_formula_reduced
        split_chemical_formula = re.findall(r"([A-Za-z]+)(([0-9]?)+)", comp_name)
        formula_sum = ""
        for symbol in split_chemical_formula:
            formula_sum += f"{symbol[0]}{symbol[1] if symbol[1] != '' else 1} "

        cif += (
            f"_chemical_formula_structural      {comp_name}\n"
            f"_chemical_formula_sum             '{formula_sum.strip()}'\n"
        )

    # Do this only if there's three non-zero lattice vectors
    if sum(attributes.dimension_types) == 3:
        a_vector, b_vector, c_vector, alpha, beta, gamma = cell_to_cellpar(
            attributes.lattice_vectors
        )

        cif += (
            f"_cell_length_a                    {a_vector:g}\n"
            f"_cell_length_b                    {b_vector:g}\n"
            f"_cell_length_c                    {c_vector:g}\n"
            f"_cell_angle_alpha                 {alpha:g}\n"
            f"_cell_angle_beta                  {beta:g}\n"
            f"_cell_angle_gamma                 {gamma:g}\n\n"
        )
        cif += (
            "_symmetry_space_group_name_H-M    'P 1'\n"
            "_symmetry_int_tables_number       1\n\n"
            "loop_\n"
            "  _symmetry_equiv_pos_as_xyz\n"
            "  'x, y, z'\n\n"
        )

    # Is it a periodic system?
    coord_type = (
        "fract" if hasattr(attributes, "fractional_site_positions") else "Cartn"
    )

    cif += "loop_\n"
    if formatting == "mp":
        cif += (
            "  _atom_site_type_symbol\n"
            "  _atom_site_label\n"
            "  _atom_site_symmetry_multiplicity\n"
            f"  _atom_site_{coord_type}_x\n"
            f"  _atom_site_{coord_type}_y\n"
            f"  _atom_site_{coord_type}_z\n"
            "  _atom_site_occupancy\n"
        )
    else:
        cif += (
            "  _atom_site_label\n"  # species.name
            "  _atom_site_occupancy\n"  # species.concentration
            f"  _atom_site_{coord_type}_x\n"  # cartesian_site_positions
            f"  _atom_site_{coord_type}_y\n"  # cartesian_site_positions
            f"  _atom_site_{coord_type}_z\n"  # cartesian_site_positions
            "  _atom_site_thermal_displace_type\n"  # Set to 'Biso'
            "  _atom_site_B_iso_or_equiv\n"  # Set to 1.0:f
            "  _atom_site_type_symbol\n"  # species.chemical_symbols
        )

    if coord_type == "fract":
        sites = attributes.fractional_site_positions
    else:
        sites = attributes.cartesian_site_positions

    species: Dict[str, OptimadeStructureSpecies] = {
        species.name: species for species in attributes.species
    }

    for site_number in range(attributes.nsites):
        species_name = attributes.species_at_sites[site_number]
        site = sites[site_number]

        current_species = species[species_name]

        for index, symbol in enumerate(current_species.chemical_symbols):
            if symbol == "vacancy":
                continue

            label = species_name
            if len(current_species.chemical_symbols) > 1:
                if (
                    "vacancy" in current_species.chemical_symbols
                    and len(current_species.chemical_symbols) == 2
                ):
                    pass
                else:
                    label = f"{symbol}{index + 1}"

            if formatting == "mp":
                cif += (
                    f"  {symbol:2}  {label:4s}  {'1':4}  {site[0]:8.5f}  {site[1]:8.5f}  "
                    f"{site[2]:8.5f}  {current_species.concentration[index]:6.1f}\n"
                )
            else:
                cif += (
                    f"  {label:8} {current_species.concentration[index]:6.4f} {site[0]:8.5f}  "
                    f"{site[1]:8.5f}  {site[2]:8.5f}  {'Biso':4}  {'1.000':6}  {symbol}\n"
                )

    return cif
