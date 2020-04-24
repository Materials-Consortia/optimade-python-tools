from pathlib import Path
from setuptools import setup, find_packages

module_dir = Path(__file__).resolve().parent

# Dependencies
# Server minded
django_deps = ["django>=2.2.9,<4.0"]
elastic_deps = ["elasticsearch-dsl>=6.4,<8.0"]
mongo_deps = ["pymongo~=3.10", "mongomock~=3.19"]
server_deps = ["uvicorn", "Jinja2~=2.11"] + mongo_deps

# Client minded
aiida_deps = ["aiida-core~=1.1"]
ase_deps = ["ase~=3.19"]
cif_deps = ["numpy~=1.18"]
pdb_deps = cif_deps
pymatgen_deps = ["pymatgen~=2020.3"]
client_deps = cif_deps

# General
testing_deps = [
    "pytest~=5.4",
    "pytest-cov",
    "codecov",
    "openapi-spec-validator",
    "jsondiff",
] + server_deps
dev_deps = ["pylint", "black", "pre-commit", "invoke"] + testing_deps + client_deps
all_deps = dev_deps + django_deps + elastic_deps + aiida_deps + ase_deps + pymatgen_deps

setup(
    name="optimade",
    version="0.8.1",
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
        "lark-parser~=0.8.5",
        "fastapi~=0.53",
        "pydantic~=1.4",
        "email_validator",
        "requests~=2.23",
        'typing-extensions~=3.7.4.1;python_version<"3.8"',
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
    },
    entry_points={
        "console_scripts": ["optimade_validator=optimade.validator:validate"]
    },
)
