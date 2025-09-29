# Serve multiple OPTIMADE APIs within a single python process

One can start multiple OPTIMADE API apps within a single FastAPI instance and mount them at different subpaths.

This is enabled by the `create_app` method that allows to override parts of the configuration for each specific app, and set up separate loggers.

Here's a simple example that sets up two OPTIMADE APIs and an Index Meta-DB respectively at subpaths `/app1`, `/app2` and `/idx`.

```python
from fastapi import FastAPI

from optimade.server.config import ServerConfig
from optimade.server.create_app import create_app

parent_app = FastAPI()

base_url = "http://127.0.0.1:8000"

conf1 = ServerConfig()
conf1.base_url = f"{base_url}/app1"
conf1.mongo_database = "optimade_1"
app1 = create_app(conf1, logger_tag="app1")
parent_app.mount("/app1", app1)

conf2 = ServerConfig()
conf2.base_url = f"{base_url}/app2"
conf2.mongo_database = "optimade_2"
app2 = create_app(conf2, logger_tag="app2")
parent_app.mount("/app2", app2)

conf3 = ServerConfig()
conf3.base_url = f"{base_url}/idx"
conf3.mongo_database = "optimade_idx"
app3 = create_app(conf3, index=True, logger_tag="idx")
parent_app.mount("/idx", app3)
```

Note that `ServerConfig()` returns the configuration based on the usual sources - env variables or json file (see [Configuration](../configuration.md) section).
