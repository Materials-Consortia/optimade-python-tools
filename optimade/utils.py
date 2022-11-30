"""This submodule implements some useful utilities for dealing
with OPTIMADE providers that can be used in server or client code and for handling nested dicts.

"""

import json
from typing import Any, Iterable, List

from pydantic import ValidationError

from optimade.models.links import LinksResource

PROVIDER_LIST_URLS = (
    "https://providers.optimade.org/v1/links",
    "https://raw.githubusercontent.com/Materials-Consortia/providers/master/src/links/v1/providers.json",
)


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
            providers = requests.get(provider_list_url).json()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout,
            json.JSONDecodeError,
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
""".format(
                    "".join([f"    * {_}\n" for _ in PROVIDER_LIST_URLS])
                )
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
    provider: LinksResource, obey_aggregate=True
) -> List[LinksResource]:
    """For a provider, return a list of available child databases.

    Arguments:
        provider: The links entry for the provider.

    Returns:
        A list of the valid links entries from this provider that
        have `link_type` `"child"`.

    Raises:
        RuntimeError: If the provider's index meta-database is down,
            invalid, or the request otherwise fails.

    """
    import requests

    from optimade.models.links import Aggregate, LinkType
    from optimade.models.responses import LinksResponse

    base_url = provider.pop("base_url")
    if base_url is None:
        raise RuntimeError(f"Provider {provider['id']} provides no base URL.")

    links_endp = base_url + "/v1/links"
    try:
        links = requests.get(links_endp, timeout=10)
    except (requests.ConnectionError, requests.Timeout) as exc:
        raise RuntimeError(f"Unable to connect to provider {provider['id']}") from exc

    if links.status_code != 200:
        raise RuntimeError(
            f"Invalid response from {links_endp} for provider {provider['id']}: {links.content!r}."
        )

    try:
        links_resp = LinksResponse(**links.json())
    except (ValidationError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Did not understand response from {provider['id']}: {links.content!r}"
        ) from exc

    if isinstance(links_resp.data, LinksResource):
        return [
            link
            for link in links_resp.data
            if link.attributes.link_type == LinkType.CHILD
            and link.attributes.base_url is not None
            and (not obey_aggregate or link.attributes.aggregate == Aggregate.OK)
        ]

    else:
        raise RuntimeError("Invalid links responses received: {links.content!r")


def get_all_databases() -> Iterable[str]:
    """Iterate through all databases reported by registered OPTIMADE providers."""
    for provider in get_providers():
        try:
            links = get_child_database_links(provider)
            for link in links:
                if link.attributes.base_url:
                    yield str(link.attributes.base_url)
        except RuntimeError:
            pass


def write_to_nested_dict(dictionary: dict, composite_key: str, value: Any):
    """Puts a value into an arbitrary position in a nested dict.

    Arguments:
        dictionary: the dictionary to which the value should be added under the composite_key.
        composite_key: The key under which the value should be stored. The sub keys should be separated by a ".".
            e.g. "outer_level_key.inner_level_key"
        value: The value that should be stored in the dictionary.

    """
    if "." in composite_key:
        split_key = composite_key.split(".", 1)
        if split_key[0] not in dictionary:
            dictionary[split_key[0]] = {}
        write_to_nested_dict(dictionary[split_key[0]], split_key[1], value)
    else:
        dictionary[composite_key] = value


def read_from_nested_dict(dictionary: dict, composite_key: str) -> Any:
    """Reads a value from an arbitrary position in a nested dict.

    Arguments:
        dictionary: the dictionary from which the value under the composite_key should be read .
        composite_key: The key under which the value should be read. The sub keys should be separated by a ".".
            e.g. "outer_level_key.inner_level_key"

    Returns:
        The value as stored in the dictionary. If the value is not stored in the dictionary it returns None.
        A boolean. True indicates that the composite_key was present in the dictionary, False that it is not present.

    """
    split_key = composite_key.split(".", 1)
    if split_key[0] in dictionary:
        if len(split_key) > 1:
            return read_from_nested_dict(dictionary[split_key[0]], split_key[1])
        else:
            return dictionary[composite_key], True
    return None, False


def remove_from_nested_dict(dictionary: dict, composite_key: str):
    """Removes an entry from an arbitrary position in a nested dict.

    Arguments:
        dictionary: the dictionary from which the composite key should be removed.
        composite_key: The key that should be removed. The sub keys should be separated by a ".".
            e.g. "outer_level_key.inner_level_key"
            If the removal of key causes the dictionary one level up to be empty it is removed as well.
    """
    split_key = composite_key.split(".", 1)
    if split_key[0] in dictionary:
        if len(split_key) > 1:
            empty = remove_from_nested_dict(dictionary[split_key[0]], split_key[1])
            if empty:
                return remove_from_nested_dict(dictionary, split_key[0])
            else:
                return False
        else:
            del dictionary[composite_key]
            if not dictionary:
                return True
            else:
                return False


def set_field_to_none_if_missing_in_dict(entry: dict, field: str) -> dict:
    _, present = read_from_nested_dict(entry, field)
    if not present:
        split_field = field.split(".", 1)
        # It would be nice if there would be a more universal way to handle special cases like this.
        if split_field[0] == "structure_features":
            value: Any = []
        else:
            value = None
        write_to_nested_dict(entry, field, value)
    return entry
