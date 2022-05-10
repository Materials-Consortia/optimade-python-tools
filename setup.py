from pathlib import Path
import re
from setuptools import setup, find_packages

module_dir = Path(__file__).resolve().parent

with open(module_dir.joinpath("optimade/__init__.py")) as version_file:
    for line in version_file:
        match = re.match(r'__version__ = "(.*)"', line)
        if match is not None:
            VERSION = match.group(1)
            break
    else:
        raise RuntimeError(
            f"Could not determine package version from {version_file.name} !"
        )

# Dependencies
# Server minded
elastic_deps = ["elasticsearch-dsl~=6.4,<7.0"]
mongo_deps = ["pymongo>=3.12.1,<5", "mongomock~=4.0"]
server_deps = [
    "uvicorn~=0.17",
    "pyyaml>=5.4,<7",  # Keep at pyyaml 5.4 for aiida-core support
] + mongo_deps

# Client minded
aiida_deps = [
    "aiida-core~=1.6,>=1.6.4;python_version<'3.8'",
    "aiida-core~=2.0;python_version>='3.8'",
]
ase_deps = ["ase~=3.22"]
cif_deps = ["numpy~=1.21"]
pdb_deps = cif_deps
pymatgen_deps = ["pymatgen==2022.0.16"]
jarvis_deps = ["jarvis-tools==2022.5.5"]
client_deps = cif_deps

# General
docs_deps = [
    "markupsafe==2.0.1",  # Can be removed once aiida supports Jinja2>=3, see pallets/markupsafe#284
    "mike~=1.1",
    "mkdocs~=1.3",
    "mkdocs-awesome-pages-plugin~=2.7",
    "mkdocs-material~=8.2",
    "mkdocstrings~=0.18.1",
]
testing_deps = [
    "build~=0.7.0",
    "codecov~=2.1",
    "jsondiff~=2.0",
    "pytest~=7.1",
    "pytest-cov~=3.0",
] + server_deps
dev_deps = (
    ["pylint~=2.13", "pre-commit~=2.19", "invoke~=1.7"]
    + docs_deps
    + testing_deps
    + client_deps
)
all_deps = dev_deps + elastic_deps + aiida_deps + ase_deps + pymatgen_deps + jarvis_deps

setup(
    name="optimade",
    version=VERSION,
    url="https://github.com/Materials-Consortia/optimade-python-tools",
    license="MIT",
    author="OPTIMADE Development Team",
    author_email="dev@optimade.org",
    description="Tools for implementing and consuming OPTIMADE APIs.",
    long_description=open(module_dir.joinpath("README.md")).read(),
    long_description_content_type="text/markdown",
    keywords="optimade jsonapi materials",
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Database :: Front-Ends",
    ],
    python_requires=">=3.7,<3.11",
    install_requires=[
        "lark-parser~=0.12",
        "fastapi~=0.65.2",
        "pydantic~=1.9",
        "email_validator~=1.2",
        "requests~=2.27",
        "typing-extensions~=4.0;python_version<'3.8'",
    ],
    extras_require={
        "all": all_deps,
        "dev": dev_deps,
        "docs": docs_deps,
        "testing": testing_deps,
        "server": server_deps,
        "client": client_deps,
        "elastic": elastic_deps,
        "mongo": mongo_deps,
        "aiida": aiida_deps,
        "ase": ase_deps,
        "cif": cif_deps,
        "pdb": pdb_deps,
        "pymatgen": pymatgen_deps,
        "jarvis": jarvis_deps,
    },
    entry_points={
        "console_scripts": ["optimade-validator=optimade.validator:validate"]
    },
)
