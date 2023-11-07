"""This module implements an OPTIMADE client that can be called
from Python code with

```python
from optimade.client import OptimadeClient
client = OptimadeClient()
client.get('elements HAS "Ag")
```

or from the command-line with
```shell
optimade-get --filter 'elements HAS "Ag"'
```

"""

from .client import OptimadeClient

__all__ = ("OptimadeClient",)
