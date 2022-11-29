import re
from pathlib import Path

from setuptools import find_packages, setup

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
elastic_deps = ["elasticsearch-dsl~=7.4,<8.0", "elasticsearch~=7.17"]
mongo_deps = ["pymongo>=3.12.1,<5", "mongomock~=4.1"]
server_deps = [
    "uvicorn~=0.19",
    "fastapi~=0.86",
    "pyyaml>=5.4,<7",  # Keep at pyyaml 5.4 for aiida-core support
] + mongo_deps


# Client minded
aiida_deps = ["aiida-core~=2.1"]

http_client_deps = [
    "httpx~=0.23",
    "rich~=12.6",
    "click~=8.1",
]
ase_deps = ["ase~=3.22"]
cif_deps = ["numpy~=1.23"]
pdb_deps = cif_deps
pymatgen_deps = ["pymatgen~=2022.7"]
jarvis_deps = ["jarvis-tools==2022.8.27"]
client_deps = cif_deps

# General
docs_deps = [
    "mike~=1.1",
    "mkdocs~=1.4",
    "mkdocs-awesome-pages-plugin~=2.8",
    "mkdocs-material~=8.5",
    "mkdocstrings[python-legacy]~=0.19.0",
]
testing_deps = [
    "build~=0.9.0",
    "codecov~=2.1",
    "jsondiff~=2.0",
    "pytest~=7.2",
    "pytest-cov~=4.0",
    "pytest-httpx~=0.21",
] + server_deps
dev_deps = (
    [
        "black~=22.10",
        "flake8~=6.0",
        "isort~=5.10",
        "mypy~=0.991",
        "pylint~=2.15",
        "pre-commit~=2.20",
        "invoke~=1.7",
        "types-all==1.0.0",
    ]
    + docs_deps
    + testing_deps
    + client_deps
    + http_client_deps
)
all_deps = (
    dev_deps
    + elastic_deps
    + aiida_deps
    + ase_deps
    + pymatgen_deps
    + jarvis_deps
    + http_client_deps
)

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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Database :: Front-Ends",
    ],
    python_requires=">=3.8",
    install_requires=[
        "lark~=1.1",
        "pydantic~=1.10,>=1.10.2",
        "email_validator~=1.2",
        "requests~=2.28",
    ],
    extras_require={
        "all": all_deps,
        "dev": dev_deps,
        "http_client": http_client_deps,
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
        "console_scripts": [
            "optimade-validator=optimade.validator:validate",
            "optimade-get=optimade.client.cli:get",
        ]
    },
)
