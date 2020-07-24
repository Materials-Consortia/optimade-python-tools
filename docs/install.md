# Installation

## The index meta-database

This package may be used to setup and run an [OPTIMADE index meta-database](https://github.com/Materials-Consortia/OPTIMADE/blob/develop/optimade.rst#index-meta-database).
Install the package via `pip install optimade[server]`.

This python OPTIMADE implementation can be configured in two ways:
First, the server can be configured via environment variables prefixed with `optimade_` and the corresponding variable names in `ServerConfig` in the [`config.py` file][optimade.server.config]. These take precedence. These environment variables are not case sensitive, so both `OPTIMADE_CONFIG_FILE` and `optimade_config_file` are valid.
Second, and the preferred method of configuring the server, is to use a [JSON file](static/example_config.json) with the bulk of the configuration and setting the `optimade_config_file` environment variable to point to the absolute location of this JSON file. By default this points to `~/.optimade.json` which can also be used to store the configuration if you don't want to set `optimade_config_file`.

For any configuration parameters not set by the above two, the defaults in built into `ServerConfig` in `optimade.server.config` will be used.

??? note "Example config file"
    ```json
    --8<-- "example_config.json"
    ```

There is a built-in index meta-database set up to populate a `mongomock` in-memory database with resources from a static `json` file containing the `child` resources you, as a database provider, want to serve under this index meta-database. The location of that `json` file is controllable using the `index_links_path` property of the configuration or setting via the environment variable `optimade_index_links_path`.

Running the index meta-database is then as simple as writing `./run.sh index` in a terminal from the root of this package.
You can find it at the base URL: <http://localhost:5001/v1>.

Here is an example of how it may look to start your server:

```sh
:~$ export OPTIMADE_CONFIG_FILE=/home/optimade_server/config.json
:~$ ./path/to/optimade/run.sh index
```

## Full development installation

The dependencies of this package can be found in `setup.py` with their latest supported versions.
By default, a minimal set of requirements are installed to work with the filter language and the `pydantic` models.
The install mode `server` (i.e. `pip install .[server]`) is sufficient to run a `uvicorn` server using the `mongomock` backend (or MongoDB with `pymongo`, if present).
The suite of development and testing tools are installed with via the install modes `dev` and `testing`.
There are additionally three backend-specific install modes, `django`, `elastic` and `mongo`, as well as the `all` mode, which installs all dependencies.
All contributed Python code, must use the [black](https://github.com/ambv/black) code formatter, and must pass the [flake8](http://flake8.pycqa.org/en/latest/) linter that is run automatically on all PRs.

```sh
# Clone this repository to your computer
git clone git@github.com:Materials-Consortia/optimade-python-tools.git
cd optimade-python-tools

# Ensure a Python>=3.7 (virtual) environment (example below using Anaconda/Miniconda)
conda create -n optimade python=3.7
conda activate optimade

# Install package and dependencies in editable mode (including "dev" requirements).
pip install -e ".[dev]"

# Run the tests with pytest
py.test

# Install pre-commit environment (e.g., auto-formats code on `git commit`)
pre-commit install

# Optional: Install MongoDB (and set `use_real_mongo = true`)
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

will run the index meta-database server at <http://localhost:5001/v1>.
