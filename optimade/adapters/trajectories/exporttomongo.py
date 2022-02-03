import re
import MDAnalysis as mda
import pymatgen.core
import datetime
from optimade.server.config import CONFIG
from optimade.server.entry_collections import create_collection
from optimade.models.trajectories import TrajectoryResource
from optimade.server.mappers import TrajectoryMapper
import h5py
import warnings


def load_trajectory_data(
    structure_file,
    trajectory_files=None,
    storage_dir=None,
    id=None,
    reference_frame=0,
):
    # step 1: load file(s) with trajectory data
    # TODO It is probably better to use paths from the Path library instead of strings for the filenames
    # TODO Determine whether the file is small enough to store in memory in that case set "in_memory=True"
    if trajectory_files:
        traj = mda.Universe(structure_file, trajectory_files)
    else:
        traj = mda.Universe(structure_file)

    # Step2 generate pymatgen structure from MDAnalysis structure so we can also use the methods of pymatgen
    if traj.trajectory[reference_frame].dimensions is not None:
        boxdim = traj.trajectory[reference_frame].dimensions[:3]
        dictstruct = {
            "lattice": {
                "a": boxdim[0],
                "b": boxdim[1],
                "c": boxdim[2],
                "alpha": traj.trajectory[reference_frame].dimensions[3],
                "beta": traj.trajectory[reference_frame].dimensions[4],
                "gamma": traj.trajectory[reference_frame].dimensions[5],
            }
        }
        lattice_present = True
    else:
        lattice_present = False
        boxdim = [1.0, 1.0, 1.0]
        dictstruct = {
            "lattice": {
                "a": boxdim[0],
                "b": boxdim[1],
                "c": boxdim[2],
                "alpha": 90.0,
                "beta": 90.0,
                "gamma": 90.0,
            }
        }

    # dictstruct["charge"] = TODO MDTRAJ does not read charges from pdb files yet so we cannot implement this yet.
    sites = []
    nsites = traj.atoms.n_atoms
    for i in range(nsites):
        site = {
            "species": [{"element": traj.atoms.elements[i], "occu": getoccu(traj, i)}],
            "abc": traj.trajectory[reference_frame].positions[i] / boxdim[:3],
        }
        sites.append(site)

    dictstruct["sites"] = sites
    struct = pymatgen.core.structure.IStructure.from_dict(dictstruct)

    # step 3: generate all the neccesary OPTIMADE fields from the data
    # TODO add automatically reading  the units from the data if present
    n_frames = len(traj.trajectory)
    # type
    if n_frames > 1:
        type = "trajectories"
    else:
        type = "structures"
    # immutable_id (OPTIONAL)
    # last_modified
    last_modified = datetime.datetime.utcnow().replace(
        microsecond=0
    )  # MongeDB does not accept microseconds  #TODO: Is this sufficient ? strange things can happen with times
    # elements
    elements = sorted(struct.symbol_set)
    # nelements
    nelements = len(elements)
    # elements_ratios
    elements_ratios = [
        float(i)
        for i in re.sub(
            "[A-Z][a-z]*",
            "",
            struct.composition.fractional_composition.alphabetical_formula,
        ).split()
    ]
    # chemical_formula_descriptive
    chemical_formula_descriptive = struct.composition.alphabetical_formula.replace(
        " ", ""
    )
    # chemical_formula_reduced
    chemical_formula_reduced = (
        struct.composition.reduced_composition.alphabetical_formula.replace(" ", "")
    )
    # chemical_formula_hill(OPTIONAL)
    # chemical_formula_anonymous
    chemical_formula_anonymous = flip_chem_form_anon(
        struct.composition.anonymized_formula
    )
    # dimension_types
    dimension_types = None  # TODO: The pdb file I use for testing does not have this information. Most likely it is periodic but to be sure I should probably check whether: 1. particles move through the periodic boundaries 2. There are chemical bonds that go through the periodic boundary 3. particles that are outside the unitcell
    # nperiodic_dimensions
    if dimension_types:
        nperiodic_dimensions = sum(dimension_types)
    else:
        nperiodic_dimensions = None
    # lattice_vectors
    if lattice_present:
        lattice_vectors = struct.lattice.matrix.tolist()
    else:
        lattice_vectors = None
    # cartesian_site_positions
    cartesian_site_positions = struct.cart_coords.tolist()
    # nsites done before

    # species_at_sites
    if hasattr(
        traj.atoms, "names"
    ):  # TODO check whether this property is also present for file types other than PDB in that case this if statement is not neccesary
        species_at_sites = traj.atoms.names.tolist()
    else:
        species_at_sites = traj.atoms.elements.tolist()
    # species  # TODO the atom names/labels may not be unique enough in some cases. In that case extra descriptors such as the number of attached hydrogens or the charge have to be added.
    species = []
    for specie in set(species_at_sites):
        index = species_at_sites.index(specie)
        species.append(
            {
                "name": specie,
                "chemical_symbols": traj.atoms.elements[index],
                "concentration": getoccu(traj, index),
                "mass": traj.atoms.masses[index],
            }
        )
    # assemblies(OPTIONAL)
    # structure_features
    structure_features = (
        []
    )  # TODO make more checks to see which properties should be set here.
    for specie in species:
        if len(specie["chemical_symbols"]) > 1:
            structure_features.append("disorder")
            break

    available_properties = {
        "cartesian_site_positions": {
            "frame_serialization_format": "explicit",
            "nvalues": n_frames,  # TODO find examples of trajectories where the number of coordinates sets and the number of frames does not match.
        },
        "lattice_vectors": {"frame_serialization_format": "constant"},
        "species": {"frame_serialization_format": "constant"},
        "dimension_types": {"frame_serialization_format": "constant"},
        "species_at_sites": {"frame_serialization_format": "constant"},
    }
    time_present = True
    warnings.filterwarnings("error")
    try:  # MDAnalysis throws a warning when the timestep is not specified but does return a reasonable value of 1.0 ps. This can be confusing, so I therefore choose to catch this error.
        dt = traj.trajectory[0].dt
    except UserWarning:
        time_present = False
    warnings.filterwarnings("default")

    # TODO find examples of trajectories where the number of coordinates sets and the number of frames does not match.

    if time_present:  # if the time step is not zero or none
        available_properties["_exmpl_time"] = {"frame_serialization_format": "linear"}

    reference_structure = {
        "elements": elements,
        "nelements": nelements,
        "elements_ratios": elements_ratios,
        "chemical_formula_descriptive": chemical_formula_descriptive,
        "chemical_formula_reduced": chemical_formula_reduced,
        "chemical_formula_anonymous": chemical_formula_anonymous,
        "dimension_types": dimension_types,
        "nperiodic_dimensions": nperiodic_dimensions,
        "lattice_vectors": lattice_vectors,
        "cartesian_site_positions": cartesian_site_positions,
        "nsites": nsites,
        "species_at_sites": species_at_sites,
        "species": species,
        "structure_features": structure_features,
    }

    entry = {
        "reference_structure": reference_structure,
        "nframes": n_frames,
        "reference_frame": reference_frame,
        "available_properties": available_properties,
        "type": type,
        "last_modified": last_modified,
        "file_path": None,
        "cartesian_site_positions": {
            "frame_serialization_format": "explicit",
            "nvalues": n_frames,
            "storage_location": "file",
        },
        "lattice_vectors": {
            "frame_serialization_format": "constant",
            "storage_location": "mongo",
            "values": [lattice_vectors],
        },
        "species": {
            "frame_serialization_format": "constant",
            "storage_location": "mongo",
            "values": [species],
        },
        "dimension_types": {
            "frame_serialization_format": "constant",
            "storage_location": "mongo",
            "values": [dimension_types],
        },
        "species_at_sites": {
            "frame_serialization_format": "constant",
            "storage_location": "mongo",
            "values": [species_at_sites],
        },
    }
    if time_present:
        entry["_exmpl_time"] = {
            "storage_location": "mongo",
            "frame_serialization_format": "linear",
            "offset_linear": traj.trajectory[0].time,
            "step_size_linear": dt,
        }

    # Step 4: store trajectory data

    trajectories_coll = create_collection(
        name=CONFIG.trajectories_collection,
        resource_cls=TrajectoryResource,
        resource_mapper=TrajectoryMapper,
    )
    mongoid = trajectories_coll.insert([entry]).inserted_ids[0]
    if not id:
        id = str(mongoid)
    hdf5path = storage_dir + id + ".hdf5"
    trajectories_coll.collection.update_one(
        {"_id": mongoid}, {"$set": {"hdf5file_path": hdf5path, "id": id}}
    )
    if (
        type == "trajectories"
    ):  # TODO it would be nice to also allow adding structures in the same way we add trajectories
        # Write trajectory data in HDF5 format
        if not storage_dir:
            storage_dir = "/home/kwibus/Documents/Cecam/testfiles/"  # TODO It would be better to specify this in a config file
        with h5py.File(hdf5path, "w") as hdf5file:
            # if "_exmpl_time" in available_properties: #TODO It would be nice as we could store all the trajectory data in the HDF5 file So we should still add the storing of the other relevant trajectory info here as well.
            #    if entry["_exmpl_time"]["storage_location"] == "file":
            #        hdf5file["_exmpl_time/frame_serialization_format"] = "linear"
            #        hdf5file["_exmpl_time/offset_linear"] = traj.trajectory[0].time
            #        hdf5file["_exmpl_time/step_size_linear"] = dt
            if traj.trajectory[
                reference_frame
            ].has_positions:  # TODO check whether there are more properties that can be stored such as force and velocities
                arr = hdf5file.create_dataset(
                    "cartesian_site_positions/value",
                    (n_frames, nsites, 3),
                    chunks=True,
                    dtype=traj.trajectory[0].positions[0][0].dtype,
                )  # TODO allow for varying number of particles
                for i in range(
                    n_frames
                ):  # TODO offer the option to place only a part of the frames in the database
                    arr[i] = traj.trajectory[i].positions


