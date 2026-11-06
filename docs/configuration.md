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

In order for the implementation to know where your configuration JSON file is located, you can set an environment variable `OPTIMADE_CONFIG_FILE` with either the value of the _absolute_ path to the configuration file or the _relative_ path to the file from the current working directory of where the server is run.

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

## Serving static files

The server can optionally serve files from a local directory, for example the contents of the entries in the [`files` endpoint](getting_started/setting_up_an_api.md#serving-the-files-endpoint), or any other supplementary material.
This is disabled by default and is configured with the [`static_files`][optimade.server.config.ServerConfig.static_files] option:

=== "JSON configuration file"

    ```json
    {
        "static_files": {
            "enabled": true,
            "directory": "/data/optimade_files",
            "route": "/static",
            "path_field": "local_path"
        }
    }
    ```

=== "Environment variable"

    ```shell
    export OPTIMADE_STATIC_FILES='{"enabled": true, "directory": "/data/optimade_files", "route": "/static"}'
    ```

=== "Python"

    ```python
    from optimade.server.config import ServerConfig, StaticFilesConfig
    from optimade.server.create_app import create_app

    config = ServerConfig(
        static_files=StaticFilesConfig(
            enabled=True, directory="/data/optimade_files", route="/static"
        )
    )
    app = create_app(config)
    ```

With the above configuration, the file `/data/optimade_files/cifs/1000000.cif` is served at `<base_url>/static/cifs/1000000.cif`.

- `directory` is required when `enabled` is `true`, and must be an existing, readable directory; otherwise the server will fail to start with a configuration error.
  Relative paths are resolved against the working directory of the server process when the configuration is loaded, so an absolute path is recommended.
- `route` must start with `/` and cannot be `/` itself, or clash with any of the OPTIMADE API paths (e.g., `/info`, `/structures`, `/versions` or versioned base URLs such as `/v1`).
  A trailing `/` is ignored.
- Files are served unversioned, i.e., only at `<base_url><route>/...` and not under `/v1/...`.
- Directory listings are not provided, and requests for paths outside of `directory` (e.g., via `..`) are rejected.
  Every file in `directory` (and its subdirectories) will be publicly accessible, so make sure it only contains files you wish to serve.

### Serving `files` entries by ID

When static files are enabled, the contents of each entry of the [`files` endpoint](getting_started/setting_up_an_api.md#serving-the-files-endpoint) can also be downloaded by its ID at `<base_url><route>/files/<id>`, e.g., `/static/files/file_1`.
This means the database does not need to store the full URL of each file:

- The file is looked up relative to `directory` using the database field named by `path_field` (e.g., `"path_field": "local_path"` with an entry containing `"local_path": "cifs/1000000.cif"`).
  If `path_field` is not set, or an entry does not have this field, the entry's `id` is used as its path instead.
  The `path_field` does not need to be exposed in the API (e.g., via `provider_fields`).
- Entries without a `url` in the database are given one pointing to this route in API responses, using the configured `base_url` (or the URL of the request, if unset).
  Entries that do have a `url` (e.g., to files hosted elsewhere) are served unchanged.
  As these URLs are generated, they cannot be used in `filter` queries.
- The response uses the entry's `media_type` (if set) as the content type, and its `name` as the file name for downloads.
- Requests for unknown entries, missing files, or paths outside of `directory` return a 404 error.

As this route takes precedence, any files in a `files/` subdirectory of `directory` cannot be served by their path.

!!! note
    With the Elasticsearch backend, only fields served by the API are retrieved from the database, so `path_field` must be one of these (e.g., a provider field).

This is intended as a convenience for small deployments; for serving large numbers of files or under heavy load, a dedicated web server, reverse proxy or object storage is likely more appropriate.

## List of configuration options

See [`config.py`][optimade.server.config.ServerConfig] for a complete list of configuration options.

The following configuration file represents the default values for all configuration options:

=== "Default values for all configuration options"

    ```json
    --8<-- "docs/static/default_config.json"
    ```
