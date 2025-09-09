import pytest
from bson import ObjectId

from optimade.server.config import CONFIG


@pytest.mark.skipif(
    CONFIG.database_backend.value not in ("mongomock", "mongodb"),
    reason="Skipping index test when testing the elasticsearch backend.",
)
def test_indexes_are_created_where_appropriate(client):
    """Test that with the test config, default indices are made by
    supported backends. This is tested by checking that we cannot insert
    an entry with the same underlying ID as the test data, and that this
    returns the appopriate database-specific error.

    """
    import pymongo.errors

    from optimade.server.query_params import EntryListingQueryParams
    from optimade.server.routers import ENTRY_COLLECTIONS

    # get one structure with and try to reinsert it
    for _type in ENTRY_COLLECTIONS:
        result, _, _, _, _ = ENTRY_COLLECTIONS[_type].find(
            EntryListingQueryParams(page_limit=1)
        )
        assert result is not None
        if isinstance(result, list):
            result = result[0]

        # The ID is mapped to the test data ID (e.g., 'task_id'), so the index is actually on that
        id_field = ENTRY_COLLECTIONS[_type].resource_mapper.get_backend_field("id")

        # Take the raw database result, extract the OPTIMADE ID and try to insert a canary
        # document containing just that ID, plus a fake MongoDB ID to avoid '_id' clashes
        canary = {id_field: result["id"], "_id": ObjectId(24 * "0")}
        # Match either for "Duplicate" (mongomock) or "duplicate" (mongodb)
        with pytest.raises(pymongo.errors.BulkWriteError, match="uplicate"):
            ENTRY_COLLECTIONS[_type].insert([canary])  # type: ignore
