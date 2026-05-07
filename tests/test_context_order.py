"""Tests for the correct ordering of preserved contexts in the test client.

These tests verify that contexts pushed during a request are re-pushed in the
correct order when using the test client as a context manager, so that the
most recent context (with the latest session/request state) is accessible.
"""
import flask
from flask.globals import _cv_request


def test_preserved_context_is_most_recent(app):
    """The preserved context after a request should reflect the most recent
    request, not an older one."""
    app.secret_key = "test-secret"

    @app.route("/set")
    def set_session():
        flask.session["value"] = "from_set"
        return "ok"

    @app.route("/get")
    def get_session():
        return flask.session.get("value", "missing")

    client = app.test_client()

    with client:
        # First request sets a session value
        rv = client.get("/set")
        assert rv.status_code == 200

        # After the request, the preserved context should have the session
        # from the most recent (and only) request.
        # The session value should reflect what was set in /set
        assert flask.session.get("value") == "from_set"

        # Second request reads the session value
        rv = client.get("/get")
        assert rv.data == b"from_set"

        # After the second request, context should still reflect most recent request
        assert flask.session.get("value") == "from_set"


def test_preserved_context_order_multiple_requests(app):
    """After multiple requests in a with block, the preserved context should
    always be from the most recent request."""
    app.secret_key = "test-secret"

    @app.route("/set/<value>")
    def set_value(value):
        flask.session["counter"] = value
        return "ok"

    client = app.test_client()

    with client:
        client.get("/set/first")
        # After first request, session should have 'first'
        assert flask.session.get("counter") == "first"

        client.get("/set/second")
        # After second request, session should have 'second' (most recent)
        assert flask.session.get("counter") == "second"

        client.get("/set/third")
        # After third request, session should have 'third' (most recent)
        assert flask.session.get("counter") == "third"


def test_current_request_context_is_most_recent(app):
    """The current request context (via _cv_request) should be the most
    recently pushed one after a request completes."""

    request_urls = []

    @app.route("/page/<name>")
    def page(name):
        return f"page: {name}"

    client = app.test_client()

    with client:
        client.get("/page/first")
        first_ctx = _cv_request.get(None)
        assert first_ctx is not None
        # The preserved context should correspond to the /page/first request
        assert "first" in first_ctx.request.url

        client.get("/page/second")
        second_ctx = _cv_request.get(None)
        assert second_ctx is not None
        # The preserved context should now correspond to /page/second request
        assert "second" in second_ctx.request.url

        # The second context should be different from the first
        assert first_ctx is not second_ctx


def test_preserved_context_not_reversed(app):
    """Regression test: contexts must be pushed in original order, not reversed.

    When multiple contexts are appended to _new_contexts during a request
    (e.g., app context + request context), they must be re-pushed in the
    same order so that the stack is correct and the most recently pushed
    context is accessible as the current one.
    """
    app.secret_key = "test-secret"

    @app.route("/")
    def index():
        flask.session["key"] = "latest_value"
        return "hello"

    client = app.test_client()

    with client:
        rv = client.get("/")
        assert rv.status_code == 200

        # The session should reflect the state from the completed request
        # If contexts were reversed, this would show stale/wrong data
        assert flask.session.get("key") == "latest_value"


def test_session_accessible_after_request_in_with_block(app):
    """Session data set during a request should be accessible after the
    request completes when using the client as a context manager."""
    app.secret_key = "test-secret"

    @app.route("/login")
    def login():
        flask.session["user"] = "alice"
        flask.session["role"] = "admin"
        return "logged in"

    client = app.test_client()

    with client:
        rv = client.get("/login")
        assert rv.status_code == 200

        # Both session values should be accessible via the preserved context
        assert flask.session.get("user") == "alice"
        assert flask.session.get("role") == "admin"


def test_g_accessible_after_request_in_with_block(app):
    """Values set on flask.g during a request should be accessible after
    the request when using the client as a context manager."""

    @app.route("/")
    def index():
        flask.g.computed_value = 42
        flask.g.message = "hello"
        return "ok"

    client = app.test_client()

    with client:
        rv = client.get("/")
        assert rv.status_code == 200

        # g values should be accessible from the preserved context
        assert flask.g.computed_value == 42
        assert flask.g.message == "hello"


def test_request_object_accessible_after_request(app):
    """The request object should be accessible and correct after a request
    completes when using the client as a context manager."""

    @app.route("/info")
    def info():
        return "ok"

    client = app.test_client()

    with client:
        rv = client.get("/info?param=value")
        assert rv.status_code == 200

        # The preserved request should be the one just made
        assert flask.request.path == "/info"
        assert flask.request.args.get("param") == "value"


def test_context_order_with_stream_with_context(app):
    """When stream_with_context is used, the correct context should be
    preserved after the request."""
    app.secret_key = "test-secret"

    @app.route("/stream")
    def stream():
        flask.session["streamed"] = True
        return flask.stream_with_context("data")

    from flask.globals import _cv_request
    import pytest

    client = app.test_client()

    # Push an initial request context to simulate the req_ctx fixture scenario
    req_ctx = app.test_request_context()
    req_ctx.push()

    try:
        with client:
            rv = client.get("/stream")

        # Close the response to release stream_with_context's context
        rv.close()

        # Only the original req_ctx should remain
        assert _cv_request.get(None) is req_ctx
    finally:
        req_ctx.pop()
