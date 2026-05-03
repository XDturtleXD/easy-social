from __future__ import annotations

from pathlib import Path
import mimetypes
from uuid import uuid4

from flask import current_app, url_for
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

IMAGE_EXTENSIONS = {"gif", "jpeg", "jpg", "png", "webp"}
VIDEO_EXTENSIONS = {"mov", "mp4", "mpeg", "webm"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def _supabase_client():
    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError("Install supabase to use Supabase Storage.") from exc

    url = current_app.config.get("SUPABASE_URL")
    key = current_app.config.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required.")
    return create_client(url, key)


def _save_to_supabase(file: FileStorage, filename: str) -> str:
    bucket = current_app.config["SUPABASE_STORAGE_BUCKET"]
    object_path = f"posts/{filename}"
    content_type = file.mimetype or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    file.stream.seek(0)
    _supabase_client().storage.from_(bucket).upload(
        path=object_path,
        file=file.stream.read(),
        file_options={
            "cache-control": "31536000",
            "content-type": content_type,
            "upsert": "false",
        },
    )
    return object_path


def save_media(file: FileStorage | None) -> tuple[str | None, str | None]:
    if not file or not file.filename:
        return None, None

    original_name = secure_filename(file.filename)
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported media type.")

    media_type = "image" if extension in IMAGE_EXTENSIONS else "video"
    filename = f"{uuid4().hex}.{extension}"
    if current_app.config.get("MEDIA_STORAGE_BACKEND") == "supabase":
        return _save_to_supabase(file, filename), media_type

    destination = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    file.save(destination)
    return filename, media_type


def media_url(media_filename: str) -> str:
    if current_app.config.get("MEDIA_STORAGE_BACKEND") == "supabase":
        bucket = current_app.config["SUPABASE_STORAGE_BUCKET"]
        return _supabase_client().storage.from_(bucket).get_public_url(media_filename)
    return url_for("static", filename=f"uploads/{media_filename}")
