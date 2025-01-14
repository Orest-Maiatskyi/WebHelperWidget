from datetime import datetime

from app.database.dao.base import Base
from app.database.models import ApiKeyModel


class ApiKey(Base):

    @staticmethod
    def create_api_key(user_uuid: str, key: str | None = None, name: str | None = None,
                       domains: dict | None = None, is_deleted: bool | None = None,
                       deleted_at: datetime | None = None) -> None:
        ApiKey.insert(ApiKeyModel(
            key=key,
            name=name,
            domains=domains,
            is_deleted=is_deleted,
            deleted_at=deleted_at,
            user_uuid=user_uuid
        ))

    @staticmethod
    def get_api_key_by_id(_id: int | str) -> ApiKeyModel | None:
        return ApiKey.scalar_query(ApiKeyModel.query.where(ApiKeyModel.id == _id))

    @staticmethod
    def get_api_key_by_uuid(uuid: str) -> ApiKeyModel | None:
        return ApiKey.scalar_query(ApiKeyModel.query.where(ApiKeyModel.uuid == uuid))

    @staticmethod
    def get_all_api_keys_by_user_uuid(user_uuid: str) -> list[ApiKeyModel]:
        return ApiKey.scalars_query(ApiKeyModel.query.where(ApiKeyModel.user_uuid == user_uuid).all())
