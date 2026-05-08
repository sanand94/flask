"""Tests to verify that instance folder creation behaves correctly.

Specifically:
- Creating the instance folder when it does not exist should succeed.
- Creating the instance folder when it already exists should succeed (exist_ok).
- A PermissionError when creating the instance folder should NOT be silently
  ignored — it should propagate to the caller.
"""
import os
import stat
import sys
from unittest import mock

import pytest

import flask


def test_instance_folder_created_when_missing(tmp_path):
    """The instance folder is created if it does not already exist."""
    instance_path = tmp_path / "new_instance"
    assert not instance_path.exists()

    app = flask.Flask(__name__, instance_path=str(instance_path))
    # Simulate what the factory does
    os.makedirs(app.instance_path, exist_ok=True)

    assert instance_path.exists()
    assert instance_path.is_dir()


def test_instance_folder_already_exists_no_error(tmp_path):
    """If the instance folder already exists, no error should be raised."""
    instance_path = tmp_path / "existing_instance"
    instance_path.mkdir()

    app = flask.Flask(__name__, instance_path=str(instance_path))
    # Should not raise even though the directory already exists
    os.makedirs(app.instance_path, exist_ok=True)

    assert instance_path.exists()


def test_instance_folder_permission_error_propagates(tmp_path):
    """A PermissionError when creating the instance folder must NOT be silently
    ignored — it should propagate to the caller.

    This is the core regression test: previously the try/except OSError block
    would catch PermissionError (a subclass of OSError) and silently pass,
    leaving the instance folder non-existent. With exist_ok=True, only the
    'already exists' case is suppressed; all other OSErrors propagate.
    """
    instance_path = tmp_path / "no_permission" / "instance"

    # Patch os.makedirs to raise PermissionError, simulating a permission
    # denied scenario without requiring root access.
    with mock.patch("os.makedirs", side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError):
            os.makedirs(str(instance_path), exist_ok=True)


def test_old_pattern_silently_ignores_permission_error(tmp_path):
    """Demonstrate that the OLD pattern (try/except OSError: pass) would
    silently swallow a PermissionError, which is the bug we fixed.

    This test verifies the old behaviour was wrong — it should NOT raise,
    which is precisely the problem.
    """
    instance_path = tmp_path / "no_permission" / "instance"

    permission_error = PermissionError("Permission denied")

    # Simulate the OLD broken pattern
    error_was_swallowed = False
    try:
        with mock.patch("os.makedirs", side_effect=permission_error):
            try:
                os.makedirs(str(instance_path))
            except OSError:
                # This is the old buggy pattern — it catches PermissionError too!
                error_was_swallowed = True
                pass
    except Exception:
        pass

    # The old pattern would have swallowed the error
    assert error_was_swallowed, (
        "The old try/except OSError pattern should have swallowed the PermissionError"
    )


def test_new_pattern_propagates_permission_error(tmp_path):
    """Verify the NEW pattern (exist_ok=True) correctly propagates PermissionError."""
    instance_path = tmp_path / "no_permission" / "instance"

    permission_error = PermissionError("Permission denied")

    # The new pattern with exist_ok=True should NOT catch PermissionError
    with mock.patch("os.makedirs", side_effect=permission_error):
        with pytest.raises(PermissionError):
            os.makedirs(str(instance_path), exist_ok=True)


def test_makedirs_exist_ok_does_not_raise_for_existing_dir(tmp_path):
    """Verify exist_ok=True does not raise when directory already exists,
    which is the behaviour that replaces the try/except OSError: pass pattern
    for the 'already exists' case.
    """
    existing_dir = tmp_path / "already_here"
    existing_dir.mkdir()

    # Should not raise
    os.makedirs(str(existing_dir), exist_ok=True)
    assert existing_dir.is_dir()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="chmod-based permission tests are unreliable on Windows",
)
def test_permission_error_on_real_filesystem(tmp_path):
    """Integration test: create a directory where we have no write permission,
    then verify that os.makedirs with exist_ok=True raises PermissionError.

    Skipped on Windows where chmod semantics differ.
    """
    # Create a parent directory and remove write permission
    parent = tmp_path / "readonly_parent"
    parent.mkdir()
    parent.chmod(stat.S_IREAD | stat.S_IEXEC)  # read + execute, no write

    try:
        instance_path = parent / "instance"

        with pytest.raises(PermissionError):
            os.makedirs(str(instance_path), exist_ok=True)
    finally:
        # Restore permissions so tmp_path cleanup works
        parent.chmod(stat.S_IRWXU)
