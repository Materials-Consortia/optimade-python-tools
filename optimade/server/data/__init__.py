""" Test Data to be used with the OPTIMADE server """
from pathlib import Path

import bson.json_util

data_paths = {
    "structures": "test_structures.json",
    "references": "test_references.json",
    "links": "test_links.json",
    "providers": "providers.json",
    "trajectories": "test_trajectories.json",
}

data_files = [
    (
        "mpf_551:cartesian_site_positions.npy",
        "numpy",
        {
            "endpoint": "structures",
            "parent_id": "mpf_551",
            "property_name": "cartesian_site_positions",
            "dim_names": ["dim_sites", "dim_cartesian_dimensions"],
        },
    ),
    (
        "6509be05a54743f440a7f36b:cartesian_site_positions.npy",
        "numpy",
        {
            "endpoint": "trajectories",
            "parent_id": "6509be05a54743f440a7f36b",
            "property_name": "cartesian_site_positions",
            "dim_names": ["dim_frames", "dim_sites", "dim_cartesian_dimensions"],
        },
    ),
]

for var, path in data_paths.items():
    try:
        with open(Path(__file__).parent / path) as f:
            globals()[var] = bson.json_util.loads(f.read())

        if var == "structures":
            globals()[var] = sorted(globals()[var], key=lambda x: x["task_id"])
    except FileNotFoundError:
        if var != "providers":
            raise
