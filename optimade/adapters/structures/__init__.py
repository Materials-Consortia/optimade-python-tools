# pylint: disable=undefined-variable
from typing import Union

from optimade.models import StructureResource

from .aiida import get_aiida_structure_data
from .ase import get_ase_atoms
from .cif import get_cif
from .proteindatabank import get_pdb, get_pdbx_mmcif
from .pymatgen import get_pymatgen_structure


__all__ = ("Structure",)


class Structure:
    """Lazy structure converter
    :param structure: JSON OPTIMADE single structures resource entry.
    """

    _structure_type_converters = {
        "aiida_structuredata": get_aiida_structure_data,
        "ase": get_ase_atoms,
        "cif": get_cif,
        "pdb": get_pdb,
        "pdbx_mmcif": get_pdbx_mmcif,
        "pymatgen": get_pymatgen_structure,
    }

    def __init__(self, structure: dict):
        self._structure = None
        self._converted_structures = dict.fromkeys(self._structure_type_converters)

        self.structure = structure

    @property
    def structure(self) -> StructureResource:
        """Get OPTIMADE structure"""
        return self._structure

    @structure.setter
    def structure(self, value: dict):
        """Set OPTIMADE structure
        If already set, print that this can _only_ be set once.
        """
        if self._structure is None:
            self._structure = StructureResource(**value)
        else:
            print("structure can only be set once and is already set.")

    def __getattr__(self, name: str):
        """Get converted structure or attribute from OPTIMADE structure
        Order:
        - Try to return converted structure if using `get_<valid_structures value>`.
        - Try to return OPTIMADE StructureResource attribute.
        - Raise AttributeError
        """
        # get_<structure_type>
        if name.startswith("get_"):
            structure_type = "_".join(name.split("_")[1:])

            if structure_type not in self._structure_type_converters:
                raise AttributeError(
                    f"Non-valid structure type to convert to: {structure_type}. "
                    f"Valid structure types: {tuple(self._structure_type_converters.keys())}"
                )

            if self._converted_structures[structure_type] is None:
                self._converted_structures[
                    structure_type
                ] = self._structure_type_converters[structure_type](self.structure)

            return self._converted_structures[structure_type]

        # Try returning StructureResource attribute
        try:
            res = getattr(self.structure, name)
        except AttributeError:
            pass
        else:
            return res

        # Non-valid attribute
        raise AttributeError(
            f"Unknown attribute: {name}.\n"
            "If you want to get a converted structure use `get_<structure_type>`, "
            f"where `<structure_type>` is one of {tuple(self._structure_type_converters.keys())}\n"
            "Otherwise, you can try to retrieve an OPTIMADE StructureResource attribute."
        )
