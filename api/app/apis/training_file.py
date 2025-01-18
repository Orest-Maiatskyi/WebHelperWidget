from io import BytesIO

from flask import Blueprint, send_file, Response
from flask_jwt_extended import jwt_required
from werkzeug.datastructures import FileStorage

from app import openai
from app.apis.utils import View, arg_parser, uuid4_regexp, JsonL, JsonLException
from app.database import FineTuningDAO

training_file_bp = Blueprint('training_file', __name__)


class TrainingFile(View):
    @jwt_required()
    @arg_parser({'api_key_uuid': uuid4_regexp})
    def get(self, api_key_uuid: str) -> tuple[dict, int] | Response:
        """
        Retrieve the content of a training file associated with the provided API key UUID.

        :param api_key_uuid: The UUID of the API key.

        :return: tuple[dict, int] | Response: JSON response with the file content (200) or error message (404).
        """
        fine_tuning = FineTuningDAO.get_fine_tuning_by_api_key_uuid(api_key_uuid)
        if fine_tuning is None:
            return {'error': 'Not Found', 'message': f"Api key with uuid: {api_key_uuid} wasn't found."}, 404
        if fine_tuning.training_file_uuid is None:
            return {'error': 'Not Found', 'message': 'The training file has not been uploaded yet.'}, 404

        file = openai.client.files.content(file_id=fine_tuning.training_file_uuid).content
        return send_file(BytesIO(file), mimetype='application/jsonl')

    @jwt_required()
    @arg_parser({'api_key_uuid': uuid4_regexp}, file_required='jsonl')
    def post(self, api_key_uuid: str, jsonl_file: FileStorage):
        """
        Upload a new training file for fine-tuning.

        :param api_key_uuid: The UUID of the API key.
        :param jsonl_file: The uploaded JSONL file.

        :return: tuple[dict, int]: JSON response indicating success (200) or failure (400/404/500).
        """
        file = jsonl_file.read()
        try:
            JsonL().load_dataset(file)
        except JsonLException as e:
            return {'error': 'Bad Request', 'message': f'Training file is incorrect.\n{e.message}'}, 400

        fine_tuning = FineTuningDAO.get_fine_tuning_by_api_key_uuid(api_key_uuid)
        if fine_tuning is None:
            return {'error': 'Not Found', 'message': f"Api key with uuid: {api_key_uuid} wasn't found."}, 404

        try:
            training_file = openai.client.files.create(file=file, purpose='fine-tune')
            fine_tuning.training_file_uuid = training_file.id
            FineTuningDAO.commit()
            return {'message': 'Training file uploaded.'}, 200
        except Exception as ignore:
            return {'error': 'Internal Server Error', 'message': 'Unable to save training file.'}, 500

    @jwt_required()
    @arg_parser({'api_key_uuid': uuid4_regexp})
    def delete(self, api_key_uuid):
        """
        Delete an existing training file associated with the provided API key UUID.

        :param api_key_uuid: The UUID of the API key.

        :return: tuple[dict, int]: JSON response indicating success (200) or failure (404/500).
        """
        fine_tuning = FineTuningDAO.get_fine_tuning_by_api_key_uuid(api_key_uuid)
        if fine_tuning is None:
            return {'error': 'Not Found', 'message': f"Api key with uuid: {api_key_uuid} wasn't found."}, 404
        if fine_tuning.training_file_uuid is None:
            return {'error': 'Not Found', 'message': 'The training file has not been uploaded yet.'}, 404

        try:
            openai.client.files.delete(fine_tuning.training_file_uuid)
            fine_tuning.training_file_uuid = None
            FineTuningDAO.commit()
            return {'message': 'Training file deleted successfully.'}, 200
        except Exception as ignore:
            return {'error': 'Internal Server Error', 'message': 'Unable to delete training file.'}, 500


training_file_bp.add_url_rule('/', view_func=TrainingFile.as_view('training_file'))
