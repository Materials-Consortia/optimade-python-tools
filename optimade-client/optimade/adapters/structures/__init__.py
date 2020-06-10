from optimade.models import StructureResource
from optimade.adapters.base import EntryAdapter

from .aiida import get_aiida_structure_data
from .ase import get_ase_atoms
from .cif import get_cif
from .proteindatabank import get_pdb, get_pdbx_mmcif
from .pymatgen import get_pymatgen


__all__ = ("Structure",)


class Structure(EntryAdapter):
    """Lazy structure resource converter
    :param structure: a single JSON OPTIMADE structure resource entry.
    """

    ENTRY_RESOURCE = StructureResource
    _type_converters = {
        "aiida_structuredata": get_aiida_structure_data,
        "ase": get_ase_atoms,
        "cif": get_cif,
        "pdb": get_pdb,
        "pdbx_mmcif": get_pdbx_mmcif,
        "pymatgen": get_pymatgen,
    }
