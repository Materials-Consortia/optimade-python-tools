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
django_deps = ["django>=2.2.9,<4.0"]
elastic_deps = ["elasticsearch-dsl>=6.4,<8.0"]
mongo_deps = ["pymongo~=3.10", "mongomock~=3.19"]
server_deps = ["uvicorn~=0.11.5", "Jinja2~=2.11"] + mongo_deps

# Client minded
aiida_deps = ["aiida-core~=1.2"]
ase_deps = ["ase~=3.19"]
cif_deps = ["numpy~=1.18"]
pdb_deps = cif_deps
pymatgen_deps = ["pymatgen~=2020.6"]
jarvis_deps = ["jarvis-tools~=2020.6"]
client_deps = cif_deps

# General
testing_deps = [
    "pytest~=5.4",
    "pytest-cov~=2.9",
    "codecov~=2.1",
    "openapi-spec-validator~=0.2.8",
    "jsondiff~=1.2",
] + server_deps
dev_deps = (
    ["pylint~=2.5", "black~=19.10b0", "pre-commit~=2.5", "invoke~=1.4"]
    + testing_deps
    + client_deps
)
all_deps = (
    dev_deps
    + django_deps
    + elastic_deps
    + aiida_deps
    + ase_deps
    + pymatgen_deps
    + jarvis_deps
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
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Database :: Front-Ends",
    ],
    python_requires=">=3.6",
    install_requires=[
        "lark-parser~=0.8.6",
        "fastapi~=0.58.0",
        "pydantic~=1.5",
        "email_validator~=1.1",
        "requests~=2.23",
        'typing-extensions~=3.7;python_version<"3.8"',
    ],
    extras_require={
        "all": all_deps,
        "dev": dev_deps,
        "testing": testing_deps,
        "server": server_deps,
        "client": client_deps,
        "django": django_deps,
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
        "console_scripts": ["optimade_validator=optimade.validator:validate"]
    },
)
