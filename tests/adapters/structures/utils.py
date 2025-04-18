import re
from pathlib import Path


def get_min_ver(dependency: str) -> str:
    """Retrieve version of `dependency` from pyproject.toml, raise if not found."""
    pyproject_toml = Path(__file__).parent.joinpath("../../../pyproject.toml")
    with open(pyproject_toml) as setup_file:
        for line in setup_file.readlines():
            min_ver = re.findall(rf'"{dependency}((=|!|<|>|~)=|>|<)(.+)"', line)
            if min_ver:
                return min_ver[0][2].split(";")[0].split(",")[0].strip('"')
        else:
            raise RuntimeError(f"Cannot find {dependency} dependency in pyproject.toml")
