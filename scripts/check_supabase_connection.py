from __future__ import annotations

import argparse
import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from dotenv import load_dotenv

from easy_social import _validate_database_url


DEFAULT_ENV_FILE = Path(".env")
LEGACY_ENV_FILE = Path("env")
DEFAULT_BUCKET = "easy-social-media"


def env_file_path(value: str | None) -> Path:
    if value:
        return Path(value)
    if DEFAULT_ENV_FILE.exists():
        return DEFAULT_ENV_FILE
    return LEGACY_ENV_FILE


def masked_url(database_url: str) -> str:
    parsed = urlsplit(database_url)
    if not parsed.username:
        return database_url

    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"

    username = parsed.username
    password = ":***" if parsed.password else ""
    netloc = f"{username}{password}@{host}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test Supabase Postgres and Storage using local .env credentials."
    )
    parser.add_argument(
        "--env-file",
        help="Path to the dotenv file to load. Defaults to .env, or env if .env is absent.",
    )
    return parser.parse_args()


def check_database(database_url: str) -> None:
    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit("Install project dependencies before testing: task install") from exc

    print(f"Testing DATABASE_URL: {masked_url(database_url)}")

    try:
        with psycopg.connect(database_url, connect_timeout=10) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                        current_user,
                        current_database(),
                        inet_server_addr()::text,
                        inet_server_port(),
                        version()
                    """
                )
                user, database, host, port, version = cursor.fetchone()
    except psycopg.OperationalError as exc:
        raise SystemExit(f"Supabase connection failed: {exc}") from exc

    print("Supabase connection succeeded.")
    print(f"User: {user}")
    print(f"Database: {database}")
    print(f"Server: {host}:{port}")
    print(f"Postgres: {version.splitlines()[0]}")


def bucket_names(client) -> set[str]:
    return {
        getattr(item, "name", item.get("name") if isinstance(item, dict) else None)
        for item in client.storage.list_buckets()
    }


def check_storage(url: str, key: str, bucket: str) -> None:
    try:
        from supabase import create_client
    except ImportError as exc:
        raise SystemExit("Install project dependencies before testing: task install") from exc

    print(f"Testing Supabase Storage bucket: {bucket}")

    client = create_client(url, key)
    object_path = f"healthchecks/{uuid4().hex}.txt"
    payload = b"easy-social supabase storage healthcheck\n"
    storage = client.storage.from_(bucket)
    uploaded = False

    try:
        if bucket not in bucket_names(client):
            raise SystemExit(f"Supabase Storage bucket not found: {bucket}")

        storage.upload(
            path=object_path,
            file=payload,
            file_options={
                "cache-control": "60",
                "content-type": "text/plain",
                "upsert": "false",
            },
        )
        uploaded = True
        downloaded = storage.download(object_path)
        if downloaded != payload:
            raise SystemExit("Supabase Storage download did not match uploaded payload.")
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(f"Supabase Storage bucket check failed: {exc}") from exc
    finally:
        if uploaded:
            try:
                storage.remove([object_path])
            except Exception as exc:
                print(f"Warning: could not delete Storage healthcheck object {object_path}: {exc}")

    print("Supabase Storage bucket check succeeded.")
    print(f"Uploaded, downloaded, and deleted: {object_path}")


def main() -> None:
    args = parse_args()
    dotenv_path = env_file_path(args.env_file)
    if not dotenv_path.exists():
        raise SystemExit(f"Environment file not found: {dotenv_path}")

    load_dotenv(dotenv_path=dotenv_path, override=False)

    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise SystemExit(f"DATABASE_URL is not set in {dotenv_path}")

    supabase_url = os.environ.get("SUPABASE_URL", "")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    bucket = os.environ.get("SUPABASE_STORAGE_BUCKET", DEFAULT_BUCKET)
    if not supabase_url or not service_role_key:
        raise SystemExit(
            f"SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in {dotenv_path}"
        )

    _validate_database_url(database_url)

    print(f"Loaded credentials from: {dotenv_path}")
    check_database(database_url)
    check_storage(supabase_url, service_role_key, bucket)


if __name__ == "__main__":
    main()
