import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)