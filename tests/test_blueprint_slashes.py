# -*- coding: utf-8 -*-
"""
    tests.test_blueprint_slashes
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for blueprint prefix/rule slash normalization.

    :copyright: © 2010 by the Pallets team.
    :license: BSD, see LICENSE for more details.
"""
import pytest
import flask


@pytest.fixture
def app():
    app = flask.Flask(__name__)
    app.testing = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.mark.parametrize(('prefix', 'rule', 'expected'), [
    # Standard case: prefix with trailing slash, rule with leading slash
    ('/bar/', '/foo', '/bar/foo'),
    # Prefix with trailing slash, rule without leading slash
    ('/bar/', 'foo', '/bar/foo'),
    # Prefix without trailing slash, rule with leading slash
    ('/bar', '/foo', '/bar/foo'),
    # Prefix without trailing slash, rule without leading slash
    ('/bar', 'foo', '/bar/foo'),
    # Both have trailing/leading slashes
    ('/bar/', '/foo/', '/bar/foo/'),
    # Prefix with multiple trailing slashes
    ('/bar//', '/foo', '/bar/foo'),
    # Rule with multiple leading slashes
    ('/bar', '//foo', '/bar/foo'),
    # Both with multiple slashes
    ('/bar//', '//foo', '/bar/foo'),
    # Prefix with trailing slash, rule is just slash
    ('/bar/', '/', '/bar/'),
    # Empty prefix (no prefix)
    ('', '/foo', '/foo'),
])
def test_blueprint_prefix_slash_merge(app, client, prefix, rule, expected):
    """Test that slashes between blueprint prefix and rule are merged correctly."""
    bp = flask.Blueprint('test_bp', __name__, url_prefix=prefix)

    @bp.route(rule)
    def index():
        return '', 204

    app.register_blueprint(bp)
    response = client.get(expected)
    assert response.status_code == 204, (
        "Expected 204 for URL {!r} with prefix={!r} rule={!r}, "
        "got {}".format(expected, prefix, rule, response.status_code)
    )


def test_blueprint_prefix_slash_via_register(app, client):
    """Test slash normalization when prefix is given at register time."""
    bp = flask.Blueprint('test_bp', __name__)

    @bp.route('/foo')
    def index():
        return '', 204

    app.register_blueprint(bp, url_prefix='/bar/')
    assert client.get('/bar/foo').status_code == 204


def test_blueprint_prefix_trailing_slash_via_register(app, client):
    """Test that trailing slash on prefix at register time is handled."""
    bp = flask.Blueprint('test_bp2', __name__)

    @bp.route('foo')
    def index():
        return '', 204

    app.register_blueprint(bp, url_prefix='/spam/')
    assert client.get('/spam/foo').status_code == 204


def test_blueprint_double_slash_prefix_and_rule(app, client):
    """Test that double slashes between prefix and rule are collapsed to one."""
    bp = flask.Blueprint('test_bp3', __name__, url_prefix='/prefix/')

    @bp.route('/route')
    def index():
        return '', 204

    app.register_blueprint(bp)
    # Should be /prefix/route, not /prefix//route
    assert client.get('/prefix/route').status_code == 204
    assert client.get('/prefix//route').status_code in (301, 404)


def test_existing_prefix_slash_test(app, client):
    """Regression test: ensure existing test_blueprint_prefix_slash still works."""
    bp = flask.Blueprint('test', __name__, url_prefix='/bar/')

    @bp.route('/foo')
    def foo():
        return '', 204

    app.register_blueprint(bp)
    app.register_blueprint(bp, url_prefix='/spam/')
    assert client.get('/bar/foo').status_code == 204
    assert client.get('/spam/foo').status_code == 204


def test_no_prefix_blueprint(app, client):
    """Test blueprint with no prefix still works correctly."""
    bp = flask.Blueprint('no_prefix', __name__)

    @bp.route('/hello')
    def hello():
        return '', 204

    app.register_blueprint(bp)
    assert client.get('/hello').status_code == 204


def test_blueprint_prefix_none(app, client):
    """Test blueprint with url_prefix=None still works correctly."""
    bp = flask.Blueprint('none_prefix', __name__, url_prefix=None)

    @bp.route('/world')
    def world():
        return '', 204

    app.register_blueprint(bp)
    assert client.get('/world').status_code == 204
