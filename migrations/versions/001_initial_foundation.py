"""initial foundation

Revision ID: 001_initial_foundation
Revises:
Create Date: 2026-09-20 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "001_initial_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONType = sa.JSON().with_variant(JSONB, "postgresql")


def upgrade() -> None:
    # 1. candidate_profile
    op.create_table(
        "candidate_profile",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("structured_profile_json", JSONType, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. source_account
    op.create_table(
        "source_account",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("external_account_hint", sa.String(length=255), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "profile_status", sa.String(length=64), nullable=False, server_default="not_verified"
        ),
        sa.Column(
            "alert_status", sa.String(length=64), nullable=False, server_default="not_verified"
        ),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. source_alert
    op.create_table(
        "source_alert",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_account_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("query_json", JSONType, nullable=False),
        sa.Column("cadence", sa.String(length=32), nullable=False, server_default="daily"),
        sa.Column("email_match_rule", sa.String(length=255), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["source_account_id"], ["source_account.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. inbound_message
    op.create_table(
        "inbound_message",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=False),
        sa.Column("provider_thread_id", sa.String(length=255), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sender", sa.String(length=255), nullable=False),
        sa.Column("recipients_json", JSONType, nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False, server_default="inbound"),
        sa.Column("subject", sa.String(length=512), nullable=False),
        sa.Column("headers_json", JSONType, nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("body_html_hash", sa.String(length=64), nullable=True),
        sa.Column("classification", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("raw_reference", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_message_id"),
    )
    op.create_index(
        "ix_inbound_message_provider_message_id", "inbound_message", ["provider_message_id"]
    )
    op.create_index(
        "ix_inbound_message_provider_thread_id", "inbound_message", ["provider_thread_id"]
    )

    # 5. company
    op.create_table(
        "company",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("aliases_json", JSONType, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_normalized_name", "company", ["normalized_name"])
    op.create_index("ix_company_domain", "company", ["domain"])

    # 6. job
    op.create_table(
        "job",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("normalized_title", sa.String(length=255), nullable=False),
        sa.Column("location_text", sa.String(length=255), nullable=True),
        sa.Column("remote_type", sa.String(length=64), nullable=True),
        sa.Column("employment_type", sa.String(length=64), nullable=True),
        sa.Column("compensation_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("compensation_max", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "compensation_currency", sa.String(length=8), nullable=False, server_default="USD"
        ),
        sa.Column("description_text", sa.Text(), nullable=True),
        sa.Column("description_hash", sa.String(length=64), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="discovered"),
        sa.ForeignKeyConstraint(["company_id"], ["company.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_normalized_title", "job", ["normalized_title"])
    op.create_index("ix_job_description_hash", "job", ["description_hash"])

    # 7. job_source
    op.create_table(
        "job_source",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("source_job_id", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("canonical_apply_url", sa.String(length=1024), nullable=True),
        sa.Column("requisition_id", sa.String(length=128), nullable=True),
        sa.Column("source_payload_json", JSONType, nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["job.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_source_source_job_id", "job_source", ["source_job_id"])
    op.create_index("ix_job_source_canonical_apply_url", "job_source", ["canonical_apply_url"])
    op.create_index("ix_job_source_requisition_id", "job_source", ["requisition_id"])

    # 8. job_evaluation
    op.create_table(
        "job_evaluation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column("rules_version", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("reason_codes_json", JSONType, nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("model_provider", sa.String(length=64), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["job.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 9. artifact
    op.create_table(
        "artifact",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("storage_uri", sa.String(length=1024), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", JSONType, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 10. application_packet
    op.create_table(
        "application_packet",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_profile_version", sa.Integer(), nullable=False),
        sa.Column("resume_artifact_id", sa.Uuid(), nullable=True),
        sa.Column("cover_letter_artifact_id", sa.Uuid(), nullable=True),
        sa.Column("answers_json", JSONType, nullable=False),
        sa.Column("unresolved_questions_json", JSONType, nullable=False),
        sa.Column("packet_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["cover_letter_artifact_id"], ["artifact.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["job.id"]),
        sa.ForeignKeyConstraint(["resume_artifact_id"], ["artifact.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 11. application
    op.create_table(
        "application",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="DISCOVERED"),
        sa.Column(
            "application_mode", sa.String(length=32), nullable=False, server_default="manual"
        ),
        sa.Column("destination_domain", sa.String(length=255), nullable=True),
        sa.Column(
            "policy_decision", sa.String(length=32), nullable=False, server_default="blocked"
        ),
        sa.Column("policy_version", sa.String(length=64), nullable=True),
        sa.Column("packet_id", sa.Uuid(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["job.id"]),
        sa.ForeignKeyConstraint(["packet_id"], ["application_packet.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 12. application_event
    op.create_table(
        "application_event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_reference", sa.String(length=255), nullable=True),
        sa.Column("payload_json", JSONType, nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["application.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 13. message_link
    op.create_table(
        "message_link",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("inbound_message_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("method", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["application.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["company.id"]),
        sa.ForeignKeyConstraint(["inbound_message_id"], ["inbound_message.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["job.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 14. contact
    op.create_table(
        "contact",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=128), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("first_contact_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_contact_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["company.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contact_email", "contact", ["email"])

    # 15. interview
    op.create_table(
        "interview",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("round_type", sa.String(length=64), nullable=False),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("location_or_link", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="scheduled"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["application.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 16. task
    op.create_table(
        "task",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("payload_json", JSONType, nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["application.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["job.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 17. policy_registry
    op.create_table(
        "policy_registry",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.Column("domain_pattern", sa.String(length=255), nullable=False),
        sa.Column("adapter", sa.String(length=64), nullable=True),
        sa.Column("capability", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False, server_default="blocked"),
        sa.Column("evidence_url", sa.String(length=1024), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 18. audit_log
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("actor", sa.String(length=64), nullable=False, server_default="system"),
        sa.Column("input_hash", sa.String(length=64), nullable=True),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", JSONType, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("policy_registry")
    op.drop_table("task")
    op.drop_table("interview")
    op.drop_table("contact")
    op.drop_table("message_link")
    op.drop_table("application_event")
    op.drop_table("application")
    op.drop_table("application_packet")
    op.drop_table("artifact")
    op.drop_table("job_evaluation")
    op.drop_table("job_source")
    op.drop_table("job")
    op.drop_table("company")
    op.drop_table("inbound_message")
    op.drop_table("source_alert")
    op.drop_table("source_account")
    op.drop_table("candidate_profile")
