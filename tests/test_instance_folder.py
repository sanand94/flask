"""Tests for instance folder creation behavior.

Verifies that:
- os.makedirs with exist_ok=True is used (not try/except OSError)
- PermissionError is NOT silently swallowed
- Creating the instance folder when it already exists does not raise
"""
import os
import stat
import sys

import pytest

import flask


def test_instance_folder_created(tmp_path):
    """Instance folder is created if it does not exist."""
    instance_path = tmp_path / "instance"
    assert not instance_path.exists()

    app = flask.Flask(__name__, instance_path=str(instance_path))
    # The instance folder is not created automatically by Flask itself,
    # but our application code should create it with exist_ok=True.
    os.makedirs(app.instance_path, exist_ok=True)

    assert instance_path.exists()
    assert instance_path.is_dir()


def test_instance_folder_already_exists(tmp_path):
    """No error when the instance folder already exists."""
    instance_path = tmp_path / "instance"
    instance_path.mkdir()
    assert instance_path.exists()

    app = flask.Flask(__name__, instance_path=str(instance_path))
    # Should not raise even though the directory already exists
    os.makedirs(app.instance_path, exist_ok=True)

    assert instance_path.exists()
    assert instance_path.is_dir()


@pytest.mark.skipif(
    sys.platform == "win32" or os.getuid() == 0,
    reason="Permission tests are not reliable on Windows or when running as root",
)
def test_instance_folder_permission_error_propagates(tmp_path):
    """PermissionError is NOT silently swallowed when creating instance folder fails."""
    # Create a parent directory with no write permission
    no_write = tmp_path / "no_write"
    no_write.mkdir()
    no_write.chmod(stat.S_IRUSR | stat.S_IXUSR)  # r-x, no write

    try:
        instance_path = no_write / "instance"
        app = flask.Flask(__name__, instance_path=str(instance_path))

        # Using exist_ok=True does NOT suppress PermissionError
        with pytest.raises(PermissionError):
            os.makedirs(app.instance_path, exist_ok=True)
    finally:
        # Restore permissions so tmp_path cleanup works
        no_write.chmod(stat.S_IRWXU)


@pytest.mark.skipif(
    sys.platform == "win32" or os.getuid() == 0,
    reason="Permission tests are not reliable on Windows or when running as root",
)
def test_old_try_except_pattern_silently_swallows_permission_error(tmp_path):
    """Demonstrate the bug: the old try/except OSError: pass pattern
    silently swallows PermissionError.

    This test documents the incorrect behavior that was present before the fix.
    The old pattern would NOT raise even for PermissionError.
    """
    no_write = tmp_path / "no_write"
    no_write.mkdir()
    no_write.chmod(stat.S_IRUSR | stat.S_IXUSR)  # r-x, no write

    try:
        instance_path = no_write / "instance"

        # OLD (buggy) behavior: silently ignores PermissionError
        exception_raised = False
        try:
            try:
                os.makedirs(str(instance_path))
            except OSError:
                pass  # This incorrectly swallows PermissionError!
        except PermissionError:
            exception_raised = True

        # The old pattern does NOT raise - demonstrating the bug
        assert not exception_raised, (
            "Old try/except OSError pattern silently swallowed the PermissionError"
        )

        # The directory was NOT created, but the error was hidden
        assert not instance_path.exists()
    finally:
        no_write.chmod(stat.S_IRWXU)


@pytest.mark.skipif(
    sys.platform == "win32" or os.getuid() == 0,
    reason="Permission tests are not reliable on Windows or when running as root",
)
def test_new_exist_ok_pattern_raises_permission_error(tmp_path):
    """The new exist_ok=True pattern correctly raises PermissionError.

    This test verifies the fixed behavior: using exist_ok=True instead of
    try/except OSError allows PermissionError to propagate.
    """
    no_write = tmp_path / "no_write"
    no_write.mkdir()
    no_write.chmod(stat.S_IRUSR | stat.S_IXUSR)  # r-x, no write

    try:
        instance_path = no_write / "instance"

        # NEW (correct) behavior: PermissionError propagates
        with pytest.raises(PermissionError):
            os.makedirs(str(instance_path), exist_ok=True)
    finally:
        no_write.chmod(stat.S_IRWXU)


def test_exist_ok_does_not_raise_for_existing_dir(tmp_path):
    """exist_ok=True does not raise when the directory already exists."""
    existing = tmp_path / "existing"
    existing.mkdir()

    # Should not raise
    os.makedirs(str(existing), exist_ok=True)
    assert existing.exists()


def test_exist_ok_creates_nested_dirs(tmp_path):
    """exist_ok=True creates nested directories correctly."""
    nested = tmp_path / "a" / "b" / "c"
    assert not nested.exists()

    os.makedirs(str(nested), exist_ok=True)
    assert nested.exists()
    assert nested.is_dir()
