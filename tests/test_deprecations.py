import warnings

import pytest


def test_markup_importable_from_flask():
    """Test that Markup can be imported from flask (with a deprecation warning)."""
    import flask

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        Markup = flask.Markup
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "flask.Markup" in str(w[0].message)
        assert "markupsafe.Markup" in str(w[0].message)

    from markupsafe import Markup as MarkupSafe

    assert Markup is MarkupSafe


def test_markup_from_flask_is_markupsafe_markup():
    """Test that flask.Markup is the same as markupsafe.Markup."""
    import flask
    from markupsafe import Markup as MarkupSafe

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        FlaskMarkup = flask.Markup

    assert FlaskMarkup is MarkupSafe


def test_markup_works_correctly_when_imported_from_flask():
    """Test that the Markup object imported from flask works as expected."""
    import flask

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        Markup = flask.Markup

    # Markup should wrap HTML safely
    result = Markup("<strong>Hello</strong>")
    assert str(result) == "<strong>Hello</strong>"
    # Markup should escape when using format
    escaped = Markup("<em>%s</em>") % "<script>"
    assert "&lt;script&gt;" in escaped


def test_escape_importable_from_flask():
    """Test that escape can be imported from flask (with a deprecation warning)."""
    import flask

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        escape = flask.escape
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "flask.escape" in str(w[0].message)
        assert "markupsafe.escape" in str(w[0].message)

    from markupsafe import escape as markupsafe_escape

    assert escape is markupsafe_escape


def test_markup_deprecation_warning_message():
    """Test the exact content of the deprecation warning for flask.Markup."""
    import flask

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _ = flask.Markup

    assert len(w) == 1
    warning = w[0]
    assert issubclass(warning.category, DeprecationWarning)
    message = str(warning.message)
    assert "flask.Markup" in message
    assert "markupsafe.Markup" in message
    assert "2.4" in message


def test_escape_deprecation_warning_message():
    """Test the exact content of the deprecation warning for flask.escape."""
    import flask

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _ = flask.escape

    assert len(w) == 1
    warning = w[0]
    assert issubclass(warning.category, DeprecationWarning)
    message = str(warning.message)
    assert "flask.escape" in message
    assert "markupsafe.escape" in message


def test_unknown_attribute_raises_attribute_error():
    """Test that accessing an unknown attribute on flask raises AttributeError."""
    import flask

    with pytest.raises(AttributeError):
        _ = flask.nonexistent_attribute_xyz


def test_signals_available_deprecation():
    """Test that signals_available raises a deprecation warning and returns True."""
    import flask

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = flask.signals_available

    assert result is True
    assert len(w) == 1
    assert issubclass(w[0].category, DeprecationWarning)
    assert "signals_available" in str(w[0].message)
