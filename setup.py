from pathlib import Path
from setuptools import setup, find_packages

module_dir = Path(__file__).resolve().parent

testing_deps = [
    "pytest~=5.4",
    "pytest-cov",
    "codecov",
    "openapi-spec-validator",
    "jsondiff",
]
dev_deps = ["pylint", "black", "pre-commit", "invoke"] + testing_deps

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
        "optimade-core~=0.8.1",
        "optimade-server~=0.8.1",
        "optimade-client~=0.8.1",
        "optimade-validator~=0.8.1",
    ],
    extras_require={"dev": dev_deps, "testing": testing_deps},
)
