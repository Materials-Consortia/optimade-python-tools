from optimade.models import DataType, EntryInfoResponse, IndexInfoResponse, InfoResponse

from ..utils import IndexEndpointTests, RegularEndpointTests


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
        ]
        self.check_keys(attributes, self.json_response["data"]["attributes"])


class TestInfoStructuresEndpoint(RegularEndpointTests):
    """Tests for /info/structures"""

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


class TestInfoReferencesEndpoint(RegularEndpointTests):
    """Tests for /info/references"""

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
