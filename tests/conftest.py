import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app
from app.core.security import create_access_token

# SQLite in-memory database for isolated, lightning-fast tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh tables for every test function and drop afterward."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provide a database session connected to the test database."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Provide a FastAPI TestClient with the database dependency overridden."""
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
def test_user_data():
    return {
        "name": "Jane Doe",
        "email": "janedoe@example.com",
        "password": "SecurePassword123!"
    }


@pytest.fixture
def registered_user(client, test_user_data):
    """Registers a user and returns registration response and access token."""
    res = client.post("/api/auth/register", json=test_user_data)
    assert res.status_code == 201
    user_info = res.json()

    # Log in to get token
    login_res = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    return {
        "user": user_info,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


@pytest.fixture
def second_user(client):
    """Registers a second user for multi-tenancy / isolation testing."""
    user_data = {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "password": "AnotherPassword456!"
    }
    res = client.post("/api/auth/register", json=user_data)
    assert res.status_code == 201

    login_res = client.post("/api/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    token = login_res.json()["access_token"]

    return {
        "user": res.json(),
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }
