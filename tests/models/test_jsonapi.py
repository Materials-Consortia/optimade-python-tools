from optimade.models.jsonapi import Error


def test_hashability():
    error = Error(id="test")
    assert set([error])
