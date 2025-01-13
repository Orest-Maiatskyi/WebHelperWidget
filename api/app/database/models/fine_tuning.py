import uuid
from datetime import datetime

from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class FineTuning(db.Model):
    __tablename__ = 'fine_tuning'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    training_file_uuid: Mapped[str | None] = mapped_column(String(30), nullable=True)
    job_uuid: Mapped[str | None] = mapped_column(String(30), nullable=True)
    tuned: Mapped[bool] = mapped_column(Boolean(), default=False)

    last_file_upload: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_tuned: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    api_key_uuid: Mapped[str] = mapped_column(String(36), ForeignKey('api_keys.uuid'), nullable=False)
    api_key = relationship('ApiKey', back_populates='fine_tuning')
