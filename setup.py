import os

from setuptools import setup, find_packages

module_dir = os.path.dirname(os.path.abspath(__file__))

# Create special extra dependencies
extras_require = {
    "dev": ["black", "invoke", "pre-commit", "twine"],
    "testing": ["pytest>=3.6", "pytest-cov", "openapi-spec-validator", "jsondiff"],
    "django": ["django>=2.2.5"],
    "elastic": ["elasticsearch_dsl>=6.4.0"],
}

extras_require["testing"] = set(
    extras_require["testing"] + extras_require["django"] + extras_require["elastic"]
)

extras_require["all"] = list(
    {item for sublist in extras_require.values() for item in sublist}
)

setup(
    name="optimade",
    version="0.2.0",
    url="https://github.com/Materials-Consortia/optimade-python-tools",
    license="MIT",
    author="OPTiMaDe Development Team",
    author_email="dev@optimade.org",
    description="Tools for implementing and consuming OPTiMaDe APIs.",
    long_description=open(os.path.join(module_dir, "README.md")).read(),
    long_description_content_type="text/markdown",
    keywords="optimade jsonapi materials",
    include_package_data=True,
    packages=find_packages(),
    package_data={"": ["*.lark"]},
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
        "pymongo>=3.8",
        "lark-parser>=0.7.7",
        "mongomock>=3.16",
        "fastapi[all]>=0.42.0",
    ],
    extras_require=extras_require,
    tests_require=list(extras_require["testing"]),
    entry_points={
        "console_scripts": ["optimade_validator=optimade.validator:validate"]
    },
)
