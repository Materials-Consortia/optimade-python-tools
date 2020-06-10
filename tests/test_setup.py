import os
from pathlib import Path
import re
import tempfile
import pytest


package_data = {
    "optimade-core": [r"\.lark"],
    "optimade-server": [
        r"index_links\.json",
        r"test_structures\.json",
        r"test_references\.json",
        r"test_links\.json",
        r"landing_page\.html",
    ],
    "optimade-validator": [r"filters\.txt", r"optional_filters\.txt"],
}


@pytest.mark.parametrize("ensure_package_data", list(package_data.items()))
def test_distribution_package_data(ensure_package_data):
    """Make sure a distribution has all the needed package data"""
    package_name, files = ensure_package_data
    repo_root = Path(__file__).parent.parent.resolve()
    package_root = repo_root.joinpath(package_name)
    print(package_root)

    with tempfile.TemporaryDirectory() as temp_dir:
        file_output = Path(temp_dir).joinpath("sdist.out")

        os.chdir(package_root)
        os.system(f"python setup.py sdist --dry-run > {file_output}")

        with open(file_output, "r") as file_:
            lines = file_.read()

        for requirement in files:
            assert re.findall(requirement, lines), f"{requirement} file NOT found."
