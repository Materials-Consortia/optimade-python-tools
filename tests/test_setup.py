import os
from pathlib import Path
import re
import tempfile
import pytest


package_data = [
    ".lark",
    "index_links.json",
    "test_structures.json",
    "test_references.json",
    "test_links.json",
    "landing_page.html",
    "providers.json",
]


@pytest.mark.parametrize("package_file", package_data)
def test_distribution_package_data(package_file):
    """Make sure a distribution has all the needed package data"""
    repo_root = Path(__file__).parent.parent.resolve()

    with tempfile.TemporaryDirectory() as temp_dir:
        file_output = Path(temp_dir).joinpath("sdist.out")

        os.chdir(repo_root)
        os.system(f"python setup.py sdist --dry-run > {file_output}")

        with open(file_output, "r") as file_:
            lines = file_.read()

        assert re.findall(package_file, lines), f"{package_file} file NOT found."
