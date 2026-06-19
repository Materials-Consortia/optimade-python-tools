# NOMAD integration

Goal: Provide a service which can provide a fully compliant OPTIMADE interface to NOMAD data.
It behaves as a service and translates OPTIMADE queries to NOMAD graphs queries and handles all the mapping between property names.

## Minimal Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[server]"
./runs.sh
```

- http://localhost:5000/
- http://localhost:5000/v1/extensions/docs