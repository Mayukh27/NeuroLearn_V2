"""
============================================================
ROUTER: Courses — Course listing, details, video links, and
V2 admin content management (create/delete courses, attach/detach
local videos). Admin endpoints require X-Admin-Key (see
services/admin_auth.py) — there is no student-facing way to add,
remove, or point content at an arbitrary URL.

Endpoints:
    GET    /api/courses
    GET    /api/courses/{course_id}
    GET    /api/courses/{course_id}/videos/{video_id}
    POST   /api/courses                                          [admin]
    DELETE /api/courses/{course_id}                               [admin]
    POST   /api/courses/{course_id}/videos/youtube                [admin]
    POST   /api/courses/{course_id}/videos/{local_video_id}       [admin]
    DELETE /api/courses/{course_id}/video-links/{video_link_id}   [admin]
============================================================
"""

from fastapi import APIRouter, HTTPException, Depends
from schemas.models import Course, VideoLink, CourseCreate, CourseYoutubeVideoCreate
from data.database import (
    get_all_courses,
    get_course,
    create_course,
    delete_course,
    attach_local_video_to_course,
    attach_youtube_video_to_course,
    detach_video_from_course,
)
from services.admin_auth import require_admin
from services.youtube_validation import is_youtube_url

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get("/", response_model=list[Course])
async def list_courses():
    """Get all available courses with progress."""
    return get_all_courses()


@router.get("/{course_id}", response_model=Course)
async def get_course_detail(course_id: str):
    """Get a specific course with all video links."""
    course = get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{course_id}/videos/{video_id}")
async def get_video_detail(course_id: str, video_id: str):
    """Get a specific video within a course."""
    course = get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    video = next(
        (v for v in course.get("video_links", []) if v["id"] == video_id),
        None,
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return {"course": course, "video": video}


# ── Admin: course management (V2, Phase 4) ─────────────────────

@router.post("/", response_model=Course, status_code=201, dependencies=[Depends(require_admin)])
async def admin_create_course(body: CourseCreate):
    """Create a new (empty) course. Attach local videos to it afterward
    via POST /api/courses/{course_id}/videos/{local_video_id}.
    """
    return create_course(
        title=body.title,
        description=body.description,
        icon=body.icon,
        category=body.category,
        difficulty=body.difficulty,
        estimated_hours=body.estimated_hours,
        tags=body.tags,
    )


@router.delete("/{course_id}", status_code=204, dependencies=[Depends(require_admin)])
async def admin_delete_course(course_id: str):
    """Deletes the course. Does not delete any LocalVideo rows/files —
    those remain in the library and can be attached to another course.
    """
    if not delete_course(course_id):
        raise HTTPException(status_code=404, detail="Course not found")


@router.post("/{course_id}/videos/youtube", response_model=Course, dependencies=[Depends(require_admin)])
async def admin_attach_youtube_video(course_id: str, body: CourseYoutubeVideoCreate):
    """Attaches a YouTube video to this course's catalog by URL. This is
    the only way a YouTube URL enters V2 — admin-only, never seeded,
    never a student-facing "paste a URL" field. Videos in a course can
    be local (see the endpoint below) or YouTube, mixed freely.
    """
    if not is_youtube_url(body.youtube_url):
        raise HTTPException(
            status_code=400,
            detail="Not a recognizable YouTube URL (expected youtube.com/watch, youtu.be/, youtube.com/embed/, or /shorts/).",
        )
    course = get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return attach_youtube_video_to_course(
        course_id, title=body.title, youtube_url=body.youtube_url, order=body.order
    )


@router.post("/{course_id}/videos/{local_video_id}", response_model=Course, dependencies=[Depends(require_admin)])
async def admin_attach_video(course_id: str, local_video_id: str, title: str | None = None, order: int | None = None):
    """Attaches an already-registered local video (see POST /api/videos/)
    to this course's catalog. Builds the video_links[].url from the
    Nginx-served local video URL — never a hand-entered or YouTube URL.
    """
    course = attach_local_video_to_course(course_id, local_video_id, title=title, order=order)
    if not course:
        raise HTTPException(status_code=404, detail="Course or local video not found")
    return course


@router.delete("/{course_id}/video-links/{video_link_id}", response_model=Course, dependencies=[Depends(require_admin)])
async def admin_detach_video(course_id: str, video_link_id: str):
    """Removes a video from this course's catalog (by video_links[].id,
    not the underlying local video id). The LocalVideo row is untouched.
    """
    course = detach_video_from_course(course_id, video_link_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
