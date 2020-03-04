from pathlib import Path

import pytest
import unittest
import json

from pydantic import ValidationError  # pylint: disable=no-name-in-module
from optimade.models import (
    StructureResource,
    EntryRelationships,
    ReferenceResource,
    AvailableApiVersion,
)
from optimade.server.mappers import StructureMapper, ReferenceMapper


class TestPydanticValidation(unittest.TestCase):
    def test_good_structures(self):
        test_structures_path = (
            Path(__file__)
            .resolve()
            .parent.joinpath("../../optimade/server/data/test_structures.json")
        )
        with open(test_structures_path, "r") as f:
            good_structures = json.load(f)
            # adjust dates as mongo would
        for doc in good_structures:
            doc["last_modified"] = doc["last_modified"]["$date"]

        for structure in good_structures:
            StructureResource(**StructureMapper.map_back(structure))

    def test_more_good_structures(self):
        test_structures_path = (
            Path(__file__).resolve().parent.joinpath("test_more_structures.json")
        )
        with open(test_structures_path, "r") as f:
            good_structures = json.load(f)

        # adjust dates as mongo would
        for doc in good_structures:
            doc["last_modified"] = doc["last_modified"]["$date"]

        for structure in good_structures:
            StructureResource(**StructureMapper.map_back(structure))

    def test_bad_structures(self):
        test_structures_path = (
            Path(__file__).resolve().parent.joinpath("test_bad_structures.json")
        )
        with open(test_structures_path, "r") as f:
            bad_structures = json.load(f)
        for doc in bad_structures:
            doc["last_modified"] = doc["last_modified"]["$date"]

        for ind, structure in enumerate(bad_structures):
            with self.assertRaises(
                ValidationError,
                msg="Bad test structure {} failed to raise an error\nContents: {}".format(
                    ind, json.dumps(structure, indent=2)
                ),
            ):
                StructureResource(**StructureMapper.map_back(structure))

    def test_simple_relationships(self):
        """Make sure relationship resources are added to the correct relationship"""

        good_relationships = (
            {"references": {"data": [{"id": "dijkstra1968", "type": "references"}]}},
            {"structures": {"data": [{"id": "dijkstra1968", "type": "structures"}]}},
        )
        for relationship in good_relationships:
            EntryRelationships(**relationship)

        bad_relationships = (
            {"references": {"data": [{"id": "dijkstra1968", "type": "structures"}]}},
            {"structures": {"data": [{"id": "dijkstra1968", "type": "references"}]}},
        )
        for relationship in bad_relationships:
            with self.assertRaises(ValidationError):
                EntryRelationships(**relationship)

    def test_advanced_relationships(self):
        """Make sure the rules for the base resource 'meta' field are upheld"""

        relationship = {
            "references": {
                "data": [
                    {
                        "id": "dijkstra1968",
                        "type": "references",
                        "meta": {
                            "description": "Reference for the search algorithm Dijkstra."
                        },
                    }
                ]
            }
        }
        EntryRelationships(**relationship)

        relationship = {
            "references": {
                "data": [{"id": "dijkstra1968", "type": "references", "meta": {}}]
            }
        }
        with self.assertRaises(ValidationError):
            EntryRelationships(**relationship)

    def test_good_references(self):
        test_refs_path = (
            Path(__file__)
            .resolve()
            .parent.joinpath("../../optimade/server/data/test_references.json")
        )
        with open(test_refs_path, "r") as f:
            good_refs = json.load(f)
        for doc in good_refs:
            doc["last_modified"] = doc["last_modified"]["$date"]
            ReferenceResource(**ReferenceMapper.map_back(doc))

    def test_bad_references(self):
        bad_refs = [
            {"id": "AAAA", "type": "references", "doi": "10.1234/1234"},  # bad id
            {"id": "newton1687", "type": "references"},  # missing all fields
            {
                "id": "newton1687",
                "type": "reference",
                "doi": "10.1234/1234",
            },  # wrong type
        ]

        for ref in bad_refs:
            with self.assertRaises(ValidationError):
                ReferenceResource(**ReferenceMapper.map_back(ref))


def test_available_api_versions():
    bad_urls = [
        "asfdsafhttps://example.com/optimade/v0.0",
        "https://example.com/optimade",
        "https://example.com/optimade/v0",
        "https://example.com/optimade/v0999",
    ]
    good_urls = [
        {"url": "https://example.com/optimade/v0", "version": "0.1.9"},
        {"url": "https://example.com/optimade/v1.0.2", "version": "1.0.2"},
        {"url": "http://example.com/optimade/v2.3", "version": "2.3.1"},
    ]
    bad_combos = [
        {"url": "https://example.com/optimade/v0", "version": "1.0.0"},
        {"url": "https://example.com/optimade/v1.0.2", "version": "1.0.3"},
        {"url": "http://example.com/optimade/v2.3", "version": "2.0.1"},
    ]

    for url in bad_urls:
        with pytest.raises(ValueError):
            AvailableApiVersion(url=url, version="1.0")
            pytest.fail(f"Url {url} should have failed")

    for data in bad_combos:
        with pytest.raises(ValueError):
            AvailableApiVersion(**data)
            pytest.fail(
                f"{data['url']} should have failed with version {data['version']}"
            )

    for data in good_urls:
        AvailableApiVersion(**data)
