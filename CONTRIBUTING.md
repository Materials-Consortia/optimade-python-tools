# Contribute to `optimade-python-tools`

The [Materials Consortia](https://github.com/Materials-Consortia) is very open to contributions to this package.

This may be anything from simple feedback and raising [new issues](https://github.com/Materials-Consortia/optimade-python-tools/issues/new) to creating [new PRs](https://github.com/Materials-Consortia/optimade-python-tools/compare).

We have below recommendations for setting up an environment in which one may develop the package further.

## Development installation

The dependencies of this package can be found in `setup.py` with their latest supported versions.
By default, a minimal set of requirements are installed to work with the filter language and the `pydantic` models.
The install mode `server` (i.e. `pip install .[server]`) is sufficient to run a `uvicorn` server using the `mongomock` backend (or MongoDB with `pymongo`, if present).
The suite of development and testing tools are installed with via the install modes `dev` and `testing`.
There are additionally three backend-specific install modes, `django`, `elastic` and `mongo`, as well as the `all` mode, which installs all dependencies.
All contributed Python code, must use the [black](https://github.com/ambv/black) code formatter, and must pass the [flake8](http://flake8.pycqa.org/en/latest/) linter that is run automatically on all PRs.

```shell
# Clone this repository to your computer
git clone git@github.com:Materials-Consortia/optimade-python-tools.git
cd optimade-python-tools

# Ensure a Python>=3.7 (virtual) environment (example below using Anaconda/Miniconda)
conda create -n optimade python=3.7
conda activate optimade

# Install package and dependencies in editable mode (including "dev" requirements).
pip install -e .[dev]

# Run the tests with pytest
py.test

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

When developing, you can run both the server and an index meta-database server at the same time (from two separate terminals).
Running the following:

```shell
./run.sh index
# or
uvicorn optimade.server.main_index:app --reload --port 5001
```

Will run the index meta-database server at <http://localhost:5001/index/optimade>.

## Getting Started with Filter Parsing and Transforming

Example use:

```python
from optimade.filterparser import Parser

p = Parser(version=(0,9,7))
tree = p.parse("nelements<3")
print(tree)
```

```shell
Tree(start, [Tree(expression, [Tree(term, [Tree(atom, [Tree(comparison, [Token(VALUE, 'nelements'), Token(OPERATOR, '<'), Token(VALUE, '3')])])])])])
```

```python
print(tree.pretty())
```

```shell
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

```shell
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

### Flow for Parsing User-Supplied Filter and Converting to Backend Query

`optimade.filterparser.Parser` will take user input to generate a `lark.Tree` and feed that to a `lark.Transformer`.
E.g., `optimade.filtertransformers.mongo.MongoTransformer` will turn the tree into something useful for your MondoDB backend:

```python
# Example: Converting to MongoDB Query Syntax
from optimade.filtertransformers.mongo import MongoTransformer

transformer = MongoTransformer()

tree = p.parse('_mp_bandgap > 5.0 AND _cod_molecular_weight < 350')
query = transformer.transform(tree)
print(query)
```

```python
{'$and': [{'_mp_bandgap': {'$gt': 5.0}}, {'_cod_molecular_weight': {'$lt': 350.0}}]}
```

There is also a [basic JSON transformer](optimade/filtertransformers/json.py) (`optimade.filtertransformers.json.JSONTransformer`) you can use as a simple example for developing your own transformer.
You can also use the JSON output it produces as an easy-to-parse input for a "transformer" in your programming language of choice.

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

### Developing New Filter Transformers

If you would like to add a new transformer, please add:

1. A module (.py file) in the `optimade/filtertransformers` folder.
2. Any additional Python requirements must be optional and provided as a separate "`extra_requires`" entry in `setup.py`.
3. Tests in `optimade/filtertransformers/tests` that are skipped if the required packages fail to import.

For examples, please check out existing filter transformers.
