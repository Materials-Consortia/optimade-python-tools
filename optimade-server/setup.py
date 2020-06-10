from setuptools import setup, find_namespace_packages


django_deps = ["django>=2.2.9,<4.0"]
elastic_deps = ["elasticsearch-dsl>=6.4,<8.0"]

setup(
    name="optimade-server",
    url="https://github.com/Materials-Consortia/optimade-python-tools",
    license="MIT",
    author="OPTIMADE Development Team",
    author_email="dev@optimade.org",
    description="Python server implementation for the OPTIMADE APIs.",
    use_scm_version={"root": "..", "relative_to": __file__},
    setup_requires=["setuptools_scm"],
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
    package_data={"": ["*.json", "*.html"]},
    python_requires=">=3.6",
    install_requires=[
        "optimade-core~=0.8.1",
        "fastapi~=0.53",
        "pydantic~=1.4",
        "email_validator",
        'typing-extensions~=3.7.4.1;python_version<"3.8"',
        "pymongo~=3.10",
        "mongomock~=3.19",
        "uvicorn",
        "requests",
        "Jinja2~=2.11",
    ],
    extras_require={"django": django_deps, "elastic": elastic_deps},
)
