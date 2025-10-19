"""Initial migration

Revision ID: d607e412e7b0
Revises:
Create Date: 2025-10-15 20:46:57.628539

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d607e412e7b0"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("config_yaml", sa.Text(), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("config_version", sa.String(length=50), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("max_teams", sa.Integer(), nullable=False),
        sa.Column("max_users_per_team", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(
        op.f("ix_organizations_slug"), "organizations", ["slug"], unique=False
    )

    # Create teams table
    op.create_table(
        "teams",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("config_yaml", sa.Text(), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("config_version", sa.String(length=50), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("permissions", sa.JSON(), nullable=True),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teams_org_id"), "teams", ["org_id"], unique=False)
    op.create_index(
        op.f("ix_teams_organization_id"), "teams", ["organization_id"], unique=False
    )

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.UUID(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("oidc_subject", sa.String(length=255), nullable=True),
        sa.Column("oidc_provider", sa.String(length=100), nullable=True),
        sa.Column("team_id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("ADMIN", "MEMBER", "VIEWER", name="userrole"),
            nullable=False,
        ),
        sa.Column("preferences", sa.JSON(), nullable=True),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("oidc_subject"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(
        op.f("ix_users_oidc_subject"), "users", ["oidc_subject"], unique=False
    )
    op.create_index(op.f("ix_users_org_id"), "users", ["org_id"], unique=False)
    op.create_index(
        op.f("ix_users_organization_id"), "users", ["organization_id"], unique=False
    )
    op.create_index(op.f("ix_users_team_id"), "users", ["team_id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=False)

    # Create incidents table
    op.create_table(
        "incidents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "OPEN",
                "IN_PROGRESS",
                "RESOLVED",
                "CLOSED",
                "CANCELLED",
                name="incidentstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="incidentpriority"),
            nullable=False,
        ),
        sa.Column("assigned_to", sa.UUID(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("incident_metadata", sa.JSON(), nullable=True),
        sa.Column("response_time_minutes", sa.Integer(), nullable=True),
        sa.Column("resolution_time_minutes", sa.Integer(), nullable=True),
        sa.Column("team_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(
        op.f("ix_incidents_assigned_to"), "incidents", ["assigned_to"], unique=False
    )
    op.create_index(
        op.f("ix_incidents_created_by"), "incidents", ["created_by"], unique=False
    )
    op.create_index(op.f("ix_incidents_org_id"), "incidents", ["org_id"], unique=False)
    op.create_index(
        op.f("ix_incidents_organization_id"),
        "incidents",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incidents_team_id"), "incidents", ["team_id"], unique=False
    )
    op.create_index(
        op.f("ix_incidents_idempotency_key"),
        "incidents",
        ["idempotency_key"],
        unique=False,
    )

    # Create agent_configs table
    op.create_table(
        "agent_configs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "agent_type",
            sa.Enum(
                "INCIDENT_RESPONSE",
                "MONITORING",
                "ANALYSIS",
                "NOTIFICATION",
                "CUSTOM",
                name="agenttype",
            ),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("config_yaml", sa.Text(), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("config_version", sa.String(length=50), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("execution_timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("retry_delay_seconds", sa.Integer(), nullable=False),
        sa.Column("triggers", sa.JSON(), nullable=True),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("config_metadata", sa.JSON(), nullable=True),
        sa.Column("team_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_configs_org_id"), "agent_configs", ["org_id"], unique=False
    )
    op.create_index(
        op.f("ix_agent_configs_organization_id"),
        "agent_configs",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_configs_team_id"), "agent_configs", ["team_id"], unique=False
    )

    # Create stats table
    op.create_table(
        "stats",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("metric_name", sa.String(length=255), nullable=False),
        sa.Column("metric_type", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_window", sa.String(length=50), nullable=True),
        sa.Column("labels", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("team_id", sa.UUID(), nullable=True),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_stats_metric_name"), "stats", ["metric_name"], unique=False
    )
    op.create_index(op.f("ix_stats_timestamp"), "stats", ["timestamp"], unique=False)
    op.create_index(op.f("ix_stats_org_id"), "stats", ["org_id"], unique=False)
    op.create_index(
        op.f("ix_stats_organization_id"), "stats", ["organization_id"], unique=False
    )
    op.create_index(op.f("ix_stats_team_id"), "stats", ["team_id"], unique=False)

    # Create configs table
    op.create_table(
        "configs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "config_type",
            sa.Enum(
                "ORGANIZATION", "TEAM", "ALERT", "AGENT", "GLOBAL", name="configtype"
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "ACTIVE", "DEPRECATED", "ARCHIVED", name="configstatus"),
            nullable=False,
        ),
        sa.Column("name_pattern", sa.String(length=500), nullable=True),
        sa.Column("severity_pattern", sa.String(length=500), nullable=True),
        sa.Column("team_pattern", sa.String(length=500), nullable=True),
        sa.Column("config_yaml", sa.Text(), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("config_version", sa.String(length=50), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_global", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("config_metadata", sa.JSON(), nullable=True),
        sa.Column("team_id", sa.UUID(), nullable=True),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_configs_org_id"), "configs", ["org_id"], unique=False)
    op.create_index(
        op.f("ix_configs_organization_id"), "configs", ["organization_id"], unique=False
    )
    op.create_index(op.f("ix_configs_team_id"), "configs", ["team_id"], unique=False)
    op.create_index(
        op.f("ix_configs_config_type"), "configs", ["config_type"], unique=False
    )
    op.create_index(op.f("ix_configs_status"), "configs", ["status"], unique=False)
    op.create_index(op.f("ix_configs_priority"), "configs", ["priority"], unique=False)
    op.create_index(
        op.f("ix_configs_is_active"), "configs", ["is_active"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_configs_is_active"), table_name="configs")
    op.drop_index(op.f("ix_configs_priority"), table_name="configs")
    op.drop_index(op.f("ix_configs_status"), table_name="configs")
    op.drop_index(op.f("ix_configs_config_type"), table_name="configs")
    op.drop_index(op.f("ix_configs_team_id"), table_name="configs")
    op.drop_index(op.f("ix_configs_organization_id"), table_name="configs")
    op.drop_index(op.f("ix_configs_org_id"), table_name="configs")
    op.drop_table("configs")
    op.drop_index(op.f("ix_stats_team_id"), table_name="stats")
    op.drop_index(op.f("ix_stats_organization_id"), table_name="stats")
    op.drop_index(op.f("ix_stats_org_id"), table_name="stats")
    op.drop_index(op.f("ix_stats_timestamp"), table_name="stats")
    op.drop_index(op.f("ix_stats_metric_name"), table_name="stats")
    op.drop_table("stats")

    op.drop_index(op.f("ix_agent_configs_team_id"), table_name="agent_configs")
    op.drop_index(op.f("ix_agent_configs_organization_id"), table_name="agent_configs")
    op.drop_index(op.f("ix_agent_configs_org_id"), table_name="agent_configs")
    op.drop_table("agent_configs")

    op.drop_index(op.f("ix_incidents_idempotency_key"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_team_id"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_organization_id"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_org_id"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_created_by"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_assigned_to"), table_name="incidents")
    op.drop_table("incidents")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_team_id"), table_name="users")
    op.drop_index(op.f("ix_users_organization_id"), table_name="users")
    op.drop_index(op.f("ix_users_org_id"), table_name="users")
    op.drop_index(op.f("ix_users_oidc_subject"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_teams_organization_id"), table_name="teams")
    op.drop_index(op.f("ix_teams_org_id"), table_name="teams")
    op.drop_table("teams")

    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_table("organizations")

    # Drop enums (SQLAlchemy will handle this automatically)
