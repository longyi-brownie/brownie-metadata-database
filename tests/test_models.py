"""Test database models."""

import uuid
from datetime import datetime

import pytest

from database.models import AgentConfig, Incident, Organization, Stats, Team, User


class TestOrganization:
    """Test Organization model."""

    def test_create_organization(self, test_db, sample_org_id):
        """Test creating an organization."""
        org = Organization(
            id=sample_org_id,
            name="Test Org",
            slug="test-org",
            description="A test organization",
            is_active=True,
            max_teams=5,
            max_users_per_team=25,
        )
        test_db.add(org)
        test_db.commit()

        assert org.id == sample_org_id
        assert org.name == "Test Org"
        assert org.slug == "test-org"
        assert org.is_active is True
        assert org.created_at is not None
        assert org.updated_at is not None

    def test_organization_unique_constraints(self, test_db):
        """Test organization unique constraints."""
        org1 = Organization(
            name="Test Org",
            slug="test-org",
            is_active=True,
            max_teams=5,
            max_users_per_team=25,
        )
        test_db.add(org1)
        test_db.commit()

        # Try to create another org with same name
        org2 = Organization(
            name="Test Org",
            slug="different-slug",
            is_active=True,
            max_teams=5,
            max_users_per_team=25,
        )
        test_db.add(org2)

        with pytest.raises(Exception):  # Should raise integrity error
            test_db.commit()


class TestTeam:
    """Test Team model."""

    def test_create_team(self, test_db, sample_organization):
        """Test creating a team."""
        team = Team(
            org_id=sample_organization.id,
            organization_id=sample_organization.id,
            name="Test Team",
            slug="test-team",
            description="A test team",
            is_active=True,
        )
        test_db.add(team)
        test_db.commit()

        assert team.name == "Test Team"
        assert team.slug == "test-team"
        assert team.org_id == sample_organization.id
        assert team.organization_id == sample_organization.id
        assert team.is_active is True


class TestUser:
    """Test User model."""

    def test_create_user(self, test_db, sample_organization, sample_team):
        """Test creating a user."""
        user = User(
            org_id=sample_organization.id,
            organization_id=sample_organization.id,
            team_id=sample_team.id,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            is_active=True,
            is_verified=True,
        )
        test_db.add(user)
        test_db.commit()

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.org_id == sample_organization.id
        assert user.team_id == sample_team.id
        assert user.is_active is True
        assert user.is_verified is True

    def test_user_unique_constraints(self, test_db, sample_organization, sample_team):
        """Test user unique constraints."""
        user1 = User(
            org_id=sample_organization.id,
            organization_id=sample_organization.id,
            team_id=sample_team.id,
            email="test@example.com",
            username="testuser",
            is_active=True,
        )
        test_db.add(user1)
        test_db.commit()

        # Try to create another user with same email
        user2 = User(
            org_id=sample_organization.id,
            organization_id=sample_organization.id,
            team_id=sample_team.id,
            email="test@example.com",
            username="differentuser",
            is_active=True,
        )
        test_db.add(user2)

        with pytest.raises(Exception):  # Should raise integrity error
            test_db.commit()


class TestIncident:
    """Test Incident model."""

    def test_create_incident(
        self, test_db, sample_organization, sample_team, sample_user
    ):
        """Test creating an incident."""
        incident = Incident(
            org_id=sample_organization.id,
            organization_id=sample_organization.id,
            team_id=sample_team.id,
            created_by=sample_user.id,
            title="Test Incident",
            description="A test incident",
            status="OPEN",
            priority="MEDIUM",
        )
        test_db.add(incident)
        test_db.commit()

        assert incident.title == "Test Incident"
        assert incident.status == "OPEN"
        assert incident.priority == "MEDIUM"
        assert incident.org_id == sample_organization.id
        assert incident.team_id == sample_team.id
        assert incident.created_by == sample_user.id
        assert incident.version == 1  # Default version


class TestAgentConfig:
    """Test AgentConfig model."""

    def test_create_agent_config(self, test_db, sample_organization, sample_team):
        """Test creating an agent config."""
        config = AgentConfig(
            org_id=sample_organization.id,
            organization_id=sample_organization.id,
            team_id=sample_team.id,
            name="Test Agent",
            description="A test agent",
            agent_type="INCIDENT_RESPONSE",
            is_active=True,
            config={"test": "value"},
            execution_timeout_seconds=300,
            max_retries=3,
            retry_delay_seconds=60,
        )
        test_db.add(config)
        test_db.commit()

        assert config.name == "Test Agent"
        assert config.agent_type == "INCIDENT_RESPONSE"
        assert config.is_active is True
        assert config.config == {"test": "value"}
        assert config.version == 1  # Default version


class TestStats:
    """Test Stats model."""

    def test_create_stats(self, test_db, sample_organization, sample_team):
        """Test creating stats."""
        stats = Stats(
            org_id=sample_organization.id,
            organization_id=sample_organization.id,
            team_id=sample_team.id,
            metric_name="test_metric",
            metric_type="counter",
            value=42.0,
            count=1,
            timestamp=datetime.now(),
            time_window="1m",
            labels={"test": "value"},
            description="A test metric",
            unit="count",
        )
        test_db.add(stats)
        test_db.commit()

        assert stats.metric_name == "test_metric"
        assert stats.metric_type == "counter"
        assert stats.value == 42.0
        assert stats.org_id == sample_organization.id
        assert stats.team_id == sample_team.id
