# Configuration

Since the server implementation is built with [FastAPI](https://fastapi.tiangolo.com/), which uses [pydantic](https://pydantic-docs.helpmanual.io/), the configuration is based on pydantic's [Setting management](https://pydantic-docs.helpmanual.io/usage/settings/).
This way of handling configuration options supports various different approaches to configure the server.
We recommend either or a combination of the following:

. Create a custom [`ServerConfig`][optimade.server.config.ServerConfig] object with the desired settings directly.
2. Set environment variables prefixed with `OPTIMADE_` or `optimade_`.
3. Create a JSON or YAML configuration file with an implementation's complete configuration in the default location [DEFAULT_CONFIG_FILE_PATH][optimade.server.config.DEFAULT_CONFIG_FILE_PATH] or specify its location with the `OPTIMADE_CONFIG_FILE` environment variable.
4. Load settings from a secret file Settings from secret file (see [pydantic documentation](https://pydantic-docs.helpmanual.io/usage/settings/#secret-support) for more information).

## The JSON configuration file

The main way of configuring the OPTIMADE server is by creating a configuration JSON file.

An example of one that works with the example implementation can be found in [`optimade_config.json`](static/optimade_config.json):

=== "Configuration file for the default OPTIMADE server"
    ```json
    --8<-- "optimade_config.json"
    ```

## Environment variables

In order for the implementation to know where your configuration JSON file is located, you can set an environment variable `OPTIMADE_CONFIG_FILE` with the value of the _full_ path to the JSON file.

This variable is actually an extension of the configuration option `config_file`.
By default, the server will try to load a JSON file called `.optimade.json` located in your home folder (or equivalent).

Here the generally recognized environment variable prefix becomes evident, namely `OPTIMADE_` or `optimade_`.
Hence, you can set (or overwrite) any configuration option from the server's defaults or a value read from the configuration JSON by setting an environment variable named `OPTIMADE_<configuration_option>`.

## List of configuration options

See [`config.py`][optimade.server.config.ServerConfig] for a complete list of configuration options.

The following configuration file represents the default values for all configuration options:

=== "Default values for all configuration options"
    ```json
    --8<-- "docs/static/default_config.json"
    ```
