from datetime import datetime

from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt

from app.apis.utils import View, arg_parser, uuid4_regexp, math_captcha, api_key_name_regexp, api_key_domains_regexp
from app.database import ApiKeyDAO

api_key_bp = Blueprint('api_key', __name__)


class ApiKey(View):

    @jwt_required()
    def get(self) -> tuple[dict, int]:
        """
        Handles GET requests to fetch all API keys (that are not deleted) associated with the authenticated user.

        :return: A dictionary containing a list of active API keys (excluding deleted ones) and status code
        """
        api_keys = ApiKeyDAO.get_all_api_keys_by_user_uuid(get_jwt().get("sub"))
        return {'api_keys': [{
            'uuid': api_key.uuid,
            'key': api_key.key,
            'name': api_key.name,
            'domains': api_key.domains,
            'registered_at': api_key.registered_at
        } for api_key in api_keys if not api_key.is_deleted]}, 200

    @jwt_required()
    @arg_parser(optional_args={
        'name': api_key_name_regexp,
        'domains': api_key_domains_regexp
    })
    def post(self, name: str | None = None, domains: str | None = None) -> tuple[dict, int]:
        """
        Handles POST requests to create a new API key for the authenticated user.

        :param name: (Optional) The name for the API key. Validated using `api_key_name_regexp`.
        :param domains: (Optional) Comma-separated list of allowed domains. Validated using `api_key_domains_regexp`.

        :return: A dictionary indicating the result of the operation (success message).
        """
        ApiKeyDAO.create_api_key(user_uuid=get_jwt().get("sub"), key=name, domains=domains)
        return {'message': 'Api key created successfully!'}, 201

    @jwt_required(fresh=True)
    @arg_parser(
        required_args={
            'uuid': uuid4_regexp
        },
        optional_args={
            'name': api_key_name_regexp,
            'domains': api_key_domains_regexp
        })
    def patch(self, uuid: str, name: str | None = None, domains: str | None = None) -> tuple[dict, int]:
        """
        Handles PATCH requests to update an existing API key's name or domains.

        :param uuid: The unique identifier of the API key to update. Validated using `uuid4_regexp`.
        :param name: (Optional) The new name for the API key.
        :param domains: (Optional) Comma-separated list of updated allowed domains.

        :return: A success message if the update is successful.
                 HTTP status code 404 if the API key is not found.
                 HTTP status code 200 on success.
        """
        api_key = ApiKeyDAO.get_api_key_by_uuid(uuid)

        if api_key is None:
            return {'error': 'Not Found', 'message': f"Api key with uuid: {uuid} wasn't found!"}, 404

        if name:
            api_key.name = name
        if domains:
            api_key.domains = domains

        ApiKeyDAO.commit()

        return {'message': 'Api key info updated!'}, 200

    @jwt_required(fresh=True)
    @math_captcha()
    @arg_parser(required_args={
        'uuid': uuid4_regexp
    })
    def delete(self, uuid: str) -> tuple[dict, int]:
        """
        Handles DELETE requests to mark an API key as deleted.

        :param uuid: The unique identifier of the API key to delete. Validated using `uuid4_regexp`.

        :return: A success message if the API key is marked as deleted.
                 HTTP status code 404 if the API key is not found.
                 HTTP status code 200 on success.
        """
        api_key = ApiKeyDAO.get_api_key_by_uuid(uuid)

        if api_key is None:
            return {'error': 'Not Found', 'message': f"Api key with uuid: {uuid} wasn't found!"}, 404

        api_key.is_deleted = True
        api_key.deleted_at = datetime.now()
        ApiKeyDAO.commit()

        return {'message': 'Account deleted successfully!'}, 200


api_key_bp.add_url_rule('/', view_func=ApiKey.as_view('api_key'))
