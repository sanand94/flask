import warnings

import pytest


def test_markup_import_from_flask():
    """Test that importing Markup from flask works and raises a deprecation warning."""
    import flask

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        Markup = flask.Markup
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "flask.Markup" in str(w[0].message)
        assert "markupsafe.Markup" in str(w[0].message)

    # Verify it's the actual Markup class from markupsafe
    from markupsafe import Markup as MarkupSafe
    assert Markup is MarkupSafe


def test_markup_import_from_flask_via_getattr():
    """Test that getattr(flask, 'Markup') works and returns markupsafe.Markup."""
    import flask
    from markupsafe import Markup as MarkupSafe

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        result = getattr(flask, "Markup")

    assert result is MarkupSafe


def test_markup_is_functional():
    """Test that the Markup imported from flask is actually functional."""
    import flask

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        Markup = flask.Markup

    # Should be able to create Markup instances
    m = Markup("<b>Hello</b>")
    assert str(m) == "<b>Hello</b>"
    assert m.__html__() == "<b>Hello</b>"


def test_escape_import_from_flask():
    """Test that importing escape from flask works and raises a deprecation warning."""
    import flask

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        escape = flask.escape
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "flask.escape" in str(w[0].message)
        assert "markupsafe.escape" in str(w[0].message)

    from markupsafe import escape as ms_escape
    assert escape is ms_escape


def test_unknown_attribute_raises_attribute_error():
    """Test that accessing an unknown attribute raises AttributeError."""
    import flask

    with pytest.raises(AttributeError):
        _ = flask.nonexistent_attribute_xyz


def test_signals_available_deprecation():
    """Test that accessing signals_available raises a deprecation warning."""
    import flask

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        val = flask.signals_available
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "signals_available" in str(w[0].message)

    assert val is True


def test_markup_deprecation_warning_message():
    """Test the exact deprecation warning message content for Markup."""
    import flask

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _ = flask.Markup

    assert len(w) == 1
    message = str(w[0].message)
    assert "deprecated" in message.lower()
    assert "Flask 2.4" in message
