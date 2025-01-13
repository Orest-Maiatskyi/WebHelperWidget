import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class User(db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    first_name: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    password: Mapped[str] = mapped_column(String(150), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    removal_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    blocked_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    api_keys = relationship('ApiKey', back_populates='user', cascade='all, delete-orphan')
