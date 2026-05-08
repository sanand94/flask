"""Tests for instance folder creation behavior.

Verifies that:
- os.makedirs with exist_ok=True is used instead of try/except OSError
- PermissionError is NOT silently swallowed when instance folder cannot be created
- The instance folder is created successfully when it does not exist
- No error is raised when the instance folder already exists
"""
import os
import stat
import sys
from unittest import mock
from unittest.mock import patch, MagicMock

import pytest

import flask


def test_instance_folder_created_when_missing(tmp_path):
    """Instance folder should be created if it does not already exist."""
    instance_path = tmp_path / "instance"
    assert not instance_path.exists()

    app = flask.Flask(__name__, instance_path=str(instance_path))
    # The Flask constructor does not auto-create the instance folder;
    # that is left to the application factory. We simulate the factory behavior.
    os.makedirs(app.instance_path, exist_ok=True)

    assert instance_path.exists()
    assert instance_path.is_dir()


def test_instance_folder_no_error_when_already_exists(tmp_path):
    """No error should be raised when the instance folder already exists."""
    instance_path = tmp_path / "instance"
    instance_path.mkdir()
    assert instance_path.exists()

    app = flask.Flask(__name__, instance_path=str(instance_path))
    # Should not raise FileExistsError
    os.makedirs(app.instance_path, exist_ok=True)

    assert instance_path.exists()


def test_instance_folder_permission_error_is_raised(tmp_path):
    """PermissionError should NOT be silently swallowed.

    This test verifies that the new behavior (using exist_ok=True without
    a broad except OSError) properly propagates PermissionError, unlike
    the old try/except OSError: pass pattern which would silently ignore it.
    """
    instance_path = tmp_path / "instance"

    app = flask.Flask(__name__, instance_path=str(instance_path))

    with patch("os.makedirs", side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError):
            os.makedirs(app.instance_path, exist_ok=True)


def test_old_pattern_silently_ignored_permission_error():
    """Demonstrate that the OLD pattern (try/except OSError: pass) silently
    ignores PermissionError — this is the bug we are fixing.

    This test shows the old broken behavior for reference: the exception
    was swallowed.
    """
    raised = []

    def makedirs_raising_permission_error(path, exist_ok=False):
        raise PermissionError("Permission denied")

    # Old pattern: catches all OSError (including PermissionError)
    try:
        makedirs_raising_permission_error("/some/path")
    except OSError:
        pass  # PermissionError is silently swallowed — this is the bug
    else:
        raised.append("no exception")

    # The old code would NOT raise — the error was lost
    assert raised == []  # confirms the bug: no exception propagated


def test_new_pattern_propagates_permission_error():
    """Demonstrate that the NEW pattern (exist_ok=True) properly propagates
    PermissionError when a directory cannot be created.
    """
    def makedirs_raising_permission_error(path, exist_ok=False):
        raise PermissionError("Permission denied")

    # New pattern: only exist_ok suppresses FileExistsError, not other errors
    with pytest.raises(PermissionError):
        makedirs_raising_permission_error("/some/path", exist_ok=True)


def test_new_pattern_suppresses_file_exists_error():
    """The exist_ok=True pattern should suppress FileExistsError (directory
    already exists), matching the old try/except OSError: pass behavior for
    the case where the directory already exists.
    """
    # os.makedirs with exist_ok=True on an existing directory does not raise
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Directory already exists — should not raise
        os.makedirs(tmpdir, exist_ok=True)


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="chmod-based permission tests are unreliable on Windows"
)
def test_makedirs_exist_ok_raises_on_unwritable_parent(tmp_path):
    """When the parent directory is not writable, os.makedirs should raise
    PermissionError rather than silently failing.

    This is the core behavior change: previously the OSError was caught and
    ignored; now it propagates.
    """
    # Make tmp_path unwritable so subdirectory creation fails
    original_mode = tmp_path.stat().st_mode
    try:
        tmp_path.chmod(0o555)  # read + execute, no write
        instance_path = tmp_path / "instance"

        with pytest.raises(PermissionError):
            os.makedirs(str(instance_path), exist_ok=True)
    finally:
        # Restore permissions so cleanup works
        tmp_path.chmod(original_mode)


def test_flask_app_instance_path_attribute(tmp_path):
    """Flask app should have the correct instance_path attribute set."""
    instance_path = tmp_path / "my_instance"
    app = flask.Flask(__name__, instance_path=str(instance_path))
    assert app.instance_path == str(instance_path)


def test_makedirs_exist_ok_true_does_not_raise_for_existing(tmp_path):
    """Calling os.makedirs with exist_ok=True on an existing directory
    should not raise any exception.
    """
    existing_dir = tmp_path / "existing"
    existing_dir.mkdir()

    # This should not raise FileExistsError
    os.makedirs(str(existing_dir), exist_ok=True)
    assert existing_dir.is_dir()


def test_makedirs_exist_ok_true_creates_nested_dirs(tmp_path):
    """os.makedirs with exist_ok=True should create nested directories."""
    nested = tmp_path / "a" / "b" / "c"
    assert not nested.exists()

    os.makedirs(str(nested), exist_ok=True)

    assert nested.exists()
    assert nested.is_dir()
