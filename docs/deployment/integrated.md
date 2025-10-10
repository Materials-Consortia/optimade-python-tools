# Integrate OPTIMADE with an existing web application

The `optimade` package can be used to create a standalone web application that serves the OPTIMADE API based on a pre-configured MongoDB backend.
In this document, we are going to use `optimade` differently and use it to add an OPTIMADE API implementation alongside an existing API that employs an Elasticsearch storage layer.

Let's assume we already have a _FastAPI_ application that runs an unrelated web service, and that we use an Elasticsearch backend that contains all structure data, but not necessarily in a form that OPTIMADE expects.

## Providing the `optimade` configuration

`optimade` can read its configuration from a JSON file.
It uses the `OPTIMADE_CONFIG_FILE` environment variable (or a default path) to find the config file.
If you run `optimade` code inside another application, you might want to provide this config file as part of the source code and not via environment variables.
Let's say you have a file `optimade_config.json` as part of the Python module that you use to create your OPTIMADE API.

!!! tip
You can find more detailed information about configuring the `optimade` server in the [Configuration](../configuration.md) section.

Before importing any `optimade` modules, you can set the `OPTIMADE_CONFIG_FILE` environment variable to refer to your config file:

```python
import os
from pathlib import Path

os.environ['OPTIMADE_CONFIG_FILE'] = str(Path(__file__).parent / "optimade_config.json")
```

## Customize the [`EntryCollection`][optimade.server.entry_collections.entry_collections.EntryCollection] implementation

Let's assume that your Elasticsearch backend stores structure data in a different enough manner that you need to provide your own custom implementation.
The following code customizes the [`EntryCollection`][optimade.server.entry_collections.entry_collections.EntryCollection] class for structures, whilst keeping the default MongoDB-based implementation (using [`MongoCollection`][optimade.server.entry_collections.mongo.MongoCollection]) for all other entry types.

```python
from optimade.server.routers import structures

structures.structures_coll = MyElasticsearchStructureCollection()
```

You can imagine that `MyElasticsearchStructureCollection` either sub-classes the default `optimade` Elasticsearch implementation ([`ElasticsearchCollection`][optimade.server.entry_collections.elasticsearch.ElasticCollection]) or sub-classes [`EntryCollection`][optimade.server.entry_collections.entry_collections.EntryCollection], depending on how deeply you need to customize the default `optimade` behavior.

## Mounting the OPTIMADE Python tools _FastAPI_ app into an existing _FastAPI_ app

Let's assume you have an existing _FastAPI_ app `my_app`.
It already implements a few routers under certain path prefixes, and now you want to add an OPTIMADE implementation under the path prefix `/optimade`.

The primary thing to modify is the `base_url` to match the new subpath. The easiest is to just update your configuration file or env parameters.

Then one can just simply do the following:

```python
from optimade.server.main import main as optimade

my_app.mount("/optimade", optimade.app)
```

See also the _FastAPI_ documentation on [sub-applications](https://fastapi.tiangolo.com/advanced/sub-applications/).

Now, if you run `my_app`, it will still serve all its routers as before and in addition it will also serve all OPTIMADE routes under `/optimade/`.
