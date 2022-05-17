# Validation of OPTIMADE APIs

`optimade-python-tools` contains tools for validating external OPTIMADE implementations that may be helpful for all OPTIMADE providers.
The validator is dynamic and fuzzy, in that the tested filters are generated based on *random* entries served by the API, and the description of the API provided at the `/info` endpoint.

The validator is implemented in the [`optimade.validator`][optimade.validator.validator] submodule, but the two main entry points are:

1. The `optimade-validator` script, which is installed alongside the package.
2. The [`optimade-validator-action`](https://github.com/Materials-Consortia/optimade-validator-action) which allows the validator to be used as a GitHub Action.

To run the script, simply provide an OPTIMADE URL to the script at the command-line.
You can use the following to validate the Heroku deployment of our reference server:

```shell
$ optimade-validator https://optimade.herokuapp.com/
Testing entire implementation at https://optimade.herokuapp.com
...
```

Several additional options can be found under the `--help` flag, with the most important being `-v/-vvvv` to set the verbosity, `--index` to validate OPTIMADE index meta-databases and `--json` to receive the validation results as JSON document for programmatic use.

```shell
$ optimade-validator --help
usage: optimade-validator [-h] [-v] [-j] [-t AS_TYPE] [--index]
                          [--skip-optional] [--fail-fast] [-m]
                          [--page_limit PAGE_LIMIT]
                          [--headers HEADERS]
                          [base_url]

Tests OPTIMADE implementations for compliance with the optimade-python-tools models.

- To test an entire implementation (at say example.com/optimade/v1) for all required/available endpoints:

    $ optimade-validator http://example.com/optimade/v1

- To test a particular response of an implementation against a particular model:

    $ optimade-validator http://example.com/optimade/v1/structures/id=1234 --as-type structure

- To test a particular response of an implementation against a particular model:

    $ optimade-validator http://example.com/optimade/v1/structures --as-type structures


positional arguments:
  base_url              The base URL of the OPTIMADE
                        implementation to point at, e.g.
                        'http://example.com/optimade/v1' or
                        'http://localhost:5000/v1'

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbosity       Increase the verbosity of the output.
                        (-v: warning, -vv: info, -vvv: debug)
  -j, --json            Only a JSON summary of the validator
                        results will be printed to stdout.
  -t AS_TYPE, --as-type AS_TYPE
                        Validate the request URL with the
                        provided type, rather than scanning the
                        entire implementation e.g. optimade-
                        validator `http://example.com/optimade/v1
                        /structures/0 --as-type structure`
  --index               Flag for whether the specified OPTIMADE
                        implementation is an Index meta-database
                        or not.
  --skip-optional       Flag for whether the skip the tests of
                        optional features.
  --fail-fast           Whether to exit on first test failure.
  -m, --minimal         Run only a minimal test set.
  --page_limit PAGE_LIMIT
                        Alter the requested page limit for some
                        tests.
  --headers HEADERS     Additional HTTP headers to use for each
                        request, specified as a JSON object.
```
