"""
services/video_path_safety.py — Safe path validation for local video files
(V2, Phase 2).

PostgreSQL only ever stores a *validated, relative* path
(data/models_orm.py::LocalVideo.relative_path) — never an absolute
filesystem path, and never anything trusted purely because it came from a
request without being re-validated here. This module is the single place
that turns a candidate relative path into something safe to persist and,
later, safe to resolve back to a real file under VIDEO_STORAGE_DIR.

Video bytes themselves are never read or served by this module or by
FastAPI generally — that's Nginx's job (Phase 3). This module only ever
touches the filesystem to check existence/stat a file for metadata
purposes (see routers/videos.py in this phase).
"""
from pathlib import Path, PurePosixPath

from config.video_config import ALLOWED_VIDEO_EXTENSIONS, get_video_storage_root


class UnsafeVideoPathError(ValueError):
    """Raised when a candidate video path is empty, absolute, traversal,
    has a disallowed extension, or resolves outside VIDEO_STORAGE_DIR."""


def validate_relative_video_path(relative_path: str) -> str:
    """Validate `relative_path` and return the normalized, forward-slash
    relative path to persist in PostgreSQL.

    Requirements enforced:
      - non-empty
      - relative (no leading '/', no drive letter, no '~')
      - no '..' traversal segment anywhere in the path
      - extension is in ALLOWED_VIDEO_EXTENSIONS
      - resolves to a location that is actually inside VIDEO_STORAGE_DIR

    Raises UnsafeVideoPathError if any check fails.
    """
    if not relative_path or not relative_path.strip():
        raise UnsafeVideoPathError("Video path must not be empty.")

    raw = relative_path.strip().replace("\\", "/")
    candidate = PurePosixPath(raw)

    if candidate.is_absolute() or raw.startswith("~"):
        raise UnsafeVideoPathError(f"Video path must be relative: {relative_path!r}")

    if ".." in candidate.parts:
        raise UnsafeVideoPathError(f"Video path must not contain '..': {relative_path!r}")

    if candidate.suffix.lower() not in ALLOWED_VIDEO_EXTENSIONS:
        raise UnsafeVideoPathError(
            f"Video path extension {candidate.suffix!r} not in {ALLOWED_VIDEO_EXTENSIONS}: "
            f"{relative_path!r}"
        )

    storage_root = get_video_storage_root()
    resolved = (storage_root / candidate).resolve()
    try:
        resolved.relative_to(storage_root)
    except ValueError:
        raise UnsafeVideoPathError(
            f"Video path resolves outside VIDEO_STORAGE_DIR: {relative_path!r}"
        )

    return candidate.as_posix()


def resolve_video_absolute_path(relative_path: str) -> Path:
    """Validate + resolve a stored relative_path to an absolute filesystem
    Path under VIDEO_STORAGE_DIR. Server-side only (e.g. checking a file
    exists, or probing duration/size for metadata) — never exposed to
    clients, and never used to stream bytes (that's Nginx's job).
    """
    safe_relative = validate_relative_video_path(relative_path)
    return get_video_storage_root() / safe_relative


def video_file_exists(relative_path: str) -> bool:
    """True if `relative_path` is safe AND an actual file exists there."""
    try:
        return resolve_video_absolute_path(relative_path).is_file()
    except UnsafeVideoPathError:
        return False
