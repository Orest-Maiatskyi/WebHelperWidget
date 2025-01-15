from datetime import datetime

from app import db
from app.database.dao.base import Base
from app.database.models import ApiKeyModel, FineTuningModel


class ApiKey(Base):

    @staticmethod
    def create_api_key(user_uuid: str, key: str | None = None, name: str | None = None,
                       domains: dict | None = None, is_deleted: bool | None = None,
                       deleted_at: datetime | None = None) -> None:
        def transaction():
            api_key = ApiKeyModel(
                key=key,
                name=name,
                domains=domains,
                is_deleted=is_deleted,
                deleted_at=deleted_at,
                user_uuid=user_uuid)
            db.session.add(api_key)
            db.session.flush()
            fine_tuning = FineTuningModel(api_key_uuid=api_key.uuid)
            db.session.add(fine_tuning)
        ApiKey.transaction(transaction)

    @staticmethod
    def get_api_key_by_id(_id: int | str) -> ApiKeyModel | None:
        return ApiKey.scalar_query(ApiKeyModel.query.where(ApiKeyModel.id == _id))

    @staticmethod
    def get_api_key_by_uuid(uuid: str) -> ApiKeyModel | None:
        return ApiKey.scalar_query(ApiKeyModel.query.where(ApiKeyModel.uuid == uuid))

    @staticmethod
    def get_all_api_keys_by_user_uuid(user_uuid: str) -> list[ApiKeyModel]:
        return ApiKey.scalars_query(ApiKeyModel.query.where(ApiKeyModel.user_uuid == user_uuid).all())
