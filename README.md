[![Build Status](https://travis-ci.org/materialsproject/optimade.svg?branch=master)](https://travis-ci.org/materialsproject/optimade)

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


