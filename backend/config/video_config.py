"""
config/video_config.py — V2 local video storage configuration (Phase 2).

VIDEO_STORAGE_DIR is the server-filesystem root that local video files are
stored under. Nginx serves bytes directly from it (Phase 3); FastAPI/
Postgres never touch video binaries. It is intentionally NOT hardcoded to
any path inside this repository, nor to any sandbox/dev-container path —
for a real ~160-client LAN deployment it must point at wherever the server
operator actually keeps video files (a dedicated data disk/volume, a NAS
mount, etc.), and is fully overridable via the VIDEO_STORAGE_DIR
environment variable. See backend/.env.example.

PostgreSQL never stores this directory itself, or any absolute path — only
a validated path *relative* to it (see data/models_orm.py::LocalVideo and
services/video_path_safety.py).
"""
import os
from pathlib import Path

from loguru import logger

# Deliberately a generic, OS-level location outside the repo/sandbox
# checkout — a placeholder for local/dev convenience only. Every real
# deployment (including the LAN server) is expected to set
# VIDEO_STORAGE_DIR explicitly rather than rely on this fallback.
_DEV_FALLBACK_VIDEO_STORAGE_DIR = str(Path.home() / "neurolearn_videos")

VIDEO_STORAGE_DIR = os.getenv("VIDEO_STORAGE_DIR", _DEV_FALLBACK_VIDEO_STORAGE_DIR)

ALLOWED_VIDEO_EXTENSIONS = tuple(
    ext.strip().lower()
    for ext in os.getenv("ALLOWED_VIDEO_EXTENSIONS", ".mp4,.webm").split(",")
    if ext.strip()
)

_warned_missing_env = False


def get_video_storage_root() -> Path:
    """Resolve VIDEO_STORAGE_DIR to an absolute Path, creating it if it
    doesn't exist yet. Resolved lazily (not at import time) so importing
    this module never has filesystem side effects, and so a changed env
    var is always picked up freshly rather than cached at import.
    """
    global _warned_missing_env
    if not os.getenv("VIDEO_STORAGE_DIR") and not _warned_missing_env:
        logger.warning(
            "VIDEO_STORAGE_DIR is not set in the environment — falling back "
            f"to {_DEV_FALLBACK_VIDEO_STORAGE_DIR}. This fallback is a local "
            "dev convenience only: set VIDEO_STORAGE_DIR explicitly to the "
            "server's real video storage location for LAN deployment."
        )
        _warned_missing_env = True

    root = Path(VIDEO_STORAGE_DIR).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def nginx_url_to_relative_path(url: str) -> str | None:
    """Inverse of get_nginx_video_url(): if `url` is one of our own
    Nginx-served local video URLs, returns the relative path portion;
    otherwise (a YouTube URL, or anything else) returns None.

    Used by ml/transcription_model.py (Phase 5) to decide whether a
    video_url can be read directly from VIDEO_STORAGE_DIR instead of
    downloaded via yt-dlp — the only thing that changes about a video's
    *source*; caching/locking/Whisper logic is identical either way.
    """
    base = os.getenv("NGINX_VIDEO_BASE_URL", "http://SERVER_LAN_IP:8080/media").rstrip("/")
    if not url or not url.startswith(base + "/"):
        return None
    return url[len(base) + 1:]


def get_nginx_video_url(relative_path: str) -> str:
    """Builds the public, LAN-reachable URL a client uses to play a video
    — NGINX_VIDEO_BASE_URL (see nginx/render_config.sh, Phase 3) joined
    with the video's validated relative path. This is the only place a
    video_links[].url is constructed in V2 — never a YouTube URL, never
    hand-entered by a student (see routers/courses.py attach-video
    endpoint, admin-only).
    """
    base = os.getenv("NGINX_VIDEO_BASE_URL", "http://SERVER_LAN_IP:8080/media").rstrip("/")
    return f"{base}/{relative_path.lstrip('/')}"
