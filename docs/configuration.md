# Configuration

Since the server implementation is built with [FastAPI](https://fastapi.tiangolo.com/), which uses [pydantic](https://pydantic-docs.helpmanual.io/), the configuration is based on pydantic's [Setting management](https://pydantic-docs.helpmanual.io/usage/settings/).
This way of handling configuration options supports various different approaches to configure the server.
We recommend either or a combination of the following:

1. Create a JSON or YAML configuration file with an implementation's complete configuration in the default location [DEFAULT_CONFIG_FILE_PATH][optimade.server.config.DEFAULT_CONFIG_FILE_PATH] or specify its location with the `OPTIMADE_CONFIG_FILE` environment variable.
2. Set environment variables prefixed with `OPTIMADE_` or `optimade_`.
3. Create a custom [`ServerConfig`][optimade.server.config.ServerConfig] object with the desired settings directly.
4. Load settings from a secret file (see [pydantic documentation](https://pydantic-docs.helpmanual.io/usage/settings/#secret-support) for more information).

## The JSON configuration file

The main way of configuring the OPTIMADE server is by creating a configuration JSON file.

An example of one that works with the example implementation can be found in [`optimade_config.json`](static/optimade_config.json):

=== "Configuration file for the default OPTIMADE server"
    ```json
    --8<-- "optimade_config.json"
    ```

## Environment variables

In order for the implementation to know where your configuration JSON file is located, you can set an environment variable `OPTIMADE_CONFIG_FILE` with the either the value of the _absolute_ path to the configuration file or the _relative_ path to the file from the current working directory of where the server is run.

This variable is actually an extension of the configuration option `config_file`.
By default, the server will try to load a JSON file called `.optimade.json` located in your home folder (or equivalent).

Here the generally recognized environment variable prefix becomes evident, namely `OPTIMADE_` or `optimade_`.
Hence, you can set (or overwrite) any configuration option from the server's defaults or a value read from the configuration JSON by setting an environment variable named `OPTIMADE_<configuration_option>`.

## Custom configuration options

One can extend the current list of configuration options by sub-classing [`ServerConfig`][optimade.server.config.ServerConfig] and adding configuration options as attributes with values of `Field` (`pydantic.field`).
Any attribute type will be validated through `pydantic` as is the case for all of the regular configuration options.

This is useful for, e.g., custom database backends, if one wants to utilize the general server configuration setup implemented in `optimade` to declare specific database information.
It can also be useful if one wishes to extend and build upon the general `optimade` server with new endpoints and routes.

Remember to instantiate an instance of the sub-class, which can be imported and used in your application.

## List of configuration options

See [`config.py`][optimade.server.config.ServerConfig] for a complete list of configuration options.

The following configuration file represents the default values for all configuration options:

=== "Default values for all configuration options"
    ```json
    --8<-- "docs/static/default_config.json"
    ```
