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

### Developing

```
# Clone this repository to your computer
git clone git@github.com:Materials-Consortia/optimade-python-tools.git
cd optimade-python-tools

# Ensure a Python>=3.6 (virtual) environment (example below using Anaconda/Miniconda)
conda create -n optimade python=3.6
conda activate optimade

# Install package and requirements in editable mode.
pip install -e .

# Optional: Install MongoDB (and set `USE_REAL_MONGO = yes` in optimade/server/congig.ini)
# Below method installs in conda environment and
# - starts server in background
# - ensures and uses ~/dbdata directory to store data
conda install -c anaconda mongodb
mkdir -p ~/dbdata && mongod --dbpath ~/dbdata --syslog --fork 

# Start a development server (auto-reload on file changes at http://localhost:5000
# You can also execute ./run.sh
uvicorn optimade.server.main:app --reload --port 5000

# View auto-generated docs
open http://localhost:5000/docs
# View Open API Schema
open http://localhost:5000/openapi.json
```

### Getting Started with Filter Parsing and Transforming

Example use:

```python
from optimade.filterparser import Parser

p = Parser(version=(0,9,7))
tree = p.parse("nelements<3")
print(tree)
```
```
Tree(start, [Token(KEYWORD, 'filter='), Tree(expression, [Tree(term, [Tree(atom, [Tree(comparison, [Token(VALUE, 'a'), Token(OPERATOR, '<'), Token(VALUE, '3')])])])])])
```
```python
print(tree.pretty())
```
```
start
  expression
    term
      atom
        comparison
          nelements
          <
          3
```
```python
tree = p.parse('_mp_bandgap > 5.0 AND _cod_molecular_weight < 350')
print(tree.pretty())
```
```
start
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
# Assumes graphviz installed on system (e.g. `conda install -c anaconda graphviz`) and `pip install pydot`
from lark.tree import pydot__tree_to_png

pydot__tree_to_png(tree, "exampletree.png")
```
![example tree](exampletree.png)

#### Flow for Parsing User-Supplied Filter and Converting to Backend Query

`optimade.filterparser.Parser` will take user input to generate a `lark.Tree` and feed that to a `lark.Transformer`
(for example, `optimade.filtertransformers.mongo.MongoTransformer`), which will turn that tree into something useful
to your backend (for example, a MongoDB query `dict`.)

```python
# Example: Converting to MongoDB Query Syntax
from optimade.filtertransformers.mongo import MongoTransformer

transformer = MongoTransformer()

tree = p.parse('_mp_bandgap > 5.0 AND _cod_molecular_weight < 350')
query = transformer.transform(tree)
print(query)
```
```
{'$and': [{'_mp_bandgap': {'$gt': 5.0}}, {'_cod_molecular_weight': {'$lt': 350.0}}]}
```

#### Developing New Filter Transformers
If you would like to add a new transformer, please add
1. a module (.py file) in the `optimade/filtertransformers` folder,
2. any additional Python requirements in `setup.py` and `requirements.txt`,
3. tests in `optimade/filtertransformers/tests`.
