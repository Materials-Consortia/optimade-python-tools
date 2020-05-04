from setuptools import setup, find_namespace_packages

setup(
    name="optimade-core",
    url="https://github.com/Materials-Consortia/optimade-python-tools",
    license="MIT",
    author="OPTIMADE Development Team",
    author_email="dev@optimade.org",
    description="Core grammar for the OPTIMADE APIs.",
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
    package_data={"optimade.grammar": ["*.lark"]},
    python_requires=">=3.6",
    install_requires=[
        "lark-parser~=0.8.5",
        "fastapi~=0.53",
        "pydantic~=1.4",
        "email_validator",
        'typing-extensions~=3.7.4.1;python_version<"3.8"',
    ],
)
