"""Test `AddWarning` middleware."""


def test_showwarning_overload(both_clients, recwarn):
    """Make sure warnings.showwarning can be overloaded correctly"""
    import warnings

    from optimade.server.middleware import AddWarnings
    from optimade.server.warnings import OptimadeWarning

    add_warning_middleware = AddWarnings(both_clients.app)
    # Set up things that are setup usually in `dispatch()`
    add_warning_middleware._warnings = []

    warnings.showwarning = add_warning_middleware.showwarning

    warning_message = "It's all gone awry!"

    warnings.warn(OptimadeWarning(detail=warning_message))

    assert add_warning_middleware._warnings == [
        {"title": OptimadeWarning.__name__, "detail": warning_message}
    ]

    # Make sure a "normal" warning is treated as usual
    warnings.warn(warning_message, UserWarning)
    assert len(add_warning_middleware._warnings) == 1
    assert len(recwarn.list) == 2
    assert recwarn.pop(OptimadeWarning)
    assert recwarn.pop(UserWarning)


def test_showwarning_debug(both_clients, recwarn):
    """Make sure warnings.showwarning adds 'meta' field in DEBUG MODE"""
    import warnings

    from optimade.server.config import CONFIG
    from optimade.server.middleware import AddWarnings
    from optimade.server.warnings import OptimadeWarning

    add_warning_middleware = AddWarnings(both_clients.app)
    # Set up things that are setup usually in `dispatch()`
    add_warning_middleware._warnings = []

    warnings.showwarning = add_warning_middleware.showwarning

    warning_message = "It's all gone awry!"

    org_debug = CONFIG.debug
    try:
        CONFIG.debug = True

        warnings.warn(OptimadeWarning(detail=warning_message))

        assert add_warning_middleware._warnings != [
            {"title": OptimadeWarning.__name__, "detail": warning_message}
        ]
        warning = add_warning_middleware._warnings[0]
        assert "meta" in warning
        for meta_field in ("filename", "lineno", "line"):
            assert meta_field in warning["meta"]
        assert len(recwarn.list) == 1
        assert recwarn.pop(OptimadeWarning)
    finally:
        CONFIG.debug = org_debug


def test_chunk_it_up():
    """Make sure all content is return from `chunk_it_up` generator"""
    from optimade.server.middleware import AddWarnings

    content = "Oh what a sad and tragic waste of a young attractive life!"
    chunk_size = 16
    assert len(content) % chunk_size != 0, "We want a rest bit, this isn't helpful!"

    generator = AddWarnings.chunk_it_up(content, chunk_size)
    assert "".join(generator) == content
