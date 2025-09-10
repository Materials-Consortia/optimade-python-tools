from optimade.server.mappers.entries import BaseResourceMapper
from optimade.models.entries import EntryResourceAttributes
from optimade.models.trajectories import TrajectoryResource
from optimade.models.structures import StructureAttributes
from bson.objectid import ObjectId
from collections import Counter
from optimade.server.config import CONFIG

__all__ = ("TrajectoryMapper",)


class TrajectoryMapper(BaseResourceMapper):
    # TODO add length aliases for trajectory specific properties
    LENGTH_ALIASES = (
        ("elements", "nelements"),
        ("element_ratios", "nelements"),
        ("cartesian_site_positions", "nsites"),
        ("species_at_sites", "nsites"),
    )
    HIDDEN_FIELDS = ["_id"]

    REFERENCE_STRUCTURE_FIELDS = list(StructureAttributes.__fields__.keys())
    STANDARD_FIELDS = (
        {"reference_structure", "reference_frame", "nframes", "available_properties"}
        .union(BaseResourceMapper.get_required_fields())
        .union(EntryResourceAttributes.__fields__.keys())
    )
    ENTRY_RESOURCE_CLASS = TrajectoryResource
    ENDPOINT = "trajectories"

    @classmethod
    def map_back(cls, doc: dict) -> dict:
        # DANI: The system is too limited to handle what we have in the database
        # DANI: A project may have multiple trajectories
        # DANI: In order to keep things simple we will return the reference MD trajectory
        project_id = doc["_id"]
        reference_md_index = doc["mdref"]
        reference_md = doc["mds"][reference_md_index]
        nframes = reference_md["frames"]
        reference_frame = reference_md.get("refframe", nframes)
        natoms = reference_md["atoms"]
        # Clean some fields from the project data so they are further parsed and renamed
        if doc.get("_id", None): del doc["_id"]
        if doc.get("mds", None): del doc["mds"]
        # Map the project document to an optimade format
        # TODO check whether fields are not in the exclude fields so we do not needlessly make an effort to generate them here.
        mapped_doc = super().map_back(doc)
        if mapped_doc["id"] is None:
            mapped_doc["id"] = project_id
        if "nframes" not in mapped_doc["attributes"]:
            mapped_doc["attributes"]["nframes"] = nframes
        if "last_modified" not in mapped_doc["attributes"]:
            # TODO Add the Modification date to the database.
            mapped_doc["attributes"]["last_modified"] = None
        if "reference_frame" not in mapped_doc["attributes"]:
            # Sometimes the trajectory starts with an unequilibrated structure so the last frame is more representative.
            mapped_doc["attributes"]["reference_frame"] = reference_frame

        # get species from sites
        from optimade.server.entry_collections.mongo import CLIENT
        from optimade.server.routers.utils import get_from_binary_gridfs

        # Get the topology associated to this project
        db = CLIENT[CONFIG.mongo_database]
        topology_collection = db["topologies"]
        topology = topology_collection.find_one({"project": ObjectId(project_id)})
        # Modifiy the reference structure to make it optimade-compliant
        mapped_doc["attributes"]["reference_structure"] = {"nsites": natoms}
        if "species_at_sites" not in CONFIG.exclude_from_reference_structure:
            mapped_doc["attributes"]["reference_structure"][
                "species_at_sites"
            ] = topology["atom_names"]
        # generate the species
        species = []
        found = []
        if "species" not in CONFIG.exclude_from_reference_structure:
            for i in range(mapped_doc["attributes"]["reference_structure"]["nsites"]):
                if topology["atom_names"][i] not in found:
                    found.append(topology["atom_names"][i])
                    species.append(
                        {
                            "name": topology["atom_names"][i],
                            "chemical_symbols": [topology["atom_elements"][i]],
                            "concentration": [1.0],
                        }
                    )
            # Todo check whether it is faster to add concentration in a later step.
            mapped_doc["attributes"]["reference_structure"]["species"] = species

        if "elements" not in CONFIG.exclude_from_reference_structure:
            element_stat = Counter(topology["atom_elements"])
            mapped_doc["attributes"]["reference_structure"]["elements"] = sorted(
                list(element_stat)
            )
            if "nelements" not in CONFIG.exclude_from_reference_structure:
                mapped_doc["attributes"]["reference_structure"]["nelements"] = len(
                    mapped_doc["attributes"]["reference_structure"]["elements"]
                )
            if "elements_ratios" not in CONFIG.exclude_from_reference_structure:
                mapped_doc["attributes"]["reference_structure"]["elements_ratios"] = [
                    element_stat[element]
                    / mapped_doc["attributes"]["reference_structure"]["nsites"]
                    for element in mapped_doc["attributes"]["reference_structure"][
                        "elements"
                    ]
                ]
        mapped_doc["attributes"]["reference_structure"]["dimension_types"] = [1, 1, 1]
        if "nperiodic_dimensions" not in CONFIG.exclude_from_reference_structure:
            mapped_doc["attributes"]["reference_structure"]["nperiodic_dimensions"] = 3
        if "lattice_vectors" not in CONFIG.exclude_from_reference_structure:
            mapped_doc["attributes"]["reference_structure"][
                "lattice_vectors"
            ] = None  # Todo: At the moment the lattice vectors are not curated Only the length of the vectors is stored in the database but not the angles.
        if "cartesian_site_positions" not in CONFIG.exclude_from_reference_structure:
            mapped_doc["attributes"]["reference_structure"][
                "cartesian_site_positions"
            ] = get_from_binary_gridfs(
                project_id,
                "trajectory.bin",
                mapped_doc["attributes"]["reference_frame"] - 1,
                mapped_doc["attributes"]["reference_frame"],
                1,
                mapped_doc["attributes"]["reference_structure"]["nsites"],
            )[
                0
            ].tolist()  # TODO The conversion to a list here is redundant when the output format is hdf5. The pydantic model however does not seem to handle numpy arrays.
        mapped_doc["attributes"]["reference_structure"]["structure_features"] = []
        mapped_doc["attributes"][
            "_" + CONFIG.provider.prefix + "_residues_at_sites"
        ] = topology["atom_residue_indices"]
        residues = []
        for i, name in enumerate(topology["residue_names"]):
            number = topology["residue_numbers"][i]
            if topology["residue_icodes"] is not None:
                icode = topology["residue_icodes"][i]
            else:
                icode = None
            residue = {"name": name, "number": number, "icode": icode}
            if topology["residue_chain_indices"] is not None:
                residue["chain"] = topology["chain_names"][
                    topology["residue_chain_indices"][i]
                ]
            residues.append(residue)
        mapped_doc["attributes"]["_" + CONFIG.provider.prefix + "_residues"] = residues

        if "available_properties" not in mapped_doc["attributes"]:
            mapped_doc["attributes"]["available_properties"] = {
                "cartesian_site_positions": {
                    "frame_serialization_format": "explicit",
                    "nvalues": mapped_doc["attributes"]["nframes"],
                }
            }
            mapped_doc["attributes"]["available_properties"]["lattice_vectors"] = {
                "frame_serialization_format": "constant",
                "nvalues": 1,
            }
            mapped_doc["attributes"]["available_properties"]["species"] = {
                "frame_serialization_format": "constant",
                "nvalues": 1,
            }
            mapped_doc["attributes"]["available_properties"]["dimension_types"] = {
                "frame_serialization_format": "constant",
                "nvalues": 1,
            }
            mapped_doc["attributes"]["available_properties"]["species_at_sites"] = {
                "frame_serialization_format": "constant",
                "nvalues": 1,
            }

        return mapped_doc
