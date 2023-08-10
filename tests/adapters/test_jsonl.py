from optimade.adapters.jsonl import from_jsonl, to_jsonl


def test_to_jsonl():
    test_object = [
        {
            "optimade_partial_data": {"version": "1.2.0"},
            "layout": "dense",
            "returned_ranges": [{"start": 10, "stop": 20, "step": 2}],
        },
        1243,
        345,
        -12.6,
        ["PARTIAL-DATA-NEXT", ["https://example.db.org/value4"]],
    ]
    file_content = to_jsonl(test_object)
    reprocessed_file = from_jsonl(file_content)
    assert test_object == reprocessed_file
    pass
