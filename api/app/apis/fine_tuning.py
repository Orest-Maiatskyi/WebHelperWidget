from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.apis.utils import View, arg_parser, uuid4_regexp, authenticator
from app.database import FineTuningDAO


fine_tuning_bp = Blueprint('fine_tuning', __name__)


class FineTuning(View):

    @authenticator()
    @arg_parser({'api_key_uuid': uuid4_regexp})
    def get(self, api_key_uuid: str) -> tuple[dict[str, str], int]:
        """
        Retrieves fine-tuning details for a given API key UUID.

        Args:
            api_key_uuid (str): The UUID of the API key used to identify the fine-tuning job.
                                It is validated using a regex for UUID v4 format.

        Returns: A dictionary containing fine-tuning details or an error message if the uuid is not correct.
        """
        fine_tuning = FineTuningDAO.get_fine_tuning_by_uuid(api_key_uuid)
        if fine_tuning is None:
            return {'error': 'Not Found', 'message': 'Invalid fine_tuning UUID!'}, 404
        return {'uuid': fine_tuning.uuid,
                'training_file_uuid': fine_tuning.training_file_uuid,
                'job_uuid': fine_tuning.job_uuid,
                'tuned': fine_tuning.tuned,
                'last_file_upload': fine_tuning.last_file_upload,
                'last_tuned': fine_tuning.last_tuned,
                }, 200


fine_tuning_bp.add_url_rule('/', view_func=FineTuning.as_view('fine_tuning'))
