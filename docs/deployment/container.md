# Run in a container (Docker)
<!-- markdownlint-disable MD046 -->

## Retrieve the container image

Retrieving the container image is explained in the [installation instructions](../INSTALL.md#retrieve-the-image).
In short, using [Docker](https://docs.docker.com) you can run:

```shell
docker pull ghcr.io/materials-consortia/optimade
```

A general overview on running a container is also given in the [installations instructions](../INSTALL.md#run-a-container).

## Prepare the container and configure the server

!!! tip
    A more complete overview of configuring the OPTIMADE server can be seen in the [configuration section](../configuration.md).

By default, the server will use the test configuration, including test data for structures and references and an in-memory mongomock database backend.
This can be changed in several different ways.

One is to `git clone` the repository locally and bind the repository folder to the `/app` folder in the container:

```shell
# volume will bind the local version of `optimade-python-tools` to the container.
docker run \
    --rm \
    --detach \
    --publish 8080:5000 \
    --env MAIN=main \
    --name my-optimade \
    --volume /path/to/optimade-python-tools:/app \
    ghcr.io/materials-consortia/optimade:latest
```

!!! help
    To clone the repository you can run:

    ```shell
    git clone --recursive https://github.com/Materials-Consortia/optimade-python-tools.git
    ```

You should change the `/path/to/optimade-python-tools` to the full local path to the repository - or use `$PWD` if you are running this command from the root of the cloned repository on a Unix system.
Equivalently, `%cd%` should work on Windows.

In this setup you can change the repository root file `optimade_config.json` with the appropriate information.
E.g., if you do not wish to use the test data you can add the `insert_test_data` key with a value of `false`.

Another option is to _not_ `git clone` the repository locally, but instead only generate a JSON or YAML file somewhere, where the directory of its location is bound to another location in the container that is not used, e.g., `/config` or similar.
As an example, let us say we generate `config.yml` locally, with the full path `/home/user/optimade/config.yml`.
Then we can start the server with the following command:

```shell
# volume will bind the local directory to an unused folder in the container.
docker run \
    --rm \
    --detach \
    --publish 8080:5000 \
    --env MAIN=main \
    --name my-optimade \
    --volume /home/user/optimade:/config \
    --env OPTIMADE_CONFIG_FILE=/config/config.yml \
    ghcr.io/materials-consortia/optimade:latest
```

As shown, it is necessary to update the environment variable `OPTIMADE_CONFIG_FILE` within the container to point to the new internal path to the config file.
By default, this environment variable points to `/app/optimade_config.json`.

This also reveals another way of configuring the server: set environment variables when running the container to supply values that would otherwise be supplied from the configuration file.

The `docker run` command even has the opportunity to pass a path to a file containing a list of environment variables (`--env-file /path/to/env_file`), if you wish to configure the server in this way instead of through the standard configuration file.

## **Example**: Multiple container services in closed network

In this example we want to setup various services through containers that interact with each other on a closed internal network, only the OPTIMADE servers are exposed to the "outside".

For this example we will use Docker only.
One could choose to use the [Docker Compose](https://docs.docker.com/compose/) framework to neatly express the services in a single YAML file, however, to keep this compatible with Docker alternatives, we will focus on only using Docker.

We will also setup an index meta-database, with an associated OPTIMADE server, serving data from a MongoDB backend.
Hence, we need to run three separate services, configure it properly, and make sure only the OPTIMADE APIs are exposed.

### 1. Setup closed network

First, we want to create the internal network:

```shell
docker network create -d bridge optimade
```

### 2. Run MongoDB service

Then, we can create a volume for the MongoDB server to use and start it.

!!! note
    This can be setup in other ways, binding to local paths or otherwise.
    For more information on the specifics of how to use the MongoDB container image, see [the Docker Hub documentation](https://hub.docker.com/_/mongo).
    For more information from the MongoDB team concerning the Enterprise version, see [the MongoDB documentation](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-enterprise-with-docker/).

```shell
docker volume create mongodb-persist
# `mongo` will be the host name in the docker network, using `--name`.
docker run \
    --detach \
    --name mongo \
    --volume mongodb-persist:/data/db \
    --network optimade \
    docker.io/library/mongo:latest
```

At this point you should fill up the database with your data, or instead of doing the command above exactly, you could choose to bind to another "local" path that contains an existing MongoDB you have.

Most likely, you will have a database dump archive, which you will now be able to import.
If you do so, please note the name of the database, the collection, and consider any data model mappings from your data to OPTIMADE data models for _structures_ and/or _references_.

In the example, we assume the database has been filled with fully valid OPTIMADE _structures_ and _references_ in a database called **optimade_prod**, within the collections **structures** and **references**, respectively.

### 3. Run the OPTIMADE service

With this information, we can now start the OPTIMADE server:

```shell
docker run \
    --rm \
    --detach \
    --publish 8081:5000 \
    --env MAIN=main \
    --name my-optimade \
    --network optimade \
    --env OPTIMADE_CONFIG_FILE= \
    --env optimade_insert_test_data=false \
    --env optimade_database_backend=mongodb \
    --env optimade_mongo_uri=mongodb://mongo:27017 \
    --env optimade_mongo_database=optimade_prod \
    --env optimade_references_collection=references \
    --env optimade_structures_collection=structures \
    --env optimade_page_limit=25 \
    --env optimade_page_limit_max=100 \
    --env optimade_base_url=http://localhost:8081 \
    --env optimade_index_base_url=http://localhost:8080 \
    --env optimade_provider="{\"prefix\":\"myorg\",\"name\":\"My Organization\",\"description\":\"Short description for My Organization\",\"homepage\":\"https://example.org\"}" \
    ghcr.io/materials-consortia/optimade:latest
```

Note, the `optimade_base_url` and `optimade_index_base_url` values should be different if the server is run through a reverse-proxy service like NGINX, Apache or other.
For this example, we are only concerned with exposing the OPTIMADE APIs from the `localhost`.

Furthermore, note that we "unset" the `OPTIMADE_CONFIG_FILE` environment variable to ensure the system defaults are used instead of configuration values that matches the test data.

### 4. Setup and run the OPTIMADE index meta-database service

The next step is to start the OPTIMADE index meta-database.
For this, we will first create a JSON file to reference and load as data for the `/links` endpoint:

```json
[
  {
    "id": "my-optimade-db",
    "type": "links",
    "name": "My OPTIMADE API",
    "description": "An OPTIMADE API for my database of essential material structures.",
    "base_url": "http://localhost:8081",
    "homepage": "https://example.org",
    "link_type": "child"
  }
]
```

This file is stored in a newly created directory at `/home/user/optimade/index_data/index_links.json`.

Now, we can start the index meta-database server:

```shell
# `optimade_insert_test_data` needs to be `true` to insert JSON file data
docker run \
    --rm \
    --detach \
    --publish 8080:5000 \
    --env MAIN=main_index \
    --name my-optimade-index \
    --network optimade \
    --env OPTIMADE_CONFIG_FILE= \
    --env optimade_insert_test_data=true \
    --env optimade_database_backend=mongodb \
    --env optimade_mongo_uri=mongodb://mongo:27017 \
    --env optimade_mongo_database=optimade_index_prod \
    --env optimade_links_collection=links \
    --env optimade_page_limit=25 \
    --env optimade_page_limit_max=100 \
    --env optimade_base_url=http://localhost:8080 \
    --env optimade_index_base_url=http://localhost:8080 \
    --env optimade_provider="{\"prefix\":\"myorg\",\"name\":\"My Organization\",\"description\":\"Short description for My Organization\",\"homepage\":\"https://example.org\"}" \
    --env optimade_default_db=my-optimade-db \
    --env optimade_index_links_path=/external/index_data/index_links.json \
    --volume /home/user/optimade/index_data:/external/index_data \
    ghcr.io/materials-consortia/optimade:latest
```

### 5. Test the services

Finally, we can test it all works as intended.

Go to [localhost:8080/links](http://localhost:8080/links) to check you see the list of OPTIMADE databases linked to by the index meta-database.
This list should include the entry from the JSON file above with ID `my-optimade-db`.

You could from there go to [localhost:8081/info](http://localhost:8081/info) and see the introspective information about the OPTIMADE database.
Furthermore, now you could go search through the material structures in your database, e.g., retrieving all structures that include carbon and oxygen in their list of chemical elements: [localhost:8081/structures?filter=elements HAS ALL "C","O"](http://localhost:8081/structures?filter=elements%20HAS%20ALL%20%22C%22%2C%22O%22).

It is also good to test the limits we specified are upheld, e.g., the maximum number of requested entries is not allowed to exceed 100 according to the `optimade_page_limit_max` value we have specified.
To test this, we could request a response with 101 entries, which should return an error: [localhost:8081/structures?page_limit=101](http://localhost:8081/structures?page_limit=101).
And then a request for a response with 101 entries, which should _not_ return an error: [localhost:8081/structures?page_limit=100](http://localhost:8081/structures?page_limit=100).

If you wish to inspect the logs of any service, you can use the `docker logs` command, followed by any of the service container names, e.g., `docker logs my-optimade` will display the logged `stdout` and `stderr` from the OPTIMADE database server.

<!-- markdownlint-disable MD046 -->
!!! example "Use the test data"
    If you do not have any data with which to fill up the MongoDB backend, you can run through the example using test data with some minor changes.
    However, it is crucial you first `git clone` the repository locally, since the test data is included only in the repository - not the container image.

    Run all `docker` commands from the root of the cloned repository.

    When running the OPTIMADE servers, leave out the line concerning "unsetting" the `OPTIMADE_CONFIG_FILE` environment variable.
    When first running the OPTIMADE server (not the index meta-database) set the `optimade_insert_test_data` value to `true`.
    If you stop the server and want to restart it, you should then set the variable to `false`, since the startup of the server will otherwise fail, due to the test data already existing in the MongoDB database collections and the subsequent re-insertion will throw an error.
