
from sqlalchemy import text

from backend.app.models.base import Base
from backend.app.models import (  # noqa: F401
    Diagnosis,
    Evidence,
    Incident,
    IncidentLog,
    InvestigationStep,
    Log,
)


def test_database_connection(test_engine):
    with test_engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar_one()

    assert result == 1


def test_expected_tables_are_registered():
    expected_tables = {
        "incidents",
        "logs",
        "incident_logs",
        "diagnoses",
        "evidence",
        "investigation_steps",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())
