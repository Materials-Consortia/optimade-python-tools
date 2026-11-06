import pytest

from optimade.models import (
    DataType,
    EntryInfoResponse,
    IndexInfoResponse,
    InfoResponse,
    PropertyDefinition,
)

from ..utils import BaseEndpointTests, IndexEndpointTests, RegularEndpointTests


class LegacyInfoEndpointTests(BaseEndpointTests):
    """Run tests for an endpoint, but _only_ for the regular server configured
    to serve the pre-v1.2 descriptions of properties at its info endpoints."""

    @pytest.fixture(autouse=True)
    def get_response(self, legacy_info_client):
        self.response = legacy_info_client.get(self.request_str)
        self.json_response = self.response.json()
        yield
        self.response = None
        self.json_response = None


class TestInfoEndpoint(RegularEndpointTests):
    """Tests for /info"""

    request_str = "/info"
    response_cls = InfoResponse

    def test_info_endpoint_attributes(self):
        assert "data" in self.json_response
        assert self.json_response["data"]["type"] == "info"
        assert self.json_response["data"]["id"] == "/"
        assert "attributes" in self.json_response["data"]
        attributes = [
            "api_version",
            "available_api_versions",
            "formats",
            "entry_types_by_format",
            "available_endpoints",
            "license",
            "available_licenses",
        ]
        self.check_keys(attributes, self.json_response["data"]["attributes"])

        # Test that the spdx identifier is transformed correctly and found in both license fields
        assert self.json_response["data"]["attributes"]["available_licenses"] == [
            "CC-BY-4.0"
        ]
        assert self.json_response["data"]["attributes"]["license"] == {
            "href": "https://spdx.org/licenses/CC-BY-4.0"
        }


class TestLegacyInfoStructuresEndpoint(LegacyInfoEndpointTests):
    """Tests for /info/structures with `legacy_info_properties` enabled"""

    request_str = "/info/structures"
    response_cls = EntryInfoResponse

    def test_info_structures_endpoint_data(self):
        assert "data" in self.json_response
        data_keys = ["description", "properties", "formats", "output_fields_by_format"]
        self.check_keys(data_keys, self.json_response["data"])

    def test_properties_type(self):
        types = {
            _.get("type", None)
            for _ in self.json_response.get("data", {}).get("properties", {}).values()
        }
        for data_type in types:
            if data_type is None:
                continue
            assert isinstance(DataType(data_type), DataType)

    def test_info_structures_sortable(self):
        """Check the sortable key is present for all properties"""
        for info_keys in (
            self.json_response.get("data", {}).get("properties", {}).values()
        ):
            assert "sortable" in info_keys

    def test_sortable_values(self):
        """Make sure certain properties are and are not sortable"""
        sortable = ["id", "nelements", "nsites"]
        non_sortable = []

        for field in sortable:
            sortable_info_value = (
                self.json_response.get("data", {})
                .get("properties", {})
                .get(field, {})
                .get("sortable", None)
            )
            assert sortable_info_value is not None
            assert sortable_info_value is True

        for field in non_sortable:
            sortable_info_value = (
                self.json_response.get("data", {})
                .get("properties", {})
                .get(field, {})
                .get("sortable", None)
            )
            assert sortable_info_value is not None
            assert sortable_info_value is False

    def test_info_structures_unit(self):
        """Check the unit key is present for certain properties"""
        unit_fields = ["lattice_vectors", "cartesian_site_positions"]
        for field, info_keys in (
            self.json_response.get("data", {}).get("properties", {}).items()
        ):
            if field in unit_fields:
                assert "unit" in info_keys, f"Field: {field}"
            else:
                assert "unit" not in info_keys, f"Field: {field}"

    def test_provider_fields(self):
        """Check the presence of provider-specific fields"""

        provider_fields = ["chemsys"]

        if not provider_fields:
            import warnings

            warnings.warn("No provider-specific fields found for 'structures'!")
            return

        for field in provider_fields:
            updated_field_name = f"_exmpl_{field}"
            assert updated_field_name in self.json_response.get("data", {}).get(
                "properties", {}
            )

            for static_key in ["description", "sortable"]:
                assert static_key in self.json_response.get("data", {}).get(
                    "properties", {}
                ).get(updated_field_name, {})


class TestLegacyInfoReferencesEndpoint(LegacyInfoEndpointTests):
    """Tests for /info/references with `legacy_info_properties` enabled"""

    request_str = "/info/references"
    response_cls = EntryInfoResponse

    def test_info_references_endpoint_data(self):
        assert "data" in self.json_response
        data_keys = ["description", "properties", "formats", "output_fields_by_format"]
        self.check_keys(data_keys, self.json_response["data"])

    def test_properties_type(self):
        types = {
            _.get("type", None)
            for _ in self.json_response.get("data", {}).get("properties", {}).values()
        }
        for data_type in types:
            if data_type is None:
                continue
            assert isinstance(DataType(data_type), DataType)


