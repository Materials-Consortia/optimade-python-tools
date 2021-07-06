# Filter parsing and transforming

One of the aims of this package is to integrate with existing databases and APIs, and as such your particular backend may not have a supported filter transformer.
This guide will briefly outline how to parse OPTIMADE filter strings into database or API-specific queries.

## Parsing OPTIMADE filter strings

The [`LarkParser`][optimade.filterparser.LarkParser] class will take an OPTIMADE filter string, supplied by the user, and parse it into a `lark.Tree` instance.

Example use:

```python
from optimade.filterparser import LarkParser

p = LarkParser(version=(1, 0, 0))
tree = p.parse("nelements<3")
print(tree)
```

```shell
Tree('filter', [Tree('expression', [Tree('expression_clause', [Tree('expression_phrase', [Tree('comparison', [Tree('property_first_comparison', [Tree('property', [Token('IDENTIFIER', 'nelements')]), Tree('value_op_rhs', [Token('OPERATOR', '<'), Tree('value', [Tree('number', [Token('SIGNED_INT', '3')])])])])])])])])])
```

```python
print(tree.pretty())
```

```shell
filter
  expression
    expression_clause
      expression_phrase
        comparison
          property_first_comparison
            property	nelements
            value_op_rhs
              <
              value
                number	3
```

```python
tree = p.parse('_mp_bandgap > 5.0 AND _cod_molecular_weight < 350')
print(tree.pretty())
```

```shell
filter
  expression
    expression_clause
      expression_phrase
        comparison
          property_first_comparison
            property	_mp_bandgap
            value_op_rhs
              >
              value
                number	5.0
      expression_phrase
        comparison
          property_first_comparison
            property	_cod_molecular_weight
            value_op_rhs
              <
              value
                number	350
```

## Flow for parsing a user-supplied filter and converting to a backend query

After the [`LarkParser`][optimade.filterparser.LarkParser] has turned the filter string into a `lark.Tree`, it is fed to a `lark.Transformer` instance, which transforms the 'lark.Tree' into a backend-specific representation of the query.
For example, [`MongoTransformer`][optimade.filtertransformers.mongo.MongoTransformer] will turn the tree into something useful for a MongoDB backend:

```python
# Example: Converting to MongoDB Query Syntax
from optimade.filtertransformers.mongo import MongoTransformer

transformer = MongoTransformer()

tree = p.parse('_mp_bandgap > 5.0 AND _cod_molecular_weight < 350')
query = transformer.transform(tree)
print(query)
```

```json
{
    "$and": [
        {"_mp_bandgap": {"$gt": 5.0}},
        {"_cod_molecular_weight": {"$lt": 350.0}}
    ]
}
```


## Developing new filter transformers

In order to support a new backend, you will need to create a new filter transformer that inherits from the [`BaseTransformer`][optimade.filtertransformers.base_transformer.BaseTransformer].
This transformer will need to override the methods that match the particular grammatical constructs in the Lark grammar in order to construct a query.
Two examples can be found within `optimade-python-tools`, one for MongoDB ([`MongoTransformer`][optimade.filtertransformers.mongo.MongoTransformer]) and one for Elasticsearch ([`ElasticTransformer`][optimade.filtertransformers.elasticsearch.ElasticTransformer]).

In some cases, you may also need to extend the base [`EntryCollection`][optimade.server.entry_collections.entry_collections.EntryCollection], the class that receives the transformed filter as an argument to its private `._run_db_query()` method.
This class handles the connections to the underlying database, formatting of the response in an OPTIMADE format, and other API features such as sorting and pagination.
Again, the examples for MongoDB ([`MongoCollection`][optimade.server.entry_collections.mongo.MongoCollection]) and Elasticsearch ([`ElasticCollection`][optimade.server.entry_collections.elasticsearch.ElasticCollection]) should be helpful.

If you would like to contribute your new filter transformer back to the package, please raise an issue to signal your intent (in case someone else is already working on this).
Adding a transformer requires the following:

1. A new submodule (`.py` file) in the `optimade/filtertransformers` folder containing an implementation of the transformer object that extends `optimade.filtertransformers.base_transformer.BaseTransformer`.
2. Any additional Python requirements must be optional and provided as a separate "`extra_requires`" entry in `setup.py` and in the `requirements.txt` file.
3. Tests in `optimade/filtertransformers/tests` that are skipped if the required packages fail to import.
