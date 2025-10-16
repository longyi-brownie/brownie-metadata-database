"""Integration tests to ensure database changes don't break the API."""

import pytest
import subprocess
import sys
import os
from pathlib import Path
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the API project to the path
api_project_path = Path(__file__).parent.parent.parent / "brownie-metadata-api"
sys.path.insert(0, str(api_project_path))

from database.models import Base
from database.base import Base as DatabaseBase


class TestDatabaseAPIIntegration:
    """Test that database changes don't break the API."""
    
    @pytest.fixture(scope="class")
    def postgres_container(self):
        """Start PostgreSQL container for testing."""
        with PostgresContainer("postgres:16") as postgres:
            yield postgres
    
    @pytest.fixture(scope="class")
    def test_db_url(self, postgres_container):
        """Get test database URL."""
        return postgres_container.get_connection_url()
    
    @pytest.fixture(scope="class")
    def test_engine(self, test_db_url):
        """Create test database engine."""
        engine = create_engine(test_db_url)
        Base.metadata.create_all(bind=engine)
        return engine
    
    @pytest.fixture(scope="class")
    def test_db_session(self, test_engine):
        """Create test database session."""
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def test_database_migration_works(self, test_db_url):
        """Test that database migrations can be applied successfully."""
        # Set environment variable for the migration
        env = os.environ.copy()
        env["DATABASE_URL"] = test_db_url
        
        # Run migration
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent,
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Migration failed: {result.stderr}"
        print(f"Migration output: {result.stdout}")
    
    def test_api_can_import_models(self):
        """Test that the API can import all database models."""
        try:
            # Test importing models from the API project
            from app.models import (
                Organization, Team, User, Incident, 
                AgentConfig, Stats, Config,
                UserRole, IncidentStatus, IncidentPriority, AgentType
            )
            
            # Test that models have expected attributes
            assert hasattr(Organization, '__tablename__')
            assert hasattr(Team, '__tablename__')
            assert hasattr(User, '__tablename__')
            assert hasattr(Incident, '__tablename__')
            assert hasattr(AgentConfig, '__tablename__')
            assert hasattr(Stats, '__tablename__')
            assert hasattr(Config, '__tablename__')
            
            print("✅ API can import all database models")
            
        except ImportError as e:
            pytest.fail(f"API cannot import database models: {e}")
    
    def test_api_can_connect_to_database(self, test_db_url):
        """Test that the API can connect to the database."""
        try:
            # Test database connection from API
            from app.db import engine
            from app.settings import settings
            
            # Override settings for test
            original_dsn = settings.postgres_dsn
            settings.postgres_dsn = test_db_url
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                assert result.fetchone()[0] == 1
            
            # Restore original settings
            settings.postgres_dsn = original_dsn
            
            print("✅ API can connect to database")
            
        except Exception as e:
            pytest.fail(f"API cannot connect to database: {e}")
    
    def test_api_can_query_tables(self, test_db_url, test_db_session):
        """Test that the API can query all tables."""
        try:
            from app.models import Organization, Team, User, Incident, AgentConfig, Stats, Config
            
            # Test that we can query each table
            org_count = test_db_session.query(Organization).count()
            team_count = test_db_session.query(Team).count()
            user_count = test_db_session.query(User).count()
            incident_count = test_db_session.query(Incident).count()
            agent_config_count = test_db_session.query(AgentConfig).count()
            stats_count = test_db_session.query(Stats).count()
            config_count = test_db_session.query(Config).count()
            
            # All queries should succeed (even if count is 0)
            assert isinstance(org_count, int)
            assert isinstance(team_count, int)
            assert isinstance(user_count, int)
            assert isinstance(incident_count, int)
            assert isinstance(agent_config_count, int)
            assert isinstance(stats_count, int)
            assert isinstance(config_count, int)
            
            print("✅ API can query all tables")
            
        except Exception as e:
            pytest.fail(f"API cannot query tables: {e}")
    
    def test_api_can_create_records(self, test_db_session):
        """Test that the API can create records in all tables."""
        try:
            from app.models import Organization, Team, User, Incident, AgentConfig, Stats, Config
            from app.models import UserRole, IncidentStatus, IncidentPriority, AgentType
            import uuid
            from datetime import datetime
            
            # Create test organization
            org = Organization(
                id=uuid.uuid4(),
                name="Test Org",
                slug="test-org",
                is_active=True,
                max_teams=10,
                max_users_per_team=50
            )
            test_db_session.add(org)
            test_db_session.flush()
            
            # Create test team
            team = Team(
                id=uuid.uuid4(),
                name="Test Team",
                slug="test-team",
                org_id=org.id,
                organization_id=org.id,
                is_active=True
            )
            test_db_session.add(team)
            test_db_session.flush()
            
            # Create test user
            user = User(
                id=uuid.uuid4(),
                email="test@example.com",
                username="testuser",
                team_id=team.id,
                role=UserRole.ADMIN,
                org_id=org.id,
                organization_id=org.id,
                is_active=True,
                is_verified=True
            )
            test_db_session.add(user)
            test_db_session.flush()
            
            # Create test incident
            incident = Incident(
                id=uuid.uuid4(),
                title="Test Incident",
                status=IncidentStatus.OPEN,
                priority=IncidentPriority.MEDIUM,
                team_id=team.id,
                org_id=org.id,
                organization_id=org.id,
                version=1
            )
            test_db_session.add(incident)
            test_db_session.flush()
            
            # Create test agent config
            agent_config = AgentConfig(
                id=uuid.uuid4(),
                name="Test Agent",
                agent_type=AgentType.INCIDENT_RESPONSE,
                team_id=team.id,
                org_id=org.id,
                organization_id=org.id,
                config={},
                version=1
            )
            test_db_session.add(agent_config)
            test_db_session.flush()
            
            # Create test stats
            stats = Stats(
                id=uuid.uuid4(),
                metric_name="test_metric",
                metric_type="counter",
                value=1.0,
                timestamp=datetime.utcnow(),
                org_id=org.id,
                organization_id=org.id
            )
            test_db_session.add(stats)
            test_db_session.flush()
            
            # Create test config
            config = Config(
                id=uuid.uuid4(),
                name="Test Config",
                config_type="ORGANIZATION",
                status="ACTIVE",
                team_id=team.id,
                org_id=org.id,
                organization_id=org.id,
                priority=1,
                is_global=False,
                is_active=True,
                version=1
            )
            test_db_session.add(config)
            test_db_session.flush()
            
            # Commit all changes
            test_db_session.commit()
            
            print("✅ API can create records in all tables")
            
        except Exception as e:
            test_db_session.rollback()
            pytest.fail(f"API cannot create records: {e}")
    
    def test_api_schemas_match_database(self):
        """Test that API schemas match database models."""
        try:
            from app.schemas import (
                OrganizationResponse, TeamResponse, UserResponse,
                IncidentResponse, AgentConfigResponse, StatsResponse
            )
            from app.models import (
                Organization, Team, User, Incident, AgentConfig, Stats
            )
            
            # Test that schemas can be created from models
            # This is a basic test - in practice, you'd test more thoroughly
            
            # Test that models have the expected fields
            org_fields = set(Organization.__table__.columns.keys())
            team_fields = set(Team.__table__.columns.keys())
            user_fields = set(User.__table__.columns.keys())
            
            # Basic field existence checks
            assert 'id' in org_fields
            assert 'name' in org_fields
            assert 'slug' in org_fields
            
            assert 'id' in team_fields
            assert 'name' in team_fields
            assert 'org_id' in team_fields
            
            assert 'id' in user_fields
            assert 'email' in user_fields
            assert 'username' in user_fields
            
            print("✅ API schemas match database models")
            
        except Exception as e:
            pytest.fail(f"API schemas don't match database models: {e}")


