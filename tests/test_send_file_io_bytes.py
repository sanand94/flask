"""Tests verifying that send_file accepts t.IO[bytes] objects, not just
t.BinaryIO objects. This covers the fix for issue #5776 where BinaryIO
was changed to IO[bytes] for wider compatibility."""
from __future__ import annotations

import inspect
import io
import typing as t

import flask
from flask.helpers import send_file


class PyBytesIO:
    """A proxy around BytesIO that does NOT inherit from io.RawIOBase or
    io.BufferedIOBase, so it would not satisfy t.BinaryIO but should
    satisfy t.IO[bytes]."""

    def __init__(self, *args, **kwargs):
        self._io = io.BytesIO(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._io, name)


class MinimalBytesIO:
    """An even more minimal IO[bytes]-compatible object that only implements
    the bare minimum required by werkzeug's send_file."""

    def __init__(self, data: bytes):
        self._data = io.BytesIO(data)

    def read(self, size: int = -1) -> bytes:
        return self._data.read(size)

    def seek(self, pos: int, whence: int = 0) -> int:
        return self._data.seek(pos, whence)

    def tell(self) -> int:
        return self._data.tell()


def test_send_file_type_annotation_uses_io_bytes():
    """Verify that the send_file signature uses t.IO[bytes] instead of t.BinaryIO."""
    sig = inspect.signature(send_file)
    param = sig.parameters["path_or_file"]
    annotation = param.annotation

    # The annotation string should contain 'IO[bytes]' and not 'BinaryIO'
    annotation_str = str(annotation)
    assert "IO[bytes]" in annotation_str, (
        f"Expected 'IO[bytes]' in annotation, got: {annotation_str}"
    )
    assert "BinaryIO" not in annotation_str, (
        f"Expected no 'BinaryIO' in annotation, got: {annotation_str}"
    )


def test_send_file_with_bytesio(app, req_ctx):
    """Test that send_file works with standard io.BytesIO."""
    data = b"Hello, World!"
    f = io.BytesIO(data)
    rv = flask.send_file(f, mimetype="text/plain")
    rv.direct_passthrough = False
    assert rv.data == data
    rv.close()


def test_send_file_with_proxy_bytesio(app, req_ctx):
    """Test that send_file works with a proxy around BytesIO (PyBytesIO).
    
    PyBytesIO does not inherit from io.IOBase, so it would fail if the
    type annotation required t.BinaryIO. With t.IO[bytes], it should work
    at runtime since werkzeug only checks for the interface, not the type.
    """
    data = b"Proxy bytes content"
    f = PyBytesIO(data)
    rv = flask.send_file(f, mimetype="application/octet-stream")
    rv.direct_passthrough = False
    assert rv.data == data
    rv.close()


def test_send_file_with_bytesio_mimetype(app, req_ctx):
    """Test that send_file correctly sets mimetype when given a BytesIO."""
    data = b'{"key": "value"}'
    f = io.BytesIO(data)
    rv = flask.send_file(f, mimetype="application/json")
    assert rv.mimetype == "application/json"
    rv.close()


def test_send_file_with_bytesio_as_attachment(app, req_ctx):
    """Test that send_file works with BytesIO as an attachment."""
    data = b"attachment content"
    f = io.BytesIO(data)
    rv = flask.send_file(
        f,
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name="test.bin",
    )
    assert rv.headers.get("Content-Disposition", "").startswith("attachment")
    rv.close()


def test_send_file_path_or_file_annotation():
    """Verify the type annotation of path_or_file is accessible and correct.
    
    This test checks the actual type hints module to ensure BinaryIO is not used.
    """
    hints = t.get_type_hints(send_file)
    path_or_file_hint = hints.get("path_or_file")
    assert path_or_file_hint is not None

    # Convert to string for inspection
    hint_str = str(path_or_file_hint)
    assert "BinaryIO" not in hint_str, (
        f"send_file should not use BinaryIO, found: {hint_str}"
    )
