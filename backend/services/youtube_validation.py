"""
services/youtube_validation.py — V2 (Phase 4, revised)

V2 removed all hardcoded/seeded YouTube content and every student-facing
"paste any URL" input. YouTube is reintroduced, but only as one of two
admin-curated video sources per course video: a local file (see
services/video_path_safety.py) or a YouTube link entered here, by the
admin, through routers/courses.py's admin-gated endpoint.

This is a shape check only (not a guarantee the video exists/is public)
— its job is to keep the admin YouTube-attach endpoint scoped to actual
YouTube URLs rather than becoming a reintroduced "paste any URL" hole.
"""
import re

_YOUTUBE_URL_RE = re.compile(
    r"^https?://(www\.|m\.)?(youtube\.com/(watch\?v=|embed/|shorts/)|youtu\.be/)[\w-]{6,}",
    re.IGNORECASE,
)


def is_youtube_url(url: str) -> bool:
    return bool(url) and bool(_YOUTUBE_URL_RE.match(url.strip()))
