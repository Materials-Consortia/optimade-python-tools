from pathlib import Path
from setuptools import setup, find_namespace_packages


setup(
    name="optimade-validator",
    url="https://github.com/Materials-Consortia/optimade-python-tools",
    license="MIT",
    author="OPTIMADE Development Team",
    author_email="dev@optimade.org",
    description="Validator for the OPTIMADE APIs.",
    version="0.8.1",
    keywords="optimade jsonapi materials",
    packages=find_namespace_packages(include=["optimade.*"]),
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
    package_data={"optimade.validator.data": ["*.txt"]},
    python_requires=">=3.6",
    install_requires=["optimade-core~=0.8.1", "fastapi~=0.53", "pydantic~=1.4"],
    entry_points={
        "console_scripts": ["optimade_validator=optimade.validator:validate"]
    },
)
