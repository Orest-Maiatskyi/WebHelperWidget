from datetime import datetime

from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt

from app.apis.utils import View, arg_parser, email_regexp, name_regexp, removal_reason_regexp, math_captcha, \
    authenticator
from app.database import UserDAO


_get_patch_delete_type = tuple[dict[str, str], int]


account_bp = Blueprint('account', __name__)


class Account(View):

    @authenticator()
    def get(self) -> _get_patch_delete_type:
        """
        This endpoint fetches the user data based on the JWT token and returns details such as
        UUID, first name, last name, email, and email verification status.

        :return: A dictionary containing user details or an error message if the user is not found.
        """
        user = UserDAO.get_user_by_uuid(get_jwt().get('sub'))
        if user is None:
            return {'error': 'Not Found', 'message': 'Invalid user UUID!'}, 404
        return {'uuid': user.uuid,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'email_verified': user.email_verified}, 200

    @authenticator(fresh=True)
    @arg_parser(optional_args={
        'first_name': name_regexp,
        'last_name': name_regexp,
        'email': email_regexp,
    })
    def patch(self, first_name: str | None = None,
              last_name: str | None = None, email: str | None = None) -> _get_patch_delete_type:
        """
        This endpoint allows users to update their account details such as first name, last name,
        and email address. The fields are optional and can be updated individually.

        :param first_name: Optional string, new first name of the user.
        :param last_name: Optional string, new last name of the user.
        :param email: Optional string, new email of the user.

        :return: A dictionary indicating the result of the operation (success message).
        """
        user = UserDAO.get_user_by_uuid(get_jwt().get('sub'))

        params = locals()
        params.pop("self", None)
        for field, value in params.items():
            if value is not None:  # TODO - change strict email replacement to email verification by adding to redis
                setattr(user, field, value)

        UserDAO.commit()
        return {'message': 'Account info updated!'}, 200

    @authenticator(fresh=True)
    @math_captcha()
    @arg_parser(optional_args={
        'removal_reason': removal_reason_regexp
    })
    def delete(self, removal_reason: str | None = None) -> _get_patch_delete_type:
        """
        This endpoint allows to set user's account marked as deleted in the database.

        :param removal_reason: Optional string, the reason for account removal.

        :return: A dictionary indicating the result of the operation (either captcha generation or success message).
        """

        if removal_reason is None:
            return {'error': 'Bad Request', 'message': 'Incorrect optional argument: removal_reason'}, 400

        user = UserDAO.get_user_by_uuid(get_jwt().get('sub'))
        user.is_deleted = True
        user.removal_reason = removal_reason
        user.deleted_at = datetime.now().isoformat()
        UserDAO.commit()

        return {'message': 'Account deleted successfully!'}, 200


account_bp.add_url_rule('/', view_func=Account.as_view('account'))
