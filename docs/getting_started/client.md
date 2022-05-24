# Using the OPTIMADE client

This package includes a Python client that can be used to query multiple OPTIMADE APIs simultaneously.
The client can be used from the command-line (`optimade-get`), or called in Python code.

The client requires some extra dependencies that can be installed with the PyPI package with

```shell
pip install optimade[http_client]
```
or from a local copy of the repository with
```shell
pip install -e .[http_client]
```

By default, the client will query all OPTIMADE API URLs that it can find via the [Providers list](https://providers.optimade.org):


=== "Command line"
    ```shell
    optimade-get --filter 'elements HAS "Ag"'
    ```

=== "Python"
    ```python
    from optimade.client import OptimadeClient
    client = OptimadeClient()
    results = client.get()
    ```

We can refine the search by manually specifying some URLs:

=== "Command line"
    ```shell
    optimade-get https://optimade.herokuapp.com https://optimade.odbx.science
    ```

=== "Python"
    ```python
    from optimade.client import OptimadeClient
    client = OptimadeClient(
        base_urls=["https://optimade.herokuapp.com", "https://optimade.odbx.science"]
    )
    client.get()
    ```

By default, the command-line interface will use an example filter, and the Python interface will use an empty filter.
You can specify your desired filter as follows (note the quotation marks):

=== "Command line"
    ```shell
    optimade-get --filter 'elements HAS "Ag" AND nsites < 2'
    ```

=== "Python"
    ```python
    from optimade.client import OptimadeClient
    client = OptimadeClient()
    client.get('elements HAS "Ag" AND nsites < 2')
    ```

The filter will be validated against the `optimade-python-tools` reference grammar before it is sent to the underlying servers.

## Accessing the results

At the command-line, the results of the query will be printed to `stdout` to be redirected to a file or piped into another program.
For example:

```shell
optimade-get --filter 'nsites = 1' https://optimade.herokuapp.com
```

has the followng (truncated) output:

```json
{  
  // The endpoint that was queried
  "structures": {  
    // The filter applied to that endpointk
    "nsites = 1": {  
      // The base URL of the OPTIMADE API
      "https://optimade.herokuapp.com": {  
        // The OPTIMADE API response as if called with an infinite `page_limit`
        "data": [  
          {
            "id": "mpf_1",
            "type": "structures",
            "attributes": {
                ...
            }
            "relationships": {
                ...
            }
          },
          ...
        ],
        "errors": [],
        "links": {
          "next": null,
          "prev": null
        },
        "included": [
            ...
        ],
        "meta": {
            ...
        }
      }
    }
  }
}
```

The response is broken down by queried endpoint, filter and then base URL so that the query URL can be easily reconstructed.
This is the same format as the cached results of the Python client:

```python
from optimade.client import OptimadeClient
import json
client = OptimadeClient(base_urls="https://optimade.herokuapp.com")
client.get('nsites = 1')
client.get('nsites = 2')
print(json.dumps(client.all_results, indent=2))
```

will return a dictionary with top-level keys:
```json
{
    "structures": {
        "nsites = 1": {
            "https://optimade.herokuapp.com": {...}
        },
        "nsites = 2": {
            "https://optimade.herokuapp.com": {...}
        }
    }
}
```

For a given session, this cache can be written and reloaded into an OPTIMADE client object to avoid needing to repeat queries.

!!! info
    In a future release, this cache will be automatically restored from disk and will obey defined cache lifetimes.

### Counting entries and limiting results

Querying all OPTIMADE APIs without limiting the number of entries can result in a lot of data.
The client will limit the number of results returned per database to the value of `max_results_per_provider` (defaults: 1000 for Python, 100 for CLI).
This limit will be enforced up to a difference of the default page limit for the underlying OPTIMADE API (which is used everywhere).
This parameter can be controlled via the `--max-results-per-provider 10` at the CLI, or as an argument to `OptimadeClient(max_results_per_provider=10)`.

Downloading all the results for a given query can require hundreds or thousands of requests, depending on the number of results and the database's page limit.
It is possible to just count the number of results before downloading the entries themselves, which only requires 1 request per database.
This is achieved via the `--count` flag in the CLI, or the `.count()` method in the Python interface.
We can use this to repeat the queries from the [OPTIMADE paper](https://doi.org/10.1038/s41597-021-00974-z):

=== "Command line"
    ```shell
    optimade-get \
        --count \
        --filter 'elements HAS ANY "C", "Si", "Ge", "Sn", "Pb"' \
        --filter 'elements HAS ANY "C", "Si", "Ge", "Sn", "Pb" AND nelements=2' \
        --filter 'elements HAS ANY "C", "Si", "Ge", "Sn" AND NOT elements HAS "Pb" AND elements LENGTH 3'
    ```

=== "Python"
    ```python
    from optimade.client import OptimadeClient
    client = OptimadeClient()
    filters = [
        'elements HAS ANY "C", "Si", "Ge", "Sn", "Pb"',
        'elements HAS ANY "C", "Si", "Ge", "Sn", "Pb" AND nelements=2'
        'elements HAS ANY "C", "Si", "Ge", "Sn" AND NOT elements HAS "Pb" AND elements LENGTH 3'
    ]
    for f in filters:
        client.count(f)
    ```

which, at the timing of writing, yields the results:

```json
{
  "structures": {
    "elements HAS ANY \"C\", \"Si\", \"Ge\", \"Sn\", \"Pb\"": {
      "http://aflow.org/API/optimade/": null,
      "https://www.crystallography.net/cod/optimade": 436062,
      "https://aiida.materialscloud.org/sssplibrary/optimade": 487,
      "https://aiida.materialscloud.org/2dstructures/optimade": 1427,
      "https://aiida.materialscloud.org/2dtopo/optimade": 0,
      "https://aiida.materialscloud.org/tc-applicability/optimade": 3719,
      "https://aiida.materialscloud.org/3dd/optimade": null,
      "https://aiida.materialscloud.org/mc3d-structures/optimade": 9592,
      "https://aiida.materialscloud.org/autowannier/optimade": 1093,
      "https://aiida.materialscloud.org/curated-cofs/optimade": 4395,
      "https://aiida.materialscloud.org/stoceriaitf/optimade": 0,
      "https://aiida.materialscloud.org/pyrene-mofs/optimade": 348,
      "https://aiida.materialscloud.org/tin-antimony-sulfoiodide/optimade": 503,
      "https://optimade.materialsproject.org": 30351,
      "https://api.mpds.io": null,
      "https://nomad-lab.eu/prod/rae/optimade/": 4451056,
      "https://optimade.odbx.science": 55,
      "http://optimade.openmaterialsdb.se": 58718,
      "http://oqmd.org/optimade/": null,
      "https://jarvis.nist.gov/optimade/jarvisdft": null,
      "https://www.crystallography.net/tcod/optimade": 2632,
      "http://optimade.2dmatpedia.org": 1172
    },
    "elements HAS ANY \"C\", \"Si\", \"Ge\", \"Sn\", \"Pb\" AND nelements=2": {
      "http://aflow.org/API/optimade/": 63011,
      "https://www.crystallography.net/cod/optimade": 3968,
      "https://aiida.materialscloud.org/sssplibrary/optimade": 2,
      "https://aiida.materialscloud.org/2dstructures/optimade": 779,
      "https://aiida.materialscloud.org/2dtopo/optimade": 0,
      "https://aiida.materialscloud.org/tc-applicability/optimade": 334,
      "https://aiida.materialscloud.org/3dd/optimade": null,
      "https://aiida.materialscloud.org/mc3d-structures/optimade": 1566,
      "https://aiida.materialscloud.org/autowannier/optimade": 276,
      "https://aiida.materialscloud.org/curated-cofs/optimade": 24,
      "https://aiida.materialscloud.org/stoceriaitf/optimade": 0,
      "https://aiida.materialscloud.org/pyrene-mofs/optimade": 0,
      "https://aiida.materialscloud.org/tin-antimony-sulfoiodide/optimade": 0,
      "https://optimade.materialsproject.org": 3728,
      "https://api.mpds.io": null,
      "https://nomad-lab.eu/prod/rae/optimade/": 587923,
      "https://optimade.odbx.science": 54,
      "http://optimade.openmaterialsdb.se": 690,
      "http://oqmd.org/optimade/": null,
      "https://jarvis.nist.gov/optimade/jarvisdft": null,
      "https://www.crystallography.net/tcod/optimade": 296,
      "http://optimade.2dmatpedia.org": 739
    },
    "elements HAS ANY \"C\", \"Si\", \"Ge\", \"Sn\" AND NOT elements HAS \"Pb\" AND elements LENGTH 3": {
      "http://aflow.org/API/optimade/": null,
      "https://www.crystallography.net/cod/optimade": 33776,
      "https://aiida.materialscloud.org/sssplibrary/optimade": 0,
      "https://aiida.materialscloud.org/2dstructures/optimade": 378,
      "https://aiida.materialscloud.org/2dtopo/optimade": 0,
      "https://aiida.materialscloud.org/tc-applicability/optimade": 144,
      "https://aiida.materialscloud.org/3dd/optimade": null,
      "https://aiida.materialscloud.org/mc3d-structures/optimade": 4398,
      "https://aiida.materialscloud.org/autowannier/optimade": 74,
      "https://aiida.materialscloud.org/curated-cofs/optimade": 1447,
      "https://aiida.materialscloud.org/stoceriaitf/optimade": 0,
      "https://aiida.materialscloud.org/pyrene-mofs/optimade": 0,
      "https://aiida.materialscloud.org/tin-antimony-sulfoiodide/optimade": 0,
      "https://optimade.materialsproject.org": 11559,
      "https://api.mpds.io": null,
      "https://nomad-lab.eu/prod/rae/optimade/": 2092989,
      "https://optimade.odbx.science": 0,
      "http://optimade.openmaterialsdb.se": 7428,
      "http://oqmd.org/optimade/": null,
      "https://jarvis.nist.gov/optimade/jarvisdft": null,
      "https://www.crystallography.net/tcod/optimade": 661,
      "http://optimade.2dmatpedia.org": 255
    }
  }
}
```