def flip_chem_form_anon(chemical_formula_anonymous: str) -> str:
    """Converts an anonymous chemical formula with the most numerous element in the last position to an
    anonymous chemical formula with the most numerous element in the first position and vice versa."""
    numbers = [n for n in re.split(r"[A-Z][a-z]*", chemical_formula_anonymous)]
    anon_elem = [
        n
        for n in re.findall(
            "[A-Z][^A-Z]*", re.sub("[0-9]+", "", chemical_formula_anonymous)
        )
    ]
    return "".join(
        [
            y
            for x in range(len(anon_elem))
            for y in [anon_elem[x], numbers[len(anon_elem) - x]]
        ]
    )


def getoccu(traj, index):
    if hasattr(traj.atoms, "occupancies"):
        return traj.atoms.occupancies[index]
    else:
        return 1.0


# structure_file = "/home/kwibus/Documents/Cecam/testfiles/systemstripped.pdb"
trajectory_files = [
    "/home/kwibus/Documents/Cecam/testfiles/sarscov2-10875754-no-water-zinc-glueCA-0000.dcd"
]
# structure_file = "/home/kwibus/Documents/Cecam/testfiles/TRAJ.xyz"
structure_file = "/home/kwibus/Documents/Cecam/testfiles/ala_small_traj.pdb"
load_trajectory_data(
    structure_file,
    storage_dir="/home/kwibus/Documents/Cecam/testfiles/",
)
# load_trajectory_data(
#     structure_file,
#     trajectory_files,
#     storage_dir="/home/kwibus/Documents/Cecam/testfiles/",
# )
# replace_end("/home/kwibus/Documents/Cecam/testfiles/system.pdb","/home/kwibus/Documents/Cecam/testfiles/systemstripped.pdb")
