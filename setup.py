import os

from setuptools import setup, find_packages

module_dir = os.path.dirname(os.path.abspath(__file__))

setup(
    name="optimade",
    version="0.2.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['*.lark']},
    url="https://github.com/Materials-Consortia/optimade-python-tools",
    license="MIT",
    author="OPTiMaDe Development Team",
    author_email="dev@optimade.org",
    description="Tools for implementing and consuming OPTiMaDe APIs.",
    long_description=open(os.path.join(module_dir, "README.md")).read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "pymongo>=3.8",
        "lark-parser>=0.5.6",
        "mongomock>=3.16",
        "fastapi[all]",
    ],
    extras_require={
        "dev": ["black", "invoke", "pre-commit", "twine"],
        "mongo": ["mongogrant"],
        "django": ["django==2.2.5"],
        "elastic": ["elasticsearch_dsl>=6.4.0"]
    },
    tests_require=["pytest>=3.6", "openapi-spec-validator", "jsondiff"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Database :: Front-Ends",
    ],
    keywords="optimade jsonapi materials",
    python_requires=">=3.7",
)
