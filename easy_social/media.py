from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

IMAGE_EXTENSIONS = {"gif", "jpeg", "jpg", "png", "webp"}
VIDEO_EXTENSIONS = {"mov", "mp4", "mpeg", "webm"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def save_media(file: FileStorage | None) -> tuple[str | None, str | None]:
    if not file or not file.filename:
        return None, None

    original_name = secure_filename(file.filename)
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported media type.")

    media_type = "image" if extension in IMAGE_EXTENSIONS else "video"
    filename = f"{uuid4().hex}.{extension}"
    destination = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    file.save(destination)
    return filename, media_type

