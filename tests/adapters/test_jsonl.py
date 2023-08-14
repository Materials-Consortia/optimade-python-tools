from pathlib import Path

from optimade.adapters.jsonl import from_jsonl, to_jsonl

test_object = from_jsonl(Path(__file__).parent.resolve() / "testdata.jsonl")


def test_to_and_from_jsonl():
    file_content = to_jsonl(test_object)
    reprocessed_file = from_jsonl(file_content)
    assert test_object == reprocessed_file
