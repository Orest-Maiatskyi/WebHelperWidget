from datetime import datetime

from app.database.dao.base import Base
from app.database.models import FineTuningModel


class FineTuning(Base):

    @staticmethod
    def create_fine_tuning(api_key_id: int | str, training_file_uuid: str | None = None,
                           job_uuid: str | None = None, tuned: bool | None = False,
                           last_file_upload: datetime | None = None, last_tuned: datetime | None = None) -> None:
        FineTuning.insert(FineTuningModel(
            api_key_id=api_key_id,
            training_file_uuid=training_file_uuid,
            job_uuid=job_uuid,
            tuned=tuned,
            last_file_upload=last_file_upload,
            last_tuned=last_tuned
        ))

    @staticmethod
    def get_fine_tuning_by_id(_id: int | str) -> FineTuningModel | None:
        return FineTuning.scalar_query(FineTuningModel.query.where(FineTuningModel.id == _id))

    @staticmethod
    def get_fine_tuning_by_uuid(uuid: str) -> FineTuningModel | None:
        return FineTuning.scalar_query(FineTuningModel.query.where(FineTuningModel.uuid == uuid))
