"""
Shared test configuration — single in-memory SQLite DB for all tests.

All test modules share this conftest so app dependency overrides and
the DB schema are set up once, consistently, before any test runs.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.auth import get_current_user_id

# Single persistent in-memory connection shared across all test modules
engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
_connection = engine.connect()
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_connection)
Base.metadata.create_all(bind=_connection)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def override_auth():
    return "test-owner-id"


# Apply overrides once at import time — all test modules benefit
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user_id] = override_auth
