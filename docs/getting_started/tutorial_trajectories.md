## Setting up an OPTIMADE Trajectory database.

The tutorial explains how to set up an OPTIMADE server for trajectory data.
The code linked to here matches the trajectory endpoint as described in [v0.2 of the trajectories proposal](https://github.com/JPBergsma/OPTIMADE/tree/JPBergsma_add_Trajectories/optimade.rst) and discussed in [OPTIMADE PR#377](https://github.com/Materials-Consortia/OPTIMADE/pull/377).
This corresponds to [version 1.2 of the OPTIMADE specification](https://github.com/Materials-Consortia/OPTIMADE/tree/develop).
The trajectory endpoint is however still under development and, based on feedback from the community, there may still be significant changes before it is merged with the main OPTIMADE specification.

The [optimade-python-tools](https://github.com/Materials-Consortia/optimade-python-tools) library currently supports the [MongoDB](https://www.mongodb.com) and [Elasticsearch](https://www.elastic.co/elasticsearch) database backends.
Other backends can be used as well, but will require creating a custom filtertransformer for converting the query into a backend compatible format and a custom [`EntryCollection`](https://www.optimade.org/optimade-python-tools/latest/api_reference/server/entry_collections/entry_collections/) object for interacting with the database backend.
More generic advice on setting up an OPTIMADE API can be found in the [online documentation](https://www.optimade.org/optimade-python-tools/latest/getting_started/setting_up_an_api/).

In this tutorial, we will use an Ubuntu-based Linux distribution with MongoDB as the backend for our trajectory data.
At the end of this document you can find a troubleshooting section.

### Acquiring the trajectory version of optimade-python-tools

The first step is to install optimade-python-tools.
You can find more details in the installation instructions described in [INSTALL.md](https://github.com/JPBergsma/optimade-python-tools/blob/optimade_python_tools_trajectory_0.1/INSTALL.md).
You will however need to use the code found on GitHub at [https://github.com/JPBergsma/optimade-python-tools/tree/JPBergsma/trajectory_endpoint](https://github.com/JPBergsma/optimade-python-tools/tree/JPBergsma/trajectory_endpoint).

If you only want to use the optimade python tools as a library you could use:

```
pip install git+https://github.com/JPBergsma/optimade-python-tools/tree/JPBergsma/trajectory_endpoint
```

In this tutorial, we are however describing how to set up your own database for sharing trajectory data.
In that case it is better to clone the repository and create your own branch from the [`optimade_python_tools_trajectory`](https://github.com/JPBergsma/optimade-python-tools/tree/JPBergsma/trajectory_endpoint) branch.
This way you can easily make modifications to the code when you want to change the behaviour of your server later on.

If you already have a GitHub account setup you can clone the repository with:

```
git clone --recursive git@github.com:JPBergsma/optimade-python-tools.git -b optimade_python_tools_trajectory_0.1
```

Without GitHub account you can use:

```
git clone --recursive https://github.com/JPBergsma/optimade-python-tools.git -b optimade_python_tools_trajectory_0.1
```


### Conda

You may now want to set up a separate Conda environment so there can't be a version conflict between the dependencies of different python programs.
See the instructions on how to install (Mini)Conda on the [conda website](https://conda.io/projects/conda/en/stable/user-guide/install/index.html).

If you use Conda you can create a separate environment using:


```
conda create -n optimade-traj python=3.10
```

You could also use Python versions 3.9+ if you need to integrate with other libraries that require them.
You can then activate and begin using the Conda environment with: `conda activate optimade-traj`


### Install the trajectory version of the optimade python tools

Next, you can install the local version of this package by going into the optimade-python-tools folder, created during the `git clone`, and installing the package locally with:

```
pip install -e .[server]
```

### Installing MongoDB

You can either install MongoDB directly on your system, or use the docker instructions in the Deployment instructions below.
For the former, installation instructions for MongoDB can be found on the [MongoDB website](https://www.mongodb.com/docs/manual/installation/)
The free community edition is good enough for our purposes.
To automatically run the `mongod` daemon when the machine is booted, you can run: `systemctl enable mongod.service`, to run it just once you can use: `systemctl start mongod.service`.

### Set up the config file

The next step is setting up the server configuration file.
The default location is in the user's home directory, i.e `"~/.optimade.json"`.
More information and alternative ways for setting up the configuration parameters can be found in the [online configuration instructions](https://github.com/JPBergsma/optimade-python-tools/blob/optimade_python_tools_trajectory_0.1/docs/configuration.md).
An example configuration file [`optimade_config.json`](https://github.com/JPBergsma/optimade-python-tools/blob/JPBergsma/trajectory_endpoint/optimade_config.json) is bundled with the package and can be used as starting point for creating your own configuration file.
If you are setting up a new API, the important parameters to set are:

* `insert_test_data`:
  * description: This value needs to be set to false, otherwise the test data will be inserted in the database you are trying to construct.
  * type: boolean

* `database_backend`:
  * description: The type of backend that is used. the options are: "elastic" for the Elasticsearch backend, "mongodb" for the MongoDB backend and "mongomock" for the test backend.
  In this tutorial, we use MongoDB, so it should be set to "mongodb".
  * type: string

* `base_url`:
  * description: The URL at which you will serve the database.
  If you are only testing the optimade python tools locally, you can use: "http://localhost:5000".
  * type: string

* `provider`:
  * description: This field contains information about the organization that provides the database.
  * type: dictionary
  * keys:
    * name:
      * description: The name of the organization providing the database.
      * type: string
    * description:
      * description: A description of the organization that provides the database.
      * type: string
    * prefix:
      * description: An abbreviation of the name of the database provider with an underscore on each side. e.g. "\_exmpl_".
      This is used as a prefix for fields in the database that are not described by the optimade standard, but have instead stead been defined by the database provider.
      * type: string
    * homepage:
      * description: A URL to the website of the provider.
      * type: string

* `provider_fields`:
  * description: In this dictionary, fields that are specific to this provider are defined.
  * type: dictionary
    * keys: Valid keys are the names of the types of endpoints ("links", "references", "structures", "trajectories") that are on this server.
    * values: A list with a dictionary for each database specific field/property that has been defined for the endpoint specified by the key.
      * keys: The sub-dictionaries describing the database specific properties/fields can contain the following keys:
        * name:
          * description: The name, without prefix, of the field as it should be presented in the OPTIMADE response.
          * type: string
        * type:
          * description: The JSON type of the field.
          Possible values are: "boolean", "object" (for an OPTIMADE dictionary), "array" (for an OPTIMADE list), "number" (for an OPTIMADE float), "string", and "integer".
          * type: string
        * unit:
          * description: The unit belonging to the property. One is encouraged to use the top most notation for the unit as described in [definitions.units](https://github.com/Materials-Consortia/OPTIMADE/blob/develop/units/definitions.units), which was taken from [GNU Units version 2.22](https://www.gnu.org/software/units/), as this will become the unit system for OPTIMADE 1.2 onward.
          * type: string
        * description:
          * description: A description of the property.
          * type: string

* `length_aliases`:
  * description: This property maps list properties to integer properties that define the length of those lists.
    For example: elements -> nelements.
    The standard aliases are applied first, so this dictionary must refer to the API fields, not the database fields.
  * type: dictionary of dictionaries.
  * keys: The names of the entrypoints available on this server. i.e. `["links", "references", "structures", "trajectories"]`
  * values: A dictionary with the name of the list field as the key and the field corresponding to the length of this list as the value.

* `max_datsa_size`:
  * description: Approximately the maximum size of a response for a particular response format.
    The optimade python tools will try to estimate the size of each frame that is to be returned and subsequently try to calculate the number of frames that can be returned in a single response.
    The final file can be larger if the estimate was poor.
  * type: Dictionary
  * keys: The names of the different supported return formats.
  * values: An integer containing the maximum size of the response in megabytes.

You can still adjust some of these parameters later if, for example, you want to add more database specific properties later on.
The script in the next section however uses the information in this file to connect to MongoDB, so that information must be present before the next step can be executed.
More parameters can be found by checking the `ServerConfig` class defined in [optimade.server.config.py](https://github.com/JPBergsma/optimade-python-tools/blob/JPBergsma/trajectory_endpoint/optimade/server/config.py), which are useful if you already have a pre-existing database or want to customize the setup of the MongoDB database.


### Loading trajectory data into MongoDB

The next step is to load the data that is needed to create valid OPTIMADE responses into the MongoDB database.
A small example script to generate a MongoDB entry from a trajectory file can be found at [JPBergsma/Export_traj_to_mongo](https://github.com/JPBergsma/Export_traj_to_mongo).
It uses the [MDanalysis](https://docs.mdanalysis.org/stable/index.html) package to read the trajectory files.
It can be downloaded with `git clone https://github.com/JPBergsma/Export_traj_to_mongo.git`
And installed with `pip install -e <path to Export_traj_to_mongo>`
You can use the same environment as before.

You can use this script to load the trajectory data into your database.

Instructions on how to run this script can be found in the accompanying [README.md](https://github.com/JPBergsma/Export_traj_to_mongo/blob/master/README.md) file.
If you have not restarted since installing MongoDB you still need to start MongoDB with: `systemctl start mongod`
To check whether MongoDB is running, you can use: `systemctl status mongod`

### Validation

To launch the OPTIMADE API server and test the setup, you can go to optimade-python-tools folder and run:

```
uvicorn optimade.server.main:app --reload --port=5000
```

By adding the --reload flag, the server is automatically restarted when code is changed as you develop your server.
Next, you can run `optimade-validator http://localhost:5000` to validate the setup of your database.

At the moment, the validator may still give a `ConfigError: duplicate validator function` error, which can be safely ignored for now.
Any errors under INTERNAL FAILURES indicate problems with the validator itself and not with the server setup. You can report those [here](https://github.com/JPBergsma/optimade-python-tools/issues).
More details about validating your server can be found in [the online documentation](https://github.com/JPBergsma/optimade-python-tools/blob/optimade_python_tools_trajectory_0.1/docs/concepts/validation.md).

### Deployment

Uvicorn runs as a single process and thus uses only a single cpu core.
If you want to run multiple processes, you can use Gunicorn.
Instructions for this on how to set this up can be found on https://fastapi.tiangolo.com/uk/deployment/server-workers/

In many organizations there is a firewall between the internet and the internal network.
You may therefore need to contact t ICT department of your organization to make your server reachable from outside the internal network.
This is also a good opportunity to ask them about extra security measures you may need to take, e.g., run the server within a container/virtual machine or using nginx.

### Using a docker container

You can run the optimade-python-tools from within a [docker](https://docs.docker.com/) container.
This adds a bit of security and is also a way to run multiple instances of the server.
The first step is building a docker image with your local version of the optimade-python-tools.
Run the following command in you local optimade-python-tools folder to create a docker image.

```
docker build -t optimade-traj:0.1
```

If you also want to run mongodb in a docker container the next step is to create a docker network, so the containers can communicate with each other, via:

```
docker network create -d bridge optimade
```

You can start mongodb in a docker container via:

```
docker run \
    --detach \
    --name mongo \
    --volume mongodb-persist:/data/db \
    --network optimade \
    docker.io/library/mongo:latest
```

In that case you have to set "mongo_uri" in the config file to "mongodb://mongo:27017".

Next you can start the container for the optimade python tools with:

```
docker run \
    --rm \
    --detach
    --publish 8081:5000 \
    --env MAIN=main \
    --name my-optimade \
    --network optimade \
    --volume /folder/containing/config/:/config \
    --env OPTIMADE_CONFIG_FILE=/config/.optimade.json \
    optimade-traj:0.1
```

You still have to replace /folder/containing/config/ with the path where you have put your config file.
The flag `--detach` causes the docker container to run in the background. If you want to see the output you can remove it.
If everything is running properly. you can now visit the landing page at http://0.0.0.0:8081/
The first value indicted under the flag `--publish` is the port number that is exposed externally.
You may need to adjust the value of "base_url" in the config file to match this port number.

If you do not run mongodb in a docker container you should set the `--network` flag to `"host"`.
The publish command is also ignored in that case, so by default the uvicorn server should be available at port 5000.

For more details see [container.md](https://www.optimade.org/optimade-python-tools/latest/deployment/container/)

### Register your database

Once you have finished setting up your server, you can register your API with the OPTIMADE consortium.
You can find instructions on how to do this [in the providers repository](https://github.com/Materials-Consortia/providers#requirements-to-be-listed-in-this-providers-list).

### Troubleshooting

#### MongoDB

##### exit code 14

This exit code means that the socket MongoDB wants to use is not available.
This may happen when MongoDB was not terminated properly.
It can be solved by: `$ rm /tmp/mongodb-27017.sock`
(27017 is the default port for mongod)

##### exit code:100 or exit code 34 or permission denied

IllegalOperation: Attempted to create a lock file on a read-only directory: /data/db or "permission denied.

Because mongod was run in a docker container the file permissions were changed.
You can reset them with:
```
sudo chmod -R 777 /data/db
```

and

```
sudo chown -R `id -u` /data/db
```


#### (Mini)Conda

If after you have installed Conda you get the error that the command cannot be found, it may be that the location of Conda has not been added to the PATH variable.
This may be because Conda has not been initialized properly.
You can try to use `conda init bash` to initialize Conda properly. (If you use a shell other than bash you should replace it with the name of your shell.)

If you get the error message: "ERROR: Error [Errno 2] No such file or directory 'git'" git still needs to be installed with:  `conda install git`

#### Docker

If you get the error "Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock:"
You have to run the docker commands with elevated privileges, for example by prepending them with `sudo `.

#### Further help

General questions about OPTIMADE can be asked on the [Matsci forum](https://matsci.org/c/optimade/29).
Bug reports or feature requests about the optimade-python-tools in general can be posted on the [optimade-python-tools github page](https://github.com/Materials-Consortia/optimade-python-tools/issues).
Issues specific to the trajectory branch of the optimade-python-tools can be posted on [https://github.com/JPBergsma/optimade-python-tools/issues](https://github.com/JPBergsma/optimade-python-tools/issues).
