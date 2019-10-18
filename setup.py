import os
import glob

from setuptools import setup, find_packages

module_dir = os.path.dirname(os.path.abspath(__file__))

with open("requirements.txt") as f:
    requirements = [
        line.strip()
        for line in f.readlines()
        if line and not line.strip().startswith("#")
    ]

extra_requirements = {}
for fname in glob.glob("requirements/*_requirements.txt"):
    req = os.path.basename(fname).split("_")[0]
    with open(fname, "r") as f:
        extra_requirements[req] = [
            line.strip()
            for line in f.readlines()
            if line and not line.strip().startswith("#")
        ]

extra_requirements["all"] = [
    req for key in extra_requirements for req in extra_requirements[key]
]

setup(
    name="optimade",
    version="0.2.0",
    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/Materials-Consortia/optimade-python-tools",
    license="MIT",
    author="OPTiMaDe Development Team",
    author_email="dev@optimade.org",
    description="Tools for implementing and consuming OPTiMaDe APIs.",
    long_description=open(os.path.join(module_dir, "README.md")).read(),
    long_description_content_type="text/markdown",
    install_requires=requirements,
    extras_require=extra_requirements,
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
