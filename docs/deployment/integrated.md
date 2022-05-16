# Integrate OPTIMADE with an existing web application

The `optimade` package can be used to create a standalone web application that serves the OPTIMADE API based on a pre-configured MongoDB backend.
In this document, we are going to use `optimade` differently and use it to add an OPTIMADE API implementation alongside an existing API that employs an Elasticsearch storage layer.

Let's assume we already have a *FastAPI* application that runs an unrelated web service, and that we use an Elasticsearch backend that contains all structure data, but not necessarily in a form that OPTIMADE expects.

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

## Mounting the OPTIMADE Python tools *FastAPI* app into an existing *FastAPI* app

Let's assume you have an existing *FastAPI* app `my_app`.
It already implements a few routers under certain path prefixes, and now you want to add an OPTIMADE implementation under the path prefix `/optimade`.

First, you have to set the `root_path` in the `optimade` configuration, so that the app expects all requests to be prefixed with `/optimade`.

Second, you simply mount the `optimade` app into your existing app `my_app`:

```python
from optimade.server.config import CONFIG

CONFIG.root_path = "/optimade"

from optimade.server import main as optimade

optimade.add_major_version_base_url(optimade.app)
my_app.mount("/optimade", optimade.app)
```

!!! tip
    In the example above, we imported `CONFIG` before `main` so that our config was loaded before app creation.
    To avoid the need for this, the `root_path` can be set in your JSON config file, passed as an environment variable, or declared in a custom Python module (see [Configuration](../configuration.md)).

See also the *FastAPI* documentation on [sub-applications](https://fastapi.tiangolo.com/advanced/sub-applications/).

Now, if you run `my_app`, it will still serve all its routers as before and in addition it will also serve all OPTIMADE routes under `/optimade/` and the versioned URLs `/optimade/v1/`.
