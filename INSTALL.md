# Installation

This package can be installed from PyPI, or by cloning the repository, depending on your use-case.

1. To use the `optimade` Python package as a library, (e.g., using the models for validation, parsing filters with the grammar, or using the command-line tool `optimade-validator` tool), it is recommended that you install the latest release of the package from PyPI with `pip install optimade`. If you also want to use the OPTIMADE client to query OPTIMADE APIs, you should install with the additional dependencies: `pip install 'optimade[http-client]'`.
2. If you want to run, use or modify the reference server implementation, then it is recommended that you clone this repository and install it from your local files (with `pip install .`, or `pip install -e .` for an editable installation).
   As an alternative, you can run the `optimade` container image (see the [Container image](#container-image) section below).

## The index meta-database

This package may be used to setup and run an [OPTIMADE index meta-database](https://github.com/Materials-Consortia/OPTIMADE/blob/develop/optimade.rst#index-meta-database).
Clone this repository and install the package locally with `pip install -e .[server]`.

!!! info
    To avoid installing anything locally and instead use the docker image, please see the section [Container image](#container-image) below.

There is a built-in index meta-database set up to populate a `mongomock` in-memory database with resources from a static `json` file containing the `child` resources you, as a database provider, want to serve under this index meta-database.
The location of that `json` file is controllable using the `index_links_path` property of the configuration or setting via the environment variable `optimade_index_links_path`.

Running the index meta-database is then as simple as writing `./run.sh index` in a terminal from the root of this package.
You can find it at the base URL: <http://localhost:5001/v1>.

Here is an example of how it may look to start your server:

```sh
export OPTIMADE_CONFIG_FILE=/home/optimade_server/config.json
./path/to/optimade/run.sh index
```

## Full development installation

The dependencies of this package can be found in `setup.py` with their latest supported versions.
By default, a minimal set of requirements are installed to work with the filter language and the `pydantic` models.
After cloning the repository, the install mode `server` (i.e. `pip install .[server]`) is sufficient to run a `uvicorn` server using the `mongomock` backend (or MongoDB with `pymongo`, if present).
The suite of development and testing tools are installed with via the install modes `dev` and `testing`.
There are additionally two backend-specific install modes, `elastic` and `mongo`, as well as the `all` mode, which installs all dependencies.
All contributed Python code, must use the [black](https://github.com/ambv/black) code formatter, and must pass the [flake8](http://flake8.pycqa.org/en/latest/) linter that is run automatically on all PRs.

```sh
# Clone this repository to your computer
git clone --recursive git@github.com:Materials-Consortia/optimade-python-tools.git
cd optimade-python-tools

# Ensure a Python>=3.8 (virtual) environment (example below using Anaconda/Miniconda)
conda create -n optimade python=3.10
conda activate optimade

# Install package and dependencies in editable mode (including "dev" requirements).
pip install -e ".[dev]"

# Optional: Retrieve the list of OPTIMADE providers. (Without this submodule, some of the tests will fail because "providers.json" cannot be found.)
git submodule update --init

# Run the tests with pytest
py.test

# Install pre-commit environment (e.g., auto-formats code on `git commit`)
pre-commit install

# Optional: Install MongoDB (and set `database_backend = mongodb`)
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

## Testing specific backends

In order to run the test suite for a specific backend, the
`OPTIMADE_DATABASE_BACKEND` [environment variable (or config
option)](https://www.optimade.org/optimade-python-tools/latest/configuration/) can be
set to one of `'mongodb'`, `'mongomock'` or `'elastic'` (see
[`ServerConfig.database_backend`][optimade.server.config.ServerConfig.database_backend]).
Tests for the two "real" database backends, MongoDB and Elasticsearch, require a writable, temporary database to be accessible.

The easiest way to deploy these databases and run the tests is with Docker, as shown below.
[Docker installation instructions](https://docs.docker.com/engine/install/) will depend on your system; on Linux, the `docker` commands below may need to be prepended with `sudo`, depending on your distribution.
These commands should be run from a local optimade-python-tools directory.

The following command starts a local Elasticsearch v7 instance, runs the test suite, then stops and deletes the containers (required as the tests insert some data):

```shell
docker run -d --name elasticsearch_test -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:7.17.7 \
&& sleep 20 \
&& OPTIMADE_DATABASE_BACKEND="elastic" py.test; \
docker container stop elasticsearch_test; docker container rm elasticsearch_test
```

The following command starts a local MongoDB instance, runs the test suite, then stops and deletes the containers:

```shell
docker run -d --name mongo_test -p 27017:27017 -d mongo:4.4.6 \
&& OPTIMADE_DATABASE_BACKEND="mongodb" py.test; \
docker container stop mongo_test; docker container rm mongo_test
```

## Container image

### Retrieve the image

The [`optimade` container image](https://github.com/Materials-Consortia/optimade-python-tools/pkgs/container/optimade) is available from the [GitHub Container registry](https://ghcr.io).
To pull the latest version using [Docker](https://docs.docker.com/) run the following:

```shell
docker pull ghcr.io/materials-consortia/optimade:latest
```

!!! note
    The tag, `:latest`, can be left out, as the `latest` version will be pulled by default.

If you'd like to pull a specific version, this can be done by replacing `latest` in the command above with the version of choice, e.g., `0.17.1`.
To see which versions are available, please go [here](https://github.com/Materials-Consortia/optimade-python-tools/pkgs/container/optimade/versions).

You can also install the `develop` version.
This is an image built from the latest commit on the `main` branch and should never be used for production.

### Run a container

When starting a container from the image there are a few choices.
It is possible to run either a standard OPTIMADE server, or an [index meta-database](https://github.com/Materials-Consortia/OPTIMADE/blob/master/optimade.rst#index-meta-database) server from this image.
Note, these servers can be run in separate containers at the same time.
The key is setting the environment variable `MAIN`.

| **MAIN** | **Result** |
|:---:|:--- |
| `main` | Standard OPTIMADE server. |
| `main_index` | Index meta-database OPTIMADE server. |

Using Docker, the following command will run a container from the image:

```shell
# rm will remove container when it exits.
# detach will run the server in the background.
# publish will run the server from the host port 8080.
# name will give the container a handy name for referencing later.
docker run \
    --rm \
    --detach \
    --publish 8080:5000 \
    --env MAIN=main \
    --name my-optimade \
    ghcr.io/materials-consortia/optimade:latest
```

The server should now be available at [localhost:8080](http://localhost:8080).