class PropertyDefinitionTests(RegularEndpointTests):
    """Common tests for the property definitions served at /info/<entry_type>"""

    response_cls = EntryInfoResponse

    @property
    def properties(self) -> dict:
        return self.json_response["data"]["properties"]

    def test_info_endpoint_data(self):
        data_keys = [
            "id",
            "type",
            "description",
            "properties",
            "formats",
            "output_fields_by_format",
        ]
        self.check_keys(data_keys, self.json_response["data"])
        assert self.json_response["data"]["type"] == "info"
        assert self.json_response["data"]["id"] == self.request_str.split("/")[-1]
        assert self.json_response["data"]["output_fields_by_format"]["json"] == list(
            self.properties
        )

    def test_properties_are_property_definitions(self):
        """Check that all properties are valid property definitions."""
        assert self.properties
        for name, definition in self.properties.items():
            PropertyDefinition.model_validate(definition)

        deserialized = self.response_cls(**self.json_response)
        assert all(
            isinstance(_, PropertyDefinition)
            for _ in deserialized.data.properties.values()
        )

    def test_standard_definitions(self):
        """Check that non-provider properties point at the definitions published for
        the specification, in the correct version of the definition format."""
        for name, definition in self.properties.items():
            if name.startswith("_"):
                continue
            assert definition["$id"].startswith("https://schemas.optimade.org/defs/v1.")
            assert definition["x-optimade-definition"]["name"] == name
            definition_format = definition["x-optimade-definition"]["format"]
            assert (
                definition["$schema"]
                == f"https://schemas.optimade.org/meta/v{definition_format}/optimade/property_definition.json"
            )
            assert "x-optimade-requirements" in definition

    def test_implementation(self):
        """Check that the support of this implementation is described for all properties."""
        for name, definition in self.properties.items():
            assert isinstance(definition["x-optimade-implementation"]["sortable"], bool)

        for name in ("id", "type"):
            assert (
                self.properties[name]["x-optimade-implementation"]["query-support"]
                == "all mandatory"
            )


class TestInfoStructuresEndpoint(PropertyDefinitionTests):
    """Tests for the property definitions at /info/structures"""

    request_str = "/info/structures"

    def test_definition_versions(self):
        """Check that properties point to the version of the specification that
        last (re)defined them."""
        assert (
            self.properties["nelements"]["$id"]
            == "https://schemas.optimade.org/defs/v1.2/properties/optimade/structures/nelements"
        )
        assert (
            self.properties["fractional_site_positions"]["$id"]
            == "https://schemas.optimade.org/defs/v1.3/properties/optimade/structures/fractional_site_positions"
        )

    def test_nested_definitions_and_units(self):
        lattice_vectors = self.properties["lattice_vectors"]
        assert lattice_vectors["x-optimade-type"] == "list"
        assert lattice_vectors["type"] == ["array", "null"]
        assert lattice_vectors["x-optimade-dimensions"]["sizes"] == [3, 3]
        assert lattice_vectors["items"]["items"]["x-optimade-unit"] == "angstrom"
        assert [
            _["symbol"] for _ in lattice_vectors["x-optimade-unit-definitions"]
        ] == ["angstrom"]

    def test_sortable_values(self):
        for field in ("id", "nelements", "nsites"):
            assert self.properties[field]["x-optimade-implementation"]["sortable"]

    def test_provider_fields(self):
        """Check that described provider fields are given full definitions."""
        definition = self.properties["_exmpl_chemsys"]
        assert definition["x-optimade-type"] == "string"
        assert definition["type"] == ["string", "null"]
        assert definition["x-optimade-unit"] == "inapplicable"
        assert definition["$id"].startswith("urn:uuid:")
        assert definition["x-optimade-definition"] == {
            "kind": "property",
            "format": "1.2",
            "name": "_exmpl_chemsys",
            "label": "_exmpl_chemsys_structures",
        }
        assert definition["x-optimade-implementation"] == {"sortable": True}

        # The keys of dictionaries that are only described by their type are unknown
        assert self.properties["_exmpl_stability"]["x-optimade-type"] == "dictionary"
        assert self.properties["_exmpl_stability"]["properties"] == {}

        # Provider fields without a description cannot be defined
        assert "_exmpl_band_gap" not in self.properties


class TestInfoReferencesEndpoint(PropertyDefinitionTests):
    """Tests for the property definitions at /info/references"""

    request_str = "/info/references"


class TestInfoFilesEndpoint(PropertyDefinitionTests):
    """Tests for the property definitions at /info/files"""

    request_str = "/info/files"


class TestIndexInfoEndpoint(IndexEndpointTests):
    """Tests for /info for the index meta-database"""

    request_str = "/info"
    response_cls = IndexInfoResponse

    def test_info_endpoint_attributes(self):
        assert "data" in self.json_response
        assert self.json_response["data"]["type"] == "info"
        assert self.json_response["data"]["id"] == "/"
        assert "attributes" in self.json_response["data"]
        attributes = [
            "api_version",
            "available_api_versions",
            "formats",
            "entry_types_by_format",
            "available_endpoints",
            "is_index",
        ]
        self.check_keys(attributes, self.json_response["data"]["attributes"])
        assert "relationships" in self.json_response["data"]
        relationships = ["default"]
        self.check_keys(relationships, self.json_response["data"]["relationships"])
        assert len(self.json_response["data"]["relationships"]["default"]) == 1
