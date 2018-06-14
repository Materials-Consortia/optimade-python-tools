import os

from setuptools import setup, find_packages

module_dir = os.path.dirname(os.path.abspath(__file__))

setup(
    name='optimade',
    version="0.1.10",
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/materialsproject/optimade/',
    license='modified BSD',
    author='MP Team',
    author_email='feedback@materialsproject.org',
    description='Tools for implementing and consuming OPTiMaDe APIs.',
    long_description=open(os.path.join(module_dir, 'README.md')).read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "marshmallow-jsonapi>=0.19.0",
        "marshmallow>=2.15.3",
        "pymongo>=3.6.1",
        "lark-parser>=0.5.6",
    ],
    tests_require=["pytest>=3.6"],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'Topic :: Database',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Database :: Front-Ends',
    ],
    keywords='optimade jsonapi materials',
    python_requires='>=3',
)