"""This submodule implements some useful utilities for dealing
with OPTIMADE providers that can be used in server or client code.

"""

import contextlib
import json
from collections.abc import Container, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from requests.exceptions import SSLError

if TYPE_CHECKING:
    import rich

from pydantic import ValidationError

from optimade.models.links import LinksResource

PROVIDER_LIST_URLS = (
    "https://providers.optimade.org/v1/links",
    "https://raw.githubusercontent.com/Materials-Consortia/providers/master/src/links/v1/providers.json",
)


def insert_from_jsonl(jsonl_path: Path, create_default_index: bool = False) -> None:
    """Insert OPTIMADE JSON lines data into the database.

    Arguments:
        jsonl_path: Path to the JSON lines file.
        create_default_index: Whether to create a default index on the `id` field.

    """
    from collections import defaultdict

    import bson.json_util

    from optimade.server.logger import LOGGER
    from optimade.server.routers import ENTRY_COLLECTIONS

    batch = defaultdict(list)
    batch_size: int = 1000

    # Attempt to treat path as absolute, otherwise join with root directory
    if not jsonl_path.is_file():
        _jsonl_path = Path(__file__).parent.joinpath(jsonl_path)
        if not _jsonl_path.is_file():
            raise FileNotFoundError(
                f"Could not find file {jsonl_path} or {_jsonl_path}"
            )
        jsonl_path = _jsonl_path

    # If the chosen database backend supports it, make the default indices
    if create_default_index:
        for entry_type in ENTRY_COLLECTIONS:
            try:
                ENTRY_COLLECTIONS[entry_type].create_default_index()
            except NotImplementedError:
                pass

    bad_rows: int = 0
    good_rows: int = 0
    with open(jsonl_path) as handle:
        header = handle.readline()
        header_jsonl = json.loads(header)
        assert header_jsonl.get("x-optimade"), (
            "No x-optimade header, not sure if this is a JSONL file"
        )

        for line_no, json_str in enumerate(handle):
            try:
                if json_str.strip():
                    entry = bson.json_util.loads(json_str)
                else:
                    LOGGER.warning("Could not read any data from L%s", line_no)
                    bad_rows += 1
                    continue
            except json.JSONDecodeError:
                from optimade.server.logger import LOGGER

                LOGGER.warning("Could not read entry L%s JSON: '%s'", line_no, json_str)
                bad_rows += 1
                continue
            try:
                id = entry.get("id", None)
                _type = entry.get("type", None)
                if id is None or _type == "info":
                    # assume this is an info endpoint for pre-1.2
                    continue

                inp_data = entry["attributes"]
                inp_data["id"] = id
                if "relationships" in entry:
                    inp_data["relationships"] = entry["relationships"]
                if "links" in entry:
                    inp_data["links"] = entry["links"]
                # Append the data to the batch
                batch[_type].append(inp_data)
            except Exception as exc:
                LOGGER.warning(f"Error with entry at L{line_no} -- {entry} -- {exc}")
                bad_rows += 1
                continue

            if len(batch[_type]) >= batch_size:
                ENTRY_COLLECTIONS[_type].insert(batch[_type])
                batch[_type] = []

            good_rows += 1

        # Insert any remaining data
        for entry_type in batch:
            ENTRY_COLLECTIONS[entry_type].insert(batch[entry_type])
            batch[entry_type] = []

        if bad_rows:
            LOGGER.warning("Could not read %d rows from the JSONL file", bad_rows)

        LOGGER.info("Inserted %d rows from the JSONL file", good_rows)


def mongo_id_for_database(database_id: str, database_type: str) -> str:
    """Produce a MongoDB ObjectId for a database"""
    from bson.objectid import ObjectId

    oid = f"{database_id}{database_type}"
    if len(oid) > 12:
        oid = oid[:12]
    elif len(oid) < 12:
        oid = f"{oid}{'0' * (12 - len(oid))}"

    return str(ObjectId(oid.encode("UTF-8")))


