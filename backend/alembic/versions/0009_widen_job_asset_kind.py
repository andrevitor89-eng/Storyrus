"""widen jobs.type and assets.kind for EXTRA_CHARACTER

Revision ID: 0009_widen_job_asset_kind
Revises: 0008_project_extra_theme
Create Date: 2026-08-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_widen_job_asset_kind"
down_revision: Union[str, None] = "0008_project_extra_theme"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("jobs", "type", existing_type=sa.String(16), type_=sa.String(32), existing_nullable=False)
    op.alter_column(
        "assets", "kind", existing_type=sa.String(16), type_=sa.String(32), existing_nullable=False
    )


def downgrade() -> None:
    op.alter_column("jobs", "type", existing_type=sa.String(32), type_=sa.String(16), existing_nullable=False)
    op.alter_column(
        "assets", "kind", existing_type=sa.String(32), type_=sa.String(16), existing_nullable=False
    )
