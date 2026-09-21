"""generation origin and live readiness gate

Revision ID: 003_generation_origin_readiness
Revises: 002_resume_variant_attribution
Create Date: 2026-09-20 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "003_generation_origin_readiness"
down_revision: str | None = "002_resume_variant_attribution"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONType = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    op.add_column(
        "application_packet",
        sa.Column("is_live_ready", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "application_packet",
        sa.Column(
            "generation_metadata_json",
            JSONType,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("application_packet", "generation_metadata_json")
    op.drop_column("application_packet", "is_live_ready")
