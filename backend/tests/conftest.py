
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models import (  # noqa: F401
    Diagnosis,
    Evidence,
    Incident,
    IncidentLog,
    InvestigationStep,
    Log,
)


@pytest.fixture(scope="session")
def test_engine():
    database_url = settings.database_url

    if not database_url.endswith("/incidentcopilot_test"):
        raise RuntimeError(
            "Tests must use the dedicated incidentcopilot_test database."
        )

    engine = create_engine(database_url, poolclass=NullPool)

    yield engine

    engine.dispose()


@pytest.fixture()
def db_session(test_engine) -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        join_transaction_mode="create_savepoint",
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)
