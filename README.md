[![Build Status](https://travis-ci.org/Materials-Consortia/optimade-python-tools.svg?branch=master)](https://travis-ci.org/Materials-Consortia/optimade-python-tools)

A library of tools for implementing and consuming
[OPTiMaDe](http://www.optimade.org) APIs in Python.

The aim of OPTiMaDe is to develop a common API, compliant
with the [JSON API 1.0](http://jsonapi.org/format/1.0/)
spec, to enable interoperability
among databases
that contain calculated properties of
existing and hypothetical materials.

### Status
This library is under development. Progress is expected during the [CECAM Workshop on Open Databases Integration for Materials Design](https://www.cecam.org/workshop-4-1525.html) during the week of June 11, 2018 to June 15, 2018.

### Getting Started

Install via `pip install optimade`. Example use:

```python
from optimade.filter import Parser

p = Parser(version=(0, 9, 5))
p.parse("filter=a<3")
```
```
Tree(start, [Token(KEYWORD, 'filter='), Tree(expression, [Tree(term, [Tree(atom, [Tree(comparison, [Token(VALUE, 'a'), Token(OPERATOR, '<'), Token(VALUE, '3')])])])])])
```
```python
p = Parser()
p.version
```
```
(0, 9, 5)
```
```python
tree = p.parse('filter=_mp_bandgap > 5.0 AND _cod_molecular_weight < 350')
print(p)
```
```
start
  filter=
  expression
    term
      term
        atom
          comparison
            _mp_bandgap
            >
            5.0
      AND
      atom
        comparison
          _cod_molecular_weight
          <
          350
```
```python
# Assumes graphviz installed on system and `pip install pydot`
from lark.tree import pydot__tree_to_png

pydot__tree_to_png(tree, "exampletree.png")
```
![example tree](exampletree.png)

### File Structure
```
.
|____optimade
| |______init__.py
| |____filter.py
| |____grammar
| | |______init__.py
| | |____v0.9.5.g
| | |____...
| |____converter
| | |______init__.py
| | |____mongoconverter
| | | |____mongo.py
| | | |____tests
| | | | |____test_bank.py
| | | | |______init__.py
| | | | |____test_converter.py
| | | |______init__.py
| | | |______pycache__
| | | |____config.ini
| | | |______main__.py
| |____tests
| | |____testfiles
| | | |____parse_005.inp
| | | |____...
| | |____test_filter.py
| | |______init__.py
|____optimade.egg-info
| |____PKG-INFO
| |____SOURCES.txt
| |____entry_points.txt
| |____requires.txt
| |____top_level.txt
| |____dependency_links.txt
|____tasks.py
|____LICENSE
|____requirements.txt
|____MANIFEST.in
|____requirements-optional.txt
|____README.md
|____setup.py
|____exampletree.png
```
### General Procedure
`Parser` will take user input to generate a tree and feed that to a `Converter` which will turn that tree into your desired query language.
![Optimade General Procedure](Optimade General Procedure.jpg)


###### Example: Optimade to MongoDB Procedure
The `Parser` class from `optimade/filter.py` will transform user input into a `Lark` tree using  [lark-parser](https://github.com/lark-parser/lark).

The `Lark` tree will then be passed into a desired `converter`, for instance, the `mongoconverter` located at `optimade/converter/mongoconverter` for transformation into your desired database query language. We have adapted our mongoconverter by using the [python query language(pql)](https://github.com/alonho/pql)

![Optimade to Mongodb Procedure](Optimade to Mongodb Procedure.jpg)


### For Developers
If you would like to add your converter, for instance, a OPTIMade to NoSQL converter, please
1. add your project in the `optimade/converter` folder,
2. add any requirements in the `requirements.txt`,
3. if you wish to have a console entry point, add the that to the `console_scripts` in the `setup.py` file
4. and run `pip install -r requirements.txt` and `pip install -e .`
