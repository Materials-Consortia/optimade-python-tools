from optimade.models.partialdata import PartialDataResponse


def test_object_generation():
    test_object = {
        "header": {
            "optimade_partial_data": {"version": "1.2.0"},
            "layout": "dense",
            "returned_ranges": [{"start": 10, "stop": 20, "step": 2}],
        },
        "data": [
            123,
            345,
            -12.6,
            ["PARTIAL-DATA-NEXT", ["https://example.db.org/value4"]],
        ],
    }

    PartialDataResponse(**test_object)

    pass
