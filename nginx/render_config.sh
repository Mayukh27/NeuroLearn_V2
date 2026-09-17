#!/usr/bin/env bash
# Renders nginx/neurolearn_video.conf.template -> nginx/neurolearn_video.conf
# using VIDEO_STORAGE_DIR / NGINX_PORT / NGINX_VIDEO_CORS_ORIGIN from
# backend/.env, so the video server's storage dir and port stay driven by
# the SAME config source as FastAPI (config/video_config.py) instead of a
# second, easy-to-drift hardcoded copy.
#
# Usage:
#   ./render_config.sh [path/to/backend/.env]
#   (defaults to ../backend/.env relative to this script)
#
# Re-run this any time backend/.env changes, then reload nginx:
#   sudo nginx -t && sudo systemctl reload nginx
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ENV="${1:-$SCRIPT_DIR/../backend/.env}"

if [ -f "$BACKEND_ENV" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$BACKEND_ENV"
    set +a
else
    echo "WARNING: $BACKEND_ENV not found — relying on already-exported env vars." >&2
fi

: "${VIDEO_STORAGE_DIR:?VIDEO_STORAGE_DIR must be set in backend/.env (or the environment) — see PHASE_2_REPORT.md. Do NOT point this at a path inside this repo/checkout.}"
export VIDEO_STORAGE_DIR
export NGINX_PORT="${NGINX_PORT:-8080}"
export CORS_ORIGIN="${NGINX_VIDEO_CORS_ORIGIN:-*}"

mkdir -p "$VIDEO_STORAGE_DIR"

envsubst '${VIDEO_STORAGE_DIR} ${NGINX_PORT} ${CORS_ORIGIN}' \
    < "$SCRIPT_DIR/neurolearn_video.conf.template" \
    > "$SCRIPT_DIR/neurolearn_video.conf"

echo "Rendered $SCRIPT_DIR/neurolearn_video.conf"
echo "  VIDEO_STORAGE_DIR = $VIDEO_STORAGE_DIR"
echo "  NGINX_PORT        = $NGINX_PORT"
echo "  CORS_ORIGIN        = $CORS_ORIGIN"
echo
echo "Next steps (server machine):"
echo "  sudo cp $SCRIPT_DIR/neurolearn_video.conf /etc/nginx/sites-available/neurolearn_video.conf"
echo "  sudo ln -sf /etc/nginx/sites-available/neurolearn_video.conf /etc/nginx/sites-enabled/"
echo "  sudo nginx -t && sudo systemctl reload nginx"
