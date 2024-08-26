import json
import pathlib
import sys
from typing import TYPE_CHECKING

import click
import rich

from optimade import __api_version__, __version__
from optimade.client.client import OptimadeClient

if TYPE_CHECKING:  # pragma: no cover
    from typing import Union

    from optimade.client.utils import QueryResults

    ClientResult = Union[
        dict[str, list[str]],
        dict[str, dict[str, dict[str, int]]],
        dict[str, dict[str, dict[str, QueryResults]]],
    ]

__all__ = ("_get",)


@click.command("optimade-get", no_args_is_help=True)
@click.version_option(
    __version__,
    prog_name=f"optimade-get, an async OPTIMADE v{__api_version__} client",
)
@click.option(
    "--filter",
    default=[None],
    help="Filter to apply to OPTIMADE API. Default is an empty filter.",
    multiple=True,
)
@click.option("--use-async/--no-async", default=True, help="Use asyncio or not")
@click.option(
    "--max-results-per-provider",
    default=10,
    help="Set the maximum number of results to download from any single provider, where -1 or 0 indicate unlimited results.",
)
@click.option(
    "--output-file",
    default=None,
    help="Write the results to a JSON file at this location.",
)
@click.option(
    "--count/--no-count",
    default=False,
    help="Count the results of the filter rather than downloading them.",
)
@click.option(
    "--list-properties",
    default=None,
    help="An entry type to list the properties of.",
)
@click.option(
    "--search-property",
    default=None,
    help="An search string for finding a particular proprety.",
)
@click.option(
    "--endpoint",
    default="structures",
    help="The endpoint to query.",
)
@click.option(
    "--sort",
    default=None,
    help="A field by which to sort the query results.",
)
@click.option(
    "--response-fields",
    default=None,
    help="A string of comma-separated response fields to request.",
)
@click.option(
    "--pretty-print",
    is_flag=True,
    help="Pretty print the JSON results.",
)
@click.option(
    "--silent",
    is_flag=True,
    help="Suppresses all output except the final JSON results.",
)
@click.option(
    "--include-providers",
    default=None,
    help="A string of comma-separated provider IDs to query.",
)
@click.option(
    "--exclude-providers",
    default=None,
    help="A string of comma-separated provider IDs to exclude from queries.",
)
@click.option(
    "--exclude-databases",
    default=None,
    help="A string of comma-separated database URLs to exclude from queries.",
)
@click.argument(
    "base-url",
    default=None,
    nargs=-1,
)
@click.option("-v", "--verbosity", count=True, help="Increase verbosity of output.")
@click.option("--skip-ssl", is_flag=True, help="Ignore SSL errors in HTTPS requests.")
@click.option(
    "--http-timeout",
    type=float,
    help="The timeout to use for each HTTP request.",
)
def get(
    use_async,
    filter,
    base_url,
    max_results_per_provider,
    output_file,
    count,
    list_properties,
    search_property,
    response_fields,
    sort,
    endpoint,
    pretty_print,
    silent,
    include_providers,
    exclude_providers,
    exclude_databases,
    verbosity,
    skip_ssl,
    http_timeout,
):
    return _get(
        use_async,
        filter,
        base_url,
        max_results_per_provider,
        output_file,
        count,
        list_properties,
        search_property,
        response_fields,
        sort,
        endpoint,
        pretty_print,
        silent,
        include_providers,
        exclude_providers,
        exclude_databases,
        verbosity,
        skip_ssl,
        http_timeout,
    )


def _get(
    use_async,
    filter,
    base_url,
    max_results_per_provider,
    output_file,
    count,
    list_properties,
    search_property,
    response_fields,
    sort,
    endpoint,
    pretty_print,
    silent,
    include_providers,
    exclude_providers,
    exclude_databases,
    verbosity,
    skip_ssl,
    http_timeout,
    **kwargs,
):
    if output_file:
        output_file_path = pathlib.Path(output_file)
        try:
            output_file_path.touch(exist_ok=False)
        except FileExistsError:
            raise SystemExit(
                f"Desired output file {output_file} already exists, not overwriting."
            )

    args = {
        "base_urls": base_url,
        "use_async": use_async,
        "max_results_per_provider": max_results_per_provider,
        "include_providers": {_.strip() for _ in include_providers.split(",")}
        if include_providers
        else None,
        "exclude_providers": {_.strip() for _ in exclude_providers.split(",")}
        if exclude_providers
        else None,
        "exclude_databases": {_.strip() for _ in exclude_databases.split(",")}
        if exclude_databases
        else None,
        "silent": silent,
        "skip_ssl": skip_ssl,
    }

    # Only set http timeout if its not null to avoid overwriting or duplicating the
    # default value set on the OptimadeClient class
    if http_timeout:
        args["http_timeout"] = http_timeout

    args["verbosity"] = verbosity

    client = OptimadeClient(
        **args,
        **kwargs,
    )
    if response_fields:
        response_fields = response_fields.split(",")
    try:
        if TYPE_CHECKING:  # pragma: no cover
            results: ClientResult

        if count:
            for f in filter:
                client.count(f, endpoint=endpoint)
                results = client.count_results
        elif list_properties:
            results = client.list_properties(entry_type=list_properties)
            if search_property:
                results = client.search_property(
                    entry_type=list_properties, query=search_property
                )
        else:
            for f in filter:
                client.get(
                    f, endpoint=endpoint, sort=sort, response_fields=response_fields
                )
                results = client.all_results
    except RuntimeError:
        sys.exit(1)

    if not output_file:
        if pretty_print:
            rich.print_json(data=results, indent=2, default=lambda _: _.asdict())
        else:
            sys.stdout.write(
                json.dumps(results, indent=2, default=lambda _: _.asdict())
            )

    if output_file:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=lambda _: _.asdict())


if __name__ == "__main__":
    get()
