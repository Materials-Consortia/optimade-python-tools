from optimade.models.partial_data import PartialDataFormat


def test_partial_data_object_generation():
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

    PartialDataFormat(**test_object)


# todo finish test below
# def test_json_object_generation():
#     test_object = {
#         "header": {
#             "optimade_partial_data": {"version": "1.2.0"},
#             "layout": "dense",
#             "returned_ranges": [{"start": 10, "stop": 20, "step": 2}],
#         },
#         "data": [
#             123,
#             345,
#             -12.6,
#             ["PARTIAL-DATA-NEXT", ["https://example.db.org/value4"]],
#         ],
#     }
#
#     PartialDataResource(**test_object)
