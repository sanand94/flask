import pytest
import flask
from flask import after_this_request


def test_after_this_request_outside_request_context_raises_runtime_error():
    """after_this_request should raise RuntimeError when called outside
    a request context, with an error message mentioning the correct context
    requirement (not a different function name)."""
    app = flask.Flask(__name__)

    with pytest.raises(RuntimeError) as exc_info:
        after_this_request(lambda response: response)

    error_message = str(exc_info.value)
    # The error message should mention request context
    assert "request context" in error_message
    # It should NOT reference copy_current_request_context or other functions
    assert "copy_current_request_context" not in error_message


def test_after_this_request_outside_request_context_is_runtime_error_not_attribute_error():
    """The error raised should be RuntimeError, not AttributeError."""
    app = flask.Flask(__name__)

    with pytest.raises(RuntimeError):
        after_this_request(lambda response: response)


def test_after_this_request_inside_request_context_works():
    """after_this_request should work correctly when inside a request context."""
    app = flask.Flask(__name__)

    with app.test_request_context("/"):
        called = []

        @after_this_request
        def modify_response(response):
            called.append(True)
            return response

        # The function should have been registered without error
        from flask.globals import _request_ctx_stack
        top = _request_ctx_stack.top
        assert modify_response in top._after_request_functions


def test_after_this_request_error_message_mentions_request_context():
    """The error message should clearly indicate a request context is needed."""
    app = flask.Flask(__name__)

    with pytest.raises(RuntimeError) as exc_info:
        after_this_request(lambda response: response)

    # Should be a helpful message about request context
    assert "request context" in str(exc_info.value).lower()


def test_after_this_request_works_in_view(app, client):
    """after_this_request should work correctly within a view function."""

    @app.route("/test-after-this-request")
    def index():
        @after_this_request
        def add_header(response):
            response.headers["X-After-This-Request"] = "yes"
            return response

        return "OK"

    rv = client.get("/test-after-this-request")
    assert rv.status_code == 200
    assert rv.headers["X-After-This-Request"] == "yes"


def test_after_this_request_outside_app_context_raises_runtime_error():
    """after_this_request should raise RuntimeError even with only an app
    context (but no request context)."""
    app = flask.Flask(__name__)

    with app.app_context():
        with pytest.raises(RuntimeError) as exc_info:
            after_this_request(lambda response: response)

        assert "request context" in str(exc_info.value).lower()
