from optimade.models import StructureResource
from optimade.adapters.base import EntryAdapter

from .aiida import get_aiida_structure_data
from .ase import get_ase_atoms
from .cif import get_cif
from .proteindatabank import get_pdb, get_pdbx_mmcif
from .pymatgen import get_pymatgen
from .jarvis import get_jarvis_atoms


class Structure(EntryAdapter):
    """
    Lazy structure resource converter.

    Go to [`EntryAdapter`][optimade.adapters.base.EntryAdapter] to see the full list of methods
    and properties.

    Attributes:
        ENTRY_RESOURCE (StructureResource): This adapter stores entry resources as
            [`StructureResource`][optimade.models.structures.StructureResource]s.
        _type_converters (Dict[str, Callable]): Dictionary of valid conversion types for entry.

            Currently available types:

            - `aiida_structuredata`
            - `ase`
            - `cif`
            - `pdb`
            - `pdbx_mmcif`
            - `pymatgen`
            - `jarvis`

        as_<_type_converters>: Convert entry to a type listed in `_type_converters`.

    """

    ENTRY_RESOURCE: StructureResource = StructureResource
    _type_converters = {
        "aiida_structuredata": get_aiida_structure_data,
        "ase": get_ase_atoms,
        "cif": get_cif,
        "pdb": get_pdb,
        "pdbx_mmcif": get_pdbx_mmcif,
        "pymatgen": get_pymatgen,
        "jarvis": get_jarvis_atoms,
    }
