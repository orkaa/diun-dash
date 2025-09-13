import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database import Base, get_db


@pytest.fixture
def test_db():
    """Create a test database and return the engine and session."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    
    # Create test database engine
    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session factory
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    yield TestSessionLocal, test_engine
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def test_client(test_db):
    """Create a test client with test database."""
    TestSessionLocal, test_engine = test_db
    
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def sample_diun_webhook():
    """Sample DIUN webhook payload for testing."""
    return {
        "diun_version": "4.24.0",
        "hostname": "myserver",
        "status": "new",
        "provider": "file", 
        "image": "docker.io/crazymax/diun:latest",
        "hub_link": "https://hub.docker.com/r/crazymax/diun",
        "mime_type": "application/vnd.docker.distribution.manifest.list.v2+json",
        "digest": "sha256:216e3ae7de4ca8b553eb11ef7abda00651e79e537e85c46108284e5e91673e01",
        "created": "2020-03-26T12:23:56Z",
        "platform": "linux/amd64",
        "metadata": {
            "ctn_command": "diun serve",
            "ctn_createdat": "2022-12-29 10:22:15 +0100 CET",
            "ctn_id": "0dbd10e15b31add2c48856fd34451adabf50d276efa466fe19a8ef5fbd87ad7c",
            "ctn_names": "diun",
            "ctn_size": "0B",
            "ctn_state": "running",
            "ctn_status": "Up Less than a second (health: starting)"
        }
    }


@pytest.fixture
def webhook_token():
    """Test webhook token."""
    return "test-webhook-token"


@pytest.fixture
def set_webhook_token(webhook_token, monkeypatch):
    """Set the webhook token environment variable for tests."""
    monkeypatch.setenv("DIUN_WEBHOOK_TOKEN", webhook_token)
    return webhook_token