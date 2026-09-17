"""
============================================================
Admin authentication gate (V2, Phase 4)

All V2 course/video catalog content is managed exclusively through
admin-only endpoints (routers/courses.py, routers/videos.py) — there is
no hardcoded seed catalog and no student-facing way to add arbitrary
content or URLs.

This is intentionally a lightweight, additive gate — a single shared key
compared against the `X-Admin-Key` header — rather than a new role added
to the existing student-facing auth/security.py system. For a single-LAN,
~160-client research deployment with one operator, a shared admin key is
the smallest change that satisfies "admin-only"; it does not touch or
weaken the existing participant JWT auth in any way.

Set ADMIN_API_KEY in backend/.env before deploying. If it is unset, admin
endpoints are refused entirely (fail closed) rather than left open.
============================================================
"""

import os
import hmac

from fastapi import Header, HTTPException


def _get_admin_api_key() -> str | None:
    # Read on every call (not cached at import) so it behaves the same way
    # VIDEO_STORAGE_DIR does in config/video_config.py — tests and
    # deployments can set it without reimporting the module.
    return os.environ.get("ADMIN_API_KEY")


async def require_admin(x_admin_key: str = Header(default="")) -> None:
    """FastAPI dependency — raises 401/403 unless the request carries a
    valid X-Admin-Key header. Use via `Depends(require_admin)` on any
    endpoint that creates/deletes catalog content.
    """
    expected = _get_admin_api_key()
    if not expected:
        raise HTTPException(
            status_code=403,
            detail="Admin endpoints are disabled: ADMIN_API_KEY is not configured on the server.",
        )
    if not x_admin_key or not hmac.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Key header.")
