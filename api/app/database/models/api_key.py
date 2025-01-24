import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db
from app.database.utils import SerializableMixin


class ApiKey(db.Model, SerializableMixin):
    __tablename__ = 'api_keys'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    key: Mapped[str] = mapped_column(String(32), unique=True, nullable=False,
                                     default=lambda: str(uuid.uuid4()).replace('-', ''))
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    domains: Mapped[dict] = mapped_column(JSON, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc).isoformat(), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user_uuid: Mapped[str] = mapped_column(String(36), ForeignKey('users.uuid'), nullable=False)
    user = relationship('User', back_populates='api_keys')

    fine_tuning = relationship('FineTuning', back_populates='api_key', cascade='all, delete-orphan')
