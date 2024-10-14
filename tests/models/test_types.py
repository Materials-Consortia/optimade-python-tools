from typing import Annotated, Optional


def test_origin_type():
    from optimade.models.types import _get_origin_type

    assert _get_origin_type(int | None) is int
    assert _get_origin_type(str | None) is str
    assert _get_origin_type(Optional[int]) is int
    assert _get_origin_type(Optional[str]) is str
    assert _get_origin_type(Annotated[int, "test"]) is int
    assert _get_origin_type(Annotated[str, "test"]) is str
    assert _get_origin_type(int | str | None) is int