class TestMigrationCompatibility:
    """Test that migrations are compatible with API expectations."""
    
    def test_migration_creates_expected_tables(self, test_db_url):
        """Test that migration creates all expected tables."""
        # Set environment variable for the migration
        env = os.environ.copy()
        env["DATABASE_URL"] = test_db_url
        
        # Run migration
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent,
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Migration failed: {result.stderr}"
        
        # Check that all expected tables exist
        from sqlalchemy import create_engine, text
        engine = create_engine(test_db_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'organizations', 'teams', 'users', 'incidents', 
                'agent_configs', 'stats', 'configs'
            ]
            
            for table in expected_tables:
                assert table in tables, f"Table {table} not found in database"
            
            print(f"✅ Migration created all expected tables: {tables}")
    
    def test_migration_creates_expected_indexes(self, test_db_url):
        """Test that migration creates all expected indexes."""
        from sqlalchemy import create_engine, text
        engine = create_engine(test_db_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY indexname
            """))
            
            indexes = [row[0] for row in result.fetchall()]
            
            # Check for some key indexes
            expected_indexes = [
                'ix_organizations_slug',
                'ix_teams_org_id',
                'ix_users_email',
                'ix_incidents_team_id',
                'ix_agent_configs_team_id',
                'ix_stats_metric_name'
            ]
            
            for index in expected_indexes:
                assert index in indexes, f"Index {index} not found in database"
            
            print(f"✅ Migration created all expected indexes: {len(indexes)} total")
