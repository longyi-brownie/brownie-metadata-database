"""Pytest configuration and fixtures."""

import os

# Add src to path
import sys
import uuid
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from database.base import Base
from database.config import DatabaseSettings
from database.models import AgentConfig, Incident, Organization, Stats, Team, User


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Get test database URL."""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_database_url: str):
    """Create test database engine."""
    engine = create_engine(
        test_database_url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    return engine


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def sample_org_id() -> uuid.UUID:
    """Sample organization ID for testing."""
    return uuid.uuid4()


@pytest.fixture
def sample_team_id() -> uuid.UUID:
    """Sample team ID for testing."""
    return uuid.uuid4()


@pytest.fixture
def sample_user_id() -> uuid.UUID:
    """Sample user ID for testing."""
    return uuid.uuid4()


@pytest.fixture
def sample_organization(test_db: Session, sample_org_id: uuid.UUID) -> Organization:
    """Create a sample organization for testing."""
    org = Organization(
        id=sample_org_id,
        name="Test Organization",
        slug="test-org",
        description="A test organization",
        is_active=True,
        max_teams=10,
        max_users_per_team=50,
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)
    return org


@pytest.fixture
def sample_team(
    test_db: Session, sample_team_id: uuid.UUID, sample_organization: Organization
) -> Team:
    """Create a sample team for testing."""
    team = Team(
        id=sample_team_id,
        org_id=sample_organization.id,
        organization_id=sample_organization.id,
        name="Test Team",
        slug="test-team",
        description="A test team",
        is_active=True,
    )
    test_db.add(team)
    test_db.commit()
    test_db.refresh(team)
    return team


@pytest.fixture
def sample_user(
    test_db: Session,
    sample_user_id: uuid.UUID,
    sample_organization: Organization,
    sample_team: Team,
) -> User:
    """Create a sample user for testing."""
    user = User(
        id=sample_user_id,
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
    test_db.refresh(user)
    return user


@pytest.fixture
def sample_incident(
    test_db: Session,
    sample_organization: Organization,
    sample_team: Team,
    sample_user: User,
) -> Incident:
    """Create a sample incident for testing."""
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
    test_db.refresh(incident)
    return incident


@pytest.fixture
def sample_agent_config(
    test_db: Session, sample_organization: Organization, sample_team: Team
) -> AgentConfig:
    """Create a sample agent config for testing."""
    config = AgentConfig(
        org_id=sample_organization.id,
        organization_id=sample_organization.id,
        team_id=sample_team.id,
        name="Test Agent",
        description="A test agent configuration",
        agent_type="INCIDENT_RESPONSE",
        is_active=True,
        config={"test": "value"},
        execution_timeout_seconds=300,
        max_retries=3,
        retry_delay_seconds=60,
    )
    test_db.add(config)
    test_db.commit()
    test_db.refresh(config)
    return config


@pytest.fixture
def sample_stats(
    test_db: Session, sample_organization: Organization, sample_team: Team
) -> Stats:
    """Create sample stats for testing."""
    stats = Stats(
        org_id=sample_organization.id,
        organization_id=sample_organization.id,
        team_id=sample_team.id,
        metric_name="test_metric",
        metric_type="counter",
        value=42.0,
        count=1,
        timestamp="2024-01-01T00:00:00Z",
        time_window="1m",
        labels={"test": "value"},
        description="A test metric",
        unit="count",
    )
    test_db.add(stats)
    test_db.commit()
    test_db.refresh(stats)
    return stats


@pytest.fixture
def test_settings() -> DatabaseSettings:
    """Test database settings."""
    return DatabaseSettings(
        host="localhost",
        port=5432,
        name="test_brownie_metadata",
        user="test",
        password="test",
    )
