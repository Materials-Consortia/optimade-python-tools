# Multiple databases

[Materials Cloud](https://materialscloud.org) uses `optimade-python-tools` as a library to provide an OPTIMADE API entry to archived computational materials studies, created with the [AiiDA](https://aiida.net) Python framework and published through their archive.
In this case, each individual study and archive entry has its own database and separate API entry.
The Python classes within the `optimade` package have been extended to make use of AiiDA and its underlying [PostgreSQL](https://postgresql.org) storage engine.

Details of this implementation can be found on GitHub at [aiidateam/aiida-optimade](https://github.com/aiidateam/aiida-optimade).
