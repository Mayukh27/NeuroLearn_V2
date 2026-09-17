"""
============================================================
ROUTER: Local Videos (V2, Phase 2) — video METADATA only.
Video bytes are never served here — Nginx serves them directly from
VIDEO_STORAGE_DIR (see Phase 3). This router only ever touches
PostgreSQL metadata (data/database.py's LocalVideo functions) plus, for
existence checks, the filesystem via services/video_path_safety.py.

Endpoints:
    GET  /api/videos                      list local video metadata
    GET  /api/videos/{video_id}           one video's metadata
    POST /api/videos                      register a video already placed
                                           on disk under VIDEO_STORAGE_DIR   [admin]
    DELETE /api/videos/{video_id}         remove metadata row (not the file) [admin]
============================================================
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from schemas.models import LocalVideoCreate, LocalVideoOut
from data.database import (
    create_local_video, get_local_video, get_local_video_by_path,
    list_local_videos, delete_local_video,
)
from services.video_path_safety import (
    UnsafeVideoPathError, validate_relative_video_path, video_file_exists,
)
from services.admin_auth import require_admin

router = APIRouter(prefix="/api/videos", tags=["Local Videos"])


@router.get("/", response_model=list[LocalVideoOut])
async def list_videos(course_id: Optional[str] = None):
    """List local video metadata, optionally filtered by course."""
    return list_local_videos(course_id=course_id)


@router.get("/{video_id}", response_model=LocalVideoOut)
async def get_video(video_id: str):
    """Get one local video's metadata."""
    video = get_local_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Local video not found")
    return video


@router.post("/", response_model=LocalVideoOut, status_code=201, dependencies=[Depends(require_admin)])
async def register_video(payload: LocalVideoCreate):
    """Register metadata for a video file that has already been placed on
    the server filesystem under VIDEO_STORAGE_DIR (e.g. by whatever
    process copies/ingests the ~160-client course library onto the
    server). This endpoint does NOT upload or move any file — it only
    validates the given relative path and records metadata about it.
    """
    try:
        safe_path = validate_relative_video_path(payload.relative_path)
    except UnsafeVideoPathError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not video_file_exists(safe_path):
        raise HTTPException(
            status_code=404,
            detail=(
                f"No file found at VIDEO_STORAGE_DIR/{safe_path}. Place the "
                "video file on the server before registering its metadata."
            ),
        )

    if get_local_video_by_path(safe_path):
        raise HTTPException(
            status_code=409,
            detail=f"A video is already registered at {safe_path!r}.",
        )

    return create_local_video(
        title=payload.title,
        relative_path=safe_path,
        course_id=payload.course_id,
        duration_seconds=payload.duration_seconds,
        file_size_bytes=payload.file_size_bytes,
        order=payload.order,
    )


@router.delete("/{video_id}", status_code=204, dependencies=[Depends(require_admin)])
async def remove_video(video_id: str):
    """Delete a video's metadata row only. Never touches the file on disk."""
    if not delete_local_video(video_id):
        raise HTTPException(status_code=404, detail="Local video not found")
