"""Tests verifying the type hint fix for FlaskCliRunner.invoke().

The return type of cli_runner.invoke() should be Result, not t.Any.
"""
import click
import pytest
from click.testing import Result

from flask import Flask
from flask.testing import FlaskCliRunner


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True

    @app.cli.command("hello")
    def hello_command():
        click.echo("Hello, World!")

    @app.cli.command("exit-one")
    def exit_one_command():
        raise SystemExit(1)

    return app


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


def test_invoke_returns_result_instance(app, runner):
    """invoke() must return a click.testing.Result object, not t.Any."""
    result = runner.invoke(args=["hello"])
    assert isinstance(result, Result), (
        f"Expected Result instance, got {type(result)}"
    )


def test_invoke_result_has_output_attribute(app, runner):
    """The returned Result object should have the .output attribute."""
    result = runner.invoke(args=["hello"])
    assert isinstance(result, Result)
    assert hasattr(result, "output")
    assert "Hello" in result.output


def test_invoke_result_has_exit_code_attribute(app, runner):
    """The returned Result object should have the .exit_code attribute."""
    result = runner.invoke(args=["hello"])
    assert isinstance(result, Result)
    assert hasattr(result, "exit_code")
    assert result.exit_code == 0


def test_invoke_with_command_object_returns_result(app, runner):
    """invoke() with a command object should still return Result."""
    @app.cli.command("greet")
    def greet_command():
        click.echo("Greetings!")

    result = runner.invoke(greet_command)
    assert isinstance(result, Result)
    assert "Greetings!" in result.output


def test_invoke_with_failing_command_returns_result(app, runner):
    """invoke() for a failing command still returns a Result object."""
    result = runner.invoke(args=["exit-one"])
    assert isinstance(result, Result)
    assert result.exit_code != 0


def test_invoke_default_cli_returns_result(app):
    """invoke() with default cli (no cli arg) returns a Result object."""
    runner = FlaskCliRunner(app)
    result = runner.invoke(args=["hello"])
    assert isinstance(result, Result)
    assert "Hello" in result.output


def test_invoke_with_explicit_cli_group_returns_result(app, runner):
    """invoke() passing the app's cli group explicitly returns a Result."""
    result = runner.invoke(cli=app.cli, args=["hello"])
    assert isinstance(result, Result)
    assert "Hello" in result.output


def test_invoke_result_type_is_not_any(app, runner):
    """Verify the result is specifically a Result, not just 'any' object."""
    result = runner.invoke(args=["hello"])
    # Result is a specific class from click.testing - verify it's exactly that
    assert type(result).__name__ == "Result"
    assert type(result).__module__ == "click.testing"


def test_flask_cli_runner_is_subclass_of_cli_runner():
    """FlaskCliRunner must be a subclass of CliRunner."""
    from click.testing import CliRunner
    assert issubclass(FlaskCliRunner, CliRunner)


def test_invoke_result_exception_attribute(app):
    """Result object has exception attribute for error cases."""
    runner = FlaskCliRunner(app)

    @app.cli.command("boom")
    def boom_command():
        raise ValueError("test error")

    result = runner.invoke(args=["boom"])
    assert isinstance(result, Result)
    # The exception is captured in the Result object
    assert hasattr(result, "exception")


def test_invoke_custom_obj_returns_result(app, runner):
    """invoke() with a custom obj kwarg still returns a Result."""
    from flask.cli import ScriptInfo

    script_info = ScriptInfo(create_app=lambda: app)
    result = runner.invoke(args=["hello"], obj=script_info)
    assert isinstance(result, Result)
    assert "Hello" in result.output
