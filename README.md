[![Build Status](https://travis-ci.org/Materials-Consortia/optimade-python-tools.svg?branch=master)](https://travis-ci.org/Materials-Consortia/optimade-python-tools)

The aim of OPTiMaDe is to develop a common API, compliant with the
[JSON API 1.0](http://jsonapi.org/format/1.0/) spec, to enable interoperability
among databases that contain calculated properties of existing and hypothetical
materials.

This repository contains a library of tools for implementing and consuming
[OPTiMaDe](http://www.optimade.org) APIs in Python.

### Status
Both the OPTiMaDe specification and this repository are **under development**.

### Links

 * [OPTiMaDe Specification](https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.md), the human-readable specification that this library is based on
 * [OpenAPI](https://github.com/OAI/OpenAPI-Specification), the machine-readable format used to specify the OPTiMaDe API in [`openapi.json`](openapi.json)
 * [Interactive documentation](https://petstore.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/openapi.json#/operation/get_structures_structures_get) generated from [`openapi.json`](openapi.json) (see also [interactive JSON editor](https://editor.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/openapi.json#/operation/get_structures_structures_get))
 * [pydantic](https://pydantic-docs.helpmanual.io/), the library used for generating the OpenAPI schema from [python models](optimade/server/models)
 * [FastAPI](https://fastapi.tiangolo.com/), the framework used for generating the reference implementation from the [`openapi.json`](openapi.json) specification.
 * [lark](https://github.com/lark-parser/lark), the library used to parse the filter language in OPTiMaDe queries

### Developing

```
# Clone this repository to your computer
git clone git@github.com:Materials-Consortia/optimade-python-tools.git
cd optimade-python-tools

# Ensure a Python>=3.7 (virtual) environment (example below using Anaconda/Miniconda)
conda create -n optimade python=3.7
conda activate optimade

# Install package and dependencies in editable mode (including "dev" requirements).
pip install -e .[dev]

# Run the tests (will install test requirements)
python setup.py test

# Install pre-commit environment (e.g., auto-formats code on `git commit`)
pre-commit install

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

When contributing to the Python code, please use the [black](https://github.com/ambv/black) code formatter.

### Getting Started with Filter Parsing and Transforming

Example use:

```python
from optimade.filterparser import Parser

p = Parser(version=(0,9,7))
tree = p.parse("nelements<3")
print(tree)
```
```
Tree(start, [Tree(expression, [Tree(term, [Tree(atom, [Tree(comparison, [Token(VALUE, 'nelements'), Token(OPERATOR, '<'), Token(VALUE, '3')])])])])])
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

There is also a [basic JSON transformer](optimade/filtertransformers/json.py)
(`optimade.filtertransformers.json.JSONTransformer`) you can use as a simple
example for developing your own transformer.
You can also use the JSON output it produces as an easy-to-parse input for a 
"transformer" in your programming language of choice.

```python
class JSONTransformer(Transformer):
    def __init__(self, compact=False):
        self.compact = compact
        super().__init__()

    def __default__(self, data, children):
        items = []
        for c in children:
            if isinstance(c, Token):
                token_repr = {
                    "@module": "lark.lexer",
                    "@class": "Token",
                    "type_": c.type,
                    "value": c.value,
                }
                if self.compact:
                    del token_repr["@module"]
                    del token_repr["@class"]
                items.append(token_repr)
            elif isinstance(c, dict):
                items.append(c)
            else:
                raise ValueError(f"Unknown type {type(c)} for tree child {c}")
        tree_repr = {
            "@module": "lark",
            "@class": "Tree",
            "data": data,
            "children": items,
        }
        if self.compact:
            del tree_repr["@module"]
            del tree_repr["@class"]
        return tree_repr
```

#### Developing New Filter Transformers
If you would like to add a new transformer, please add
1. a module (.py file) in the `optimade/filtertransformers` folder,
2. any additional Python requirements in `setup.py` and `requirements.txt`,
3. tests in `optimade/filtertransformers/tests`.
