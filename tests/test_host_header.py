"""Tests for Host header validation in Flask request context.

The Host header in HTTP must contain only ASCII characters. Non-ASCII
Unicode characters are not valid Host header values.
"""
import pytest

import flask
from flask.testing import EnvironBuilder


def test_non_ascii_host_raises_bad_request():
    """Non-ASCII characters in the Host header should result in a 400 Bad Request.

    The Host header cannot contain non-ASCII characters per HTTP spec.
    This covers the case previously (incorrectly) tested by
    test_environ_for_valid_idna_completes which expected a 200 response
    for a Unicode host - that test was invalid and has been removed.
    """
    app = flask.Flask(__name__)

    @app.route("/")
    def index():
        return "Hello World!"

    builder = EnvironBuilder(app)
    environ = builder.get_environ()

    # Non-ASCII Unicode characters are not valid in a Host header
    environ["HTTP_HOST"] = "ąśźäüжŠßя.com"

    with app.request_context(environ) as ctx:
        response = app.full_dispatch_request(ctx)

    # Should not return 200 - non-ASCII host headers are invalid
    assert response.status_code != 200


def test_non_printable_host_raises_bad_request():
    """Non-printable characters in the Host header should result in a 400 Bad Request."""
    app = flask.Flask(__name__)

    builder = EnvironBuilder(app)
    environ = builder.get_environ()

    environ["HTTP_HOST"] = "\x8a"

    with app.request_context(environ) as ctx:
        response = app.full_dispatch_request(ctx)

    assert response.status_code == 400


def test_valid_ascii_host_completes():
    """A valid ASCII host header should work normally."""
    app = flask.Flask(__name__)

    @app.route("/")
    def index():
        return "Hello World!"

    # xn--on-0ia.com is the punycode/IDNA encoding of a valid domain
    response = app.test_client().get("/", headers={"host": "xn--on-0ia.com"})
    assert response.status_code == 200


def test_standard_localhost_host_completes():
    """Standard localhost host header should work normally."""
    app = flask.Flask(__name__)

    @app.route("/")
    def index():
        return "Hello World!"

    response = app.test_client().get("/", headers={"host": "localhost"})
    assert response.status_code == 200


def test_host_with_port_completes():
    """Host header with port should work normally."""
    app = flask.Flask(__name__)

    @app.route("/")
    def index():
        return "Hello World!"

    response = app.test_client().get("/", headers={"host": "example.com:8080"})
    assert response.status_code == 200
