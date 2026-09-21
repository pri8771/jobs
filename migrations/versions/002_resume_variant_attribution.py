"""resume variant attribution and packet provenance

Revision ID: 002_resume_variant_attribution
Revises: 001_initial_foundation
Create Date: 2026-09-20 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "002_resume_variant_attribution"
down_revision: str | None = "001_initial_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONType = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    # 1. create resume_variant table
    op.create_table(
        "resume_variant",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("resume_family", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parent_variant_id", sa.Uuid(), nullable=True),
        sa.Column("source_reference", sa.String(length=512), nullable=True),
        sa.Column("target_job_id", sa.Uuid(), nullable=True),
        sa.Column("target_role_family", sa.String(length=128), nullable=True),
        sa.Column("tailoring_method", sa.String(length=64), nullable=False, server_default="base"),
        sa.Column("model_provider", sa.String(length=64), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parent_variant_id"], ["resume_variant.id"]),
        sa.ForeignKeyConstraint(["target_job_id"], ["job.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resume_variant_resume_family"), "resume_variant", ["resume_family"], unique=False)
    op.create_index(op.f("ix_resume_variant_name"), "resume_variant", ["name"], unique=False)

    # 2. add resume_variant_id and answer_provenance_json to application_packet
    op.add_column("application_packet", sa.Column("resume_variant_id", sa.Uuid(), nullable=True))
    op.add_column(
        "application_packet",
        sa.Column("answer_provenance_json", JSONType, nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_foreign_key(
        "fk_application_packet_resume_variant_id",
        "application_packet",
        "resume_variant",
        ["resume_variant_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_application_packet_resume_variant_id", "application_packet", type_="foreignkey")
    op.drop_column("application_packet", "answer_provenance_json")
    op.drop_column("application_packet", "resume_variant_id")
    op.drop_index(op.f("ix_resume_variant_name"), table_name="resume_variant")
    op.drop_index(op.f("ix_resume_variant_resume_family"), table_name="resume_variant")
    op.drop_table("resume_variant")
