from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from werkzeug.datastructures import FileStorage

from easy_social.media import save_media


def make_upload(filename: str, content: bytes = b"file-data") -> FileStorage:
    return FileStorage(stream=BytesIO(content), filename=filename)


def test_save_media_returns_empty_values_without_file(app):
    with app.app_context():
        assert save_media(None) == (None, None)
        assert save_media(make_upload("")) == (None, None)


@pytest.mark.parametrize(
    ("filename", "expected_type"),
    [
        ("photo.PNG", "image"),
        ("clip.MP4", "video"),
    ],
)
def test_save_media_accepts_allowed_extensions(app, filename, expected_type):
    with app.app_context():
        saved_filename, media_type = save_media(make_upload(filename, b"content"))
        saved_path = Path(app.config["UPLOAD_FOLDER"]) / saved_filename

        assert media_type == expected_type
        assert saved_filename is not None
        assert saved_filename.endswith(f".{filename.rsplit('.', 1)[-1].lower()}")
        assert saved_path.read_bytes() == b"content"


def test_save_media_rejects_unsupported_extensions(app):
    with app.app_context():
        with pytest.raises(ValueError, match="Unsupported media type"):
            save_media(make_upload("payload.exe"))

        assert not list(Path(app.config["UPLOAD_FOLDER"]).iterdir())
