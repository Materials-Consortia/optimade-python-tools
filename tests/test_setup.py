"""Distribution tests."""

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


@pytest.fixture(scope="module")
def build_dist() -> str:
    """Run `python -m build` and return the output."""
    import os
    from pathlib import Path
    from tempfile import TemporaryDirectory

    repo_root = Path(__file__).parent.parent.resolve()

    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir).resolve()
        file_output = tmp_path / "sdist.out"

        os.chdir(repo_root)
        os.system(f"python -m build -o {tmp_path / 'dist'} > {file_output}")

        return file_output.read_text(encoding="utf-8")


@pytest.mark.parametrize("package_file", package_data)
def test_distribution_package_data(package_file: str, build_dist: str) -> None:
    """Make sure a distribution has all the needed package data."""
    import re

    assert re.findall(
        package_file, build_dist
    ), f"{package_file} file NOT found.\nOUTPUT:\n{build_dist}"
