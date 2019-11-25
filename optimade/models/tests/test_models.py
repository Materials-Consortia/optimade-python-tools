from pathlib import Path

import pytest
import unittest
import json

from pydantic import ValidationError, BaseModel, ConfigError
from optimade.models.util import conlist
from optimade.models import StructureResource, EntryRelationships
from optimade.server.mappers import StructureMapper


class TestPydanticValidation(unittest.TestCase):
    def test_good_structures(self):
        test_structures_path = (
            Path(__file__)
            .resolve()
            .parent.joinpath("../../server/tests/test_structures.json")
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
        relationship = {
            "references": {"data": [{"id": "Dijkstra1968", "type": "references"}]}
        }
        EntryRelationships(**relationship)

        relationship = {
            "references": {"data": [{"id": "Dijkstra1968", "type": "structures"}]}
        }
        with self.assertRaises(ValidationError):
            EntryRelationships(**relationship)


def test_constrained_list():
    class ConListModel(BaseModel):
        v: conlist(len_eq=3)

    ConListModel(v=[1, 2, 3])
    with pytest.raises(ValidationError) as exc_info:
        ConListModel(v=[1, 2, 3, 4])
    assert exc_info.value.errors() == [
        {
            "loc": ("v",),
            "msg": "ensure this value is less than or equal to 3",
            "type": "value_error.number.not_le",
            "ctx": {"limit_value": 3},
        }
    ]

    with pytest.raises(ConfigError):

        class ConListModel(BaseModel):  # pylint: disable=function-redefined
            v: conlist(len_eq=3, len_lt=3)
