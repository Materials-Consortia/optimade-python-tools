# Customize OPTIMADE python tools and integrate with an existing web application

OPTIMADE python tools (OPT) can be run as a standalone web application that serves the OPTIMADE
API based on a pre-configured mongodb backend. In this document, we are going to use OTP
differently and use it to add an OPTIMADE API implementation to an existing application with
an existing elasticsearch as database.

Lets assume, we already have a *fastapi* application that runs an unrelated web service,
and that we use an elasticsearch backend that contains all structure data, but not necessarily
into a form that OPTIMADE python tools expect.

## Providing a OPT configuration

OPT reads its configuration from a file. It uses the `OPTIMADE_CONFIG_FILE` environment
variable (or a default path) to find the config file. If you run OPT from another application,
you might want to provide this config file as part of source code and not via environment
variables. Let's say you have a file `optimade_config.json` as part of the Python
module that you use to create your OPT

Before importing any OPT packages, you can set the `OPTIMADE_CONFIG_FILE` environment
variable to link OPT to your config file:

```python
import os
import sys

os.environ['OPTIMADE_CONFIG_FILE'] = os.path.join(os.path.dirname(__file__), 'optimade_config.json')
```

## Customize the *EntryCollection* implementation

Let's assume that your elasticsearch backend stores structure data different enough that you
need to provide your own custom implementation. The following code customized the used
`EntryCollection` class for structures, while keeping the default *mongomock* implementation
for all other entry types.

```python
from optimade.server.routers import structures

structures.structures_coll = MyElasticsearchStructureCollection()
```

You can imagine that `MyElasticsearchStructureCollection` either sub-classes the
default OTP elasticsearch implementation or sub-classes `EntryCollection` depending on
how deeply you need to customize the default OTP behavior.

## Mounting the OPTIMADE python tools *fastapi* app into an existing *fastapi* app.

Let's you assume you have an existing *fastapi* app `my_app`. It already adds a few routers
under certain path prefixes and now you want to add the OTP API implementation under the
path prefix `/optimade`. First, you have to set the `root_path` in the OTP configuration.
Now the OTP app expects all requests being prefixed with `/optimade`. Of course, you
can also set the value in your OTP config file. Second, you simply
mount the optimade app into `my_app`. See also the fastapi documentation on
[sub-applications](https://fastapi.tiangolo.com/advanced/sub-applications/):

```python
from optimade.server.config import CONFIG
CONFIG.root_path = "/optimade"

from optimade.server import main as optimade

optimade.add_major_version_base_url(optimade.app)
my_app.mount("/optimade", optimade.app)
```

If you run `my_app`, it will still server all its routes as before and in addition it will
also serve all OTP provided routes under `/optimade/*` and `/optimade/v1/*`.