def get_providers(add_mongo_id: bool = False) -> list:
    """Retrieve Materials-Consortia providers (from https://providers.optimade.org/v1/links).

    Fallback order if providers.optimade.org is not available:

    1. Try Materials-Consortia/providers on GitHub.
    2. Try submodule `providers`' list of providers.
    3. Log warning that providers list from Materials-Consortia is not included in the
       `/links`-endpoint.

    Arguments:
        add_mongo_id: Whether to populate the `_id` field of the provider with MongoDB
            ObjectID.

    Returns:
        List of raw JSON-decoded providers including MongoDB object IDs.

    """
    import json

    import requests

    for provider_list_url in PROVIDER_LIST_URLS:
        try:
            providers = requests.get(provider_list_url, timeout=10).json()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout,
            json.JSONDecodeError,
            requests.exceptions.SSLError,
        ):
            pass
        else:
            break
    else:
        try:
            from optimade.server.data import providers  # type: ignore
        except ImportError:
            from optimade.server.logger import LOGGER

            LOGGER.warning(
                """Could not retrieve a list of providers!

    Tried the following resources:

{}
    The list of providers will not be included in the `/links`-endpoint.
""".format("".join([f"    * {_}\n" for _ in PROVIDER_LIST_URLS]))
            )
            return []

    providers_list = []
    for provider in providers.get("data", []):
        # Remove/skip "exmpl"
        if provider["id"] == "exmpl":
            continue

        provider.update(provider.pop("attributes", {}))

        # Add MongoDB ObjectId
        if add_mongo_id:
            provider["_id"] = {
                "$oid": mongo_id_for_database(provider["id"], provider["type"])
            }

        providers_list.append(provider)

    return providers_list


def get_child_database_links(
    provider: LinksResource,
    obey_aggregate: bool = True,
    headers: dict | None = None,
    skip_ssl: bool = False,
) -> list[LinksResource]:
    """For a provider, return a list of available child databases.

    Arguments:
        provider: The links entry for the provider.
        obey_aggregate: Whether to only return links that allow
            aggregation.
        headers: Additional HTTP headers to pass to the provider.

    Returns:
        A list of the valid links entries from this provider that
        have `link_type` `"child"`.

    Raises:
        RuntimeError: If the provider's index meta-database is down,
            invalid, or the request otherwise fails.

    """
    import requests

    from optimade.models.links import Aggregate, LinkType

    base_url = provider.pop("base_url")
    if base_url is None:
        raise RuntimeError(f"Provider {provider['id']} provides no base URL.")

    links_endp = base_url + "/v1/links"
    try:
        links = requests.get(links_endp, timeout=10, headers=headers)
    except SSLError as exc:
        if skip_ssl:
            links = requests.get(links_endp, timeout=10, headers=headers, verify=False)
        else:
            raise RuntimeError(
                f"SSL error when connecting to provider {provider['id']}. Use `skip_ssl` to ignore."
            ) from exc
    except (requests.ConnectionError, requests.Timeout) as exc:
        raise RuntimeError(f"Unable to connect to provider {provider['id']}") from exc

    if links.status_code != 200:
        raise RuntimeError(
            f"Invalid response from {links_endp} for provider {provider['id']}: {links.content!r}."
        )

    try:
        links_resources = links.json().get("data", [])
        return_links = []
        for link in links_resources:
            link = LinksResource(**link)
            if (
                link.attributes.link_type == LinkType.CHILD
                and link.attributes.base_url is not None
                and (not obey_aggregate or link.attributes.aggregate == Aggregate.OK)
            ):
                return_links.append(link)

        return return_links

    except (ValidationError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Did not understand response from {provider['id']}: {links.content!r}, {exc}"
        )


def get_all_databases(
    include_providers: Container[str] | None = None,
    exclude_providers: Container[str] | None = None,
    exclude_databases: Container[str] | None = None,
    progress: "Optional[rich.Progress]" = None,
    skip_ssl: bool = False,
) -> Iterable[str]:
    """Iterate through all databases reported by registered OPTIMADE providers.

    Parameters:
        include_providers: A set/container of provider IDs to include child databases for.
        exclude_providers: A set/container of provider IDs to exclude child databases for.
        exclude_databases: A set/container of specific database URLs to exclude.

    Returns:
        A generator of child database links that obey the given parameters.

    """
    if progress is not None:
        _task = progress.add_task(
            description="Retrieving all databases from registered OPTIMADE providers...",
            total=None,
        )
    else:
        progress = contextlib.nullcontext()
        progress.print = lambda _: None  # type: ignore[attr-defined]
        progress.advance = lambda *_: None  # type: ignore[attr-defined]
        _task = None

    with progress:
        for provider in get_providers():
            if exclude_providers and provider["id"] in exclude_providers:
                continue
            if include_providers and provider["id"] not in include_providers:
                continue

            try:
                links = get_child_database_links(provider, skip_ssl=skip_ssl)
                for link in links:
                    if link.attributes.base_url:
                        if (
                            exclude_databases
                            and link.attributes.base_url in exclude_databases
                        ):
                            continue
                        yield str(link.attributes.base_url)
                if links and progress is not None:
                    progress.advance(_task, 1)
                    progress.print(
                        f"Retrieved databases from [bold green]{provider['id']}[/bold green]"
                    )
            except RuntimeError as exc:
                if progress is not None:
                    progress.print(
                        f"Unable to retrieve databases from [bold red]{provider['id']}[/bold red]: {exc}",
                    )
                pass
