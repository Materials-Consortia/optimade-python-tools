import json
import pathlib
import sys

import click
import rich

from optimade.client.client import OptimadeClient

__all__ = ("_get",)


@click.command("optimade-get")
@click.option(
    "--filter",
    default=[""],
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
@click.argument("base-url", default=None, nargs=-1)
def get(
    use_async,
    filter,
    base_url,
    max_results_per_provider,
    output_file,
    count,
    response_fields,
    sort,
    endpoint,
    pretty_print,
):
    return _get(
        use_async,
        filter,
        base_url,
        max_results_per_provider,
        output_file,
        count,
        response_fields,
        sort,
        endpoint,
        pretty_print,
    )


def _get(
    use_async,
    filter,
    base_url,
    max_results_per_provider,
    output_file,
    count,
    response_fields,
    sort,
    endpoint,
    pretty_print,
):

    if output_file:
        output_file_path = pathlib.Path(output_file)
        try:
            output_file_path.touch(exist_ok=False)
        except FileExistsError:
            raise SystemExit(
                f"Desired output file {output_file} already exists, not overwriting."
            )

    client = OptimadeClient(
        base_urls=base_url,
        use_async=use_async,
        max_results_per_provider=max_results_per_provider,
    )
    if response_fields:
        response_fields = response_fields.split(",")
    try:
        if count:
            for f in filter:
                client.count(f, endpoint=endpoint)
                results = client.count_results
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
            rich.print_json(data=results, indent=2, default=lambda _: _.dict())
        else:
            sys.stdout.write(json.dumps(results, indent=2, default=lambda _: _.dict()))

    if output_file:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=lambda _: _.dict())


if __name__ == "__main__":
    get()
