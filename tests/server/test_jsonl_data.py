"""Tests that the JSONL test data fixture (`optimade/server/data/test_data.jsonl`)
is internally consistent with the OPTIMADE models:

- every entry resource line validates against its resource model;
- every `/info/<entry>` line validates against `EntryInfoResource` and exposes all
  the properties defined by the corresponding model.
"""

from pathlib import Path

import bson.json_util
import pytest

import optimade.server.data
from optimade.models import EntryInfoResource
from optimade.server.schemas import ENTRY_INFO_SCHEMAS, retrieve_queryable_properties

JSONL_PATH = Path(optimade.server.data.__file__).parent / "test_data.jsonl"


def _load_jsonl() -> tuple[list[dict], list[dict]]:
    """Return ``(entry_lines, info_lines)`` parsed from the JSONL fixture."""
    entries: list[dict] = []
    infos: list[dict] = []
    with open(JSONL_PATH) as handle:
        handle.readline()  # skip the `x-optimade` header line
        for line in handle:
            if not line.strip():
                continue
            obj = bson.json_util.loads(line)
            if obj.get("type") == "info":
                infos.append(obj)
            elif obj.get("id") is not None:
                entries.append(obj)
    return entries, infos


ENTRY_LINES, INFO_LINES = _load_jsonl()
# Only entry-type info endpoints (i.e. those with a known resource model)
ENTRY_INFO_LINES = [i for i in INFO_LINES if i.get("id") in ENTRY_INFO_SCHEMAS]


def test_jsonl_data_present():
    """Sanity check that the fixture actually contains data to test."""
    assert ENTRY_LINES, "No entry resource lines found in the JSONL fixture"
    assert ENTRY_INFO_LINES, "No entry-info lines found in the JSONL fixture"


@pytest.mark.parametrize(
    "entry", ENTRY_LINES, ids=[f"{e['type']}/{e['id']}" for e in ENTRY_LINES]
)
def test_jsonl_entries_validate(entry):
    """Each entry resource line must validate against its resource model."""
    entry_type = entry["type"]
    assert entry_type in ENTRY_INFO_SCHEMAS, (
        f"Unknown entry type {entry_type!r} in JSONL fixture"
    )
    ENTRY_INFO_SCHEMAS[entry_type](**entry)


@pytest.mark.parametrize(
    "info", ENTRY_INFO_LINES, ids=[i["id"] for i in ENTRY_INFO_LINES]
)
def test_jsonl_info_validates_and_exposes_all_properties(info):
    """Each /info/<entry> line must validate and expose all model properties."""
    resource = EntryInfoResource(**info)

    model = ENTRY_INFO_SCHEMAS[info["id"]]
    expected = set(retrieve_queryable_properties(model, ("id", "type", "attributes")))
    present = set(resource.properties)

    missing = expected - present
    assert not missing, f"/info/{info['id']} is missing properties: {sorted(missing)}"
