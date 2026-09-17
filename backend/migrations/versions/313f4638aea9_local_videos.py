"""local videos (V2 Phase 2)

Revision ID: 313f4638aea9
Revises: e5f8b1c3d704
Create Date: 2026-09-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "313f4638aea9"
down_revision: Union[str, Sequence[str], None] = "e5f8b1c3d704"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _create_index(name: str, table_name: str, columns: list[str], unique: bool = False) -> None:
    indexes = {idx["name"] for idx in sa.inspect(op.get_bind()).get_indexes(table_name)}
    if name not in indexes:
        op.create_index(name, table_name, columns, unique=unique)


def upgrade() -> None:
    if "local_videos" not in _tables():
        op.create_table(
            "local_videos",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("title", sa.String(), nullable=False),
            # Relative to the server's VIDEO_STORAGE_DIR (env-configured,
            # see config/video_config.py) — never an absolute path, never
            # a binary. Validated by services/video_path_safety.py before
            # any write; the CHECK constraints below are a defense-in-depth
            # backstop, not the primary validation path.
            sa.Column("relative_path", sa.String(), nullable=False, unique=True),
            sa.Column("course_id", sa.String(), sa.ForeignKey("courses.id"), nullable=True),
            sa.Column("duration_seconds", sa.Float(), nullable=True),
            sa.Column("file_size_bytes", sa.Integer(), nullable=True),
            sa.Column("order", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint("relative_path NOT LIKE '%..%'", name="ck_local_videos_no_traversal"),
            sa.CheckConstraint("relative_path NOT LIKE '/%'", name="ck_local_videos_not_absolute"),
        )
        _create_index("ix_local_videos_course_id", "local_videos", ["course_id"])


def downgrade() -> None:
    if "local_videos" in _tables():
        op.drop_table("local_videos")
