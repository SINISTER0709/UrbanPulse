import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
settings.ENVIRONMENT = "testing"
from app.main import app
from app.db.session import get_db
from app.models.base import Base
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import hash_password, create_access_token

# In-memory SQLite for reliable, lightning-fast isolated unit and integration tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def citizen_user(db_session):
    user = User(
        id="citizen-uuid-0001",
        email="citizen@urbanpulse.local",
        hashed_password=hash_password("citizen_pass_123"),
        full_name="Jane Citizen",
        role=UserRole.Citizen,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def citizen_token(citizen_user):
    return create_access_token(
        data={"sub": citizen_user.id, "email": citizen_user.email, "role": citizen_user.role.value}
    )


@pytest.fixture
def admin_user(db_session):
    user = User(
        id="admin-uuid-0001",
        email="admin@urbanpulse.local",
        hashed_password=hash_password("admin_pass_123"),
        full_name="Chief Admin",
        role=UserRole.Admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(
        data={"sub": admin_user.id, "email": admin_user.email, "role": admin_user.role.value}
    )


@pytest.fixture
def department_user(db_session):
    user = User(
        id="dept-uuid-0001",
        email="dept@urbanpulse.local",
        hashed_password=hash_password("dept_pass_123"),
        full_name="Public Works Officer",
        role=UserRole.Department,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def department_token(department_user):
    return create_access_token(
        data={"sub": department_user.id, "email": department_user.email, "role": department_user.role.value}
    )
