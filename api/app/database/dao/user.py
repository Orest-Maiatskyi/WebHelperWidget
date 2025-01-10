from typing import Union, Optional

from app.database.dao.base import Base
from app.database.models import UserModel


class User(Base):

    @staticmethod
    def create_user(first_name: str, last_name: str, email: str, password: str,
                    email_verified: Optional[str] = None) -> None:
        User.insert(UserModel(
            first_name=first_name,
            last_name=last_name,
            email=email,
            email_verified=email_verified,
            password=password,
        ))

    @staticmethod
    def get_user_by_id(_id: Union[int, str]) -> Optional[UserModel]:
        return User.scalar_query(UserModel.query.where(UserModel.id == _id))

    @staticmethod
    def get_user_by_uuid(uuid: Union[int, str]) -> Optional[UserModel]:
        return User.scalar_query(UserModel.query.where(UserModel.uuid == uuid))

    @staticmethod
    def get_user_by_email(email: str) -> Optional[UserModel]:
        return User.scalar_query(UserModel.query.where(UserModel.email == email))
