from pathlib import Path
from setuptools import setup, find_packages

module_dir = Path(__file__).resolve().parent

# Dependencies
mongo_deps = ["pymongo~=3.8", "mongomock~=3.16"]
server_deps = ["uvicorn"] + mongo_deps
django_deps = ["django~=2.2,>=2.2.8"]
elastic_deps = ["elasticsearch_dsl~=6.4"]
testing_deps = [
    "pytest~=3.6",
    "pytest-cov",
    "codecov",
    "openapi-spec-validator",
    "jsondiff",
] + server_deps
dev_deps = ["pylint", "black", "pre-commit", "invoke"] + testing_deps
all_deps = dev_deps + django_deps + elastic_deps

setup(
    name="optimade",
    version="0.3.0",
    url="https://github.com/Materials-Consortia/optimade-python-tools",
    license="MIT",
    author="OPTiMaDe Development Team",
    author_email="dev@optimade.org",
    description="Tools for implementing and consuming OPTiMaDe APIs.",
    long_description=open(module_dir.joinpath("README.md")).read(),
    long_description_content_type="text/markdown",
    keywords="optimade jsonapi materials",
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Database :: Front-Ends",
    ],
    python_requires=">=3.7",
    install_requires=[
        "lark-parser~=0.7.8",
        "fastapi~=0.44",
        "pydantic~=1.2",
        "email_validator",
        "requests",
    ],
    extras_require={
        "all": all_deps,
        "dev": dev_deps,
        "server": server_deps,
        "testing": testing_deps,
        "django": django_deps,
        "elastic": elastic_deps,
        "mongo": mongo_deps,
    },
    entry_points={
        "console_scripts": ["optimade_validator=optimade.validator:validate"]
    },
)
