"""Tests to verify that errorhandler type definitions work correctly
for all valid error handler signatures, including custom HTTPException
subclasses and plain Exception subclasses."""

import pytest
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import Forbidden
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import InternalServerError
from werkzeug.exceptions import NotFound

import flask


def test_errorhandler_with_custom_exception(app, client):
    """Registering an error handler for a custom Exception subclass should work."""

    class MyError(Exception):
        pass

    @app.errorhandler(MyError)
    def handle_my_error(e):
        assert isinstance(e, MyError)
        return "custom error", 200

    @app.route("/raise")
    def raise_error():
        raise MyError()

    response = client.get("/raise")
    assert response.status_code == 200
    assert response.data == b"custom error"


def test_errorhandler_with_http_exception_subclass(app, client):
    """Registering an error handler for a custom HTTPException subclass should work."""

    class MyBadRequest(BadRequest):
        pass

    @app.errorhandler(MyBadRequest)
    def handle_my_bad_request(e):
        assert isinstance(e, MyBadRequest)
        return "my bad request", 400

    @app.route("/raise")
    def raise_error():
        raise MyBadRequest()

    response = client.get("/raise")
    assert response.status_code == 400
    assert response.data == b"my bad request"


def test_errorhandler_with_plain_exception(app, client):
    """Registering an error handler for the base Exception class should work."""
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.errorhandler(Exception)
    def handle_exception(e):
        return f"caught {type(e).__name__}", 200

    @app.route("/raise")
    def raise_error():
        raise ValueError("test")

    response = client.get("/raise")
    assert response.status_code == 200
    assert b"caught ValueError" in response.data


def test_errorhandler_with_http_exception(app, client):
    """Registering an error handler for HTTPException should work."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        assert isinstance(e, HTTPException)
        return f"http error {e.code}", e.code

    @app.route("/raise")
    def raise_error():
        raise NotFound()

    response = client.get("/raise")
    assert response.status_code == 404
    assert b"http error 404" in response.data


def test_errorhandler_with_status_code(app, client):
    """Registering an error handler for an HTTP status code should work."""

    @app.errorhandler(404)
    def handle_404(e):
        assert isinstance(e, NotFound)
        return "not found", 404

    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert response.data == b"not found"


def test_errorhandler_with_forbidden_subclass(app, client):
    """Registering an error handler for a Forbidden subclass should work."""

    class MyForbidden(Forbidden):
        pass

    @app.errorhandler(MyForbidden)
    def handle_my_forbidden(e):
        assert isinstance(e, MyForbidden)
        return "my forbidden", 403

    @app.errorhandler(403)
    def handle_403(e):
        assert isinstance(e, Forbidden)
        return "forbidden", 403

    @app.route("/my-forbidden")
    def raise_my_forbidden():
        raise MyForbidden()

    @app.route("/forbidden")
    def raise_forbidden():
        flask.abort(403)

    response = client.get("/my-forbidden")
    assert response.status_code == 403
    assert response.data == b"my forbidden"

    response = client.get("/forbidden")
    assert response.status_code == 403
    assert response.data == b"forbidden"


def test_register_error_handler_with_custom_exception(app, client):
    """register_error_handler (non-decorator) should work for custom exceptions."""

    class MyError(Exception):
        pass

    def handle_my_error(e):
        assert isinstance(e, MyError)
        return "registered handler", 200

    app.register_error_handler(MyError, handle_my_error)

    @app.route("/raise")
    def raise_error():
        raise MyError()

    response = client.get("/raise")
    assert response.status_code == 200
    assert response.data == b"registered handler"


def test_errorhandler_typing_import():
    """The ErrorHandlerCallable type should be importable without error."""
    from flask.typing import ErrorHandlerCallable

    # Verify it's a valid type that can be used in annotations
    assert ErrorHandlerCallable is not None


def test_errorhandler_typing_no_typevar_error():
    """The typing module should not raise TypeError for invalid TypeVar usage."""
    # This test verifies the fix: previously GenericException TypeVar with
    # both 'bound' and 'contravariant=True' would cause a TypeError
    import importlib
    import flask.typing

    # Re-importing should not raise any errors
    importlib.reload(flask.typing)


def test_errorhandler_with_internal_server_error(app, client):
    """Registering an error handler for InternalServerError should work."""
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.errorhandler(InternalServerError)
    def handle_500(e):
        assert isinstance(e, InternalServerError)
        return "internal error", 500

    @app.route("/raise")
    def raise_error():
        raise RuntimeError("unexpected error")

    response = client.get("/raise")
    assert response.status_code == 500
    assert response.data == b"internal error"


def test_multiple_errorhandlers_on_same_function(app, client):
    """Applying errorhandler decorator multiple times should work."""

    @app.errorhandler(BadRequest)
    @app.errorhandler(404)
    def handle_errors(e):
        if isinstance(e, HTTPException):
            return f"http {e.code}", e.code
        return "error", 400

    @app.route("/bad-request")
    def raise_bad_request():
        raise BadRequest()

    response = client.get("/nonexistent")
    assert response.status_code == 404

    response = client.get("/bad-request")
    assert response.status_code == 400
