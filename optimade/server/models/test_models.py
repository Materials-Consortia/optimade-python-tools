import pytest
from pydantic import BaseModel, ValidationError, ConfigError

from .util import conlist


def test_constrained_list():
    class ConListModel(BaseModel):
        v: conlist(len_eq=3)

    _ = ConListModel(v=[1, 2, 3])
    with pytest.raises(ValidationError) as exc_info:
        ConListModel(v=[1, 2, 3, 4])
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'ensure this value is less than or equal to 3',
            'type': 'value_error.number.not_le',
            'ctx': {'limit_value': 3},
        }
    ]

    with pytest.raises(ConfigError):
        class ConListModel(BaseModel):
            v: conlist(len_eq=3, len_lt=3)
