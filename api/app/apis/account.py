from datetime import datetime
import time

from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt

from app.apis.utils import View, arg_parser, generate_math_problem, \
                            email_regexp, name_regexp, math_captcha_answer_regexp, removal_reason_regexp
from app.database import UserDAO
from app import redis_client, app


_get_patch_delete_type = tuple[dict[str, str], int]


account_bp = Blueprint('account', __name__)


class Account(View):

    @jwt_required()
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

    @jwt_required(fresh=True)
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

    @jwt_required(fresh=True)
    @arg_parser(optional_args={
        'captcha_answer': math_captcha_answer_regexp,
        'removal_reason': removal_reason_regexp
    })
    def delete(self, captcha_answer: str | None = None, removal_reason: str | None = None) -> _get_patch_delete_type:
        """
        This endpoint first checks if a valid captcha answer is provided. If not, it generates
        a new captcha for the user to answer. If the captcha answer is correct, and a removal
        reason is provided, the user's account is marked as deleted in the database.

        :param captcha_answer: Optional string, the answer to the math captcha for account deletion.
        :param removal_reason: Optional string, the reason for account removal.

        :return: A dictionary indicating the result of the operation (either captcha generation or success message).
        """
        def set_captcha():
            """
            Generates a new captcha for account deletion and stores the answer in Redis.

            :return: A dictionary containing the math captcha and a timestamp.
            """
            problem, result_ = generate_math_problem()
            redis_client.set(
                f'account-{get_jwt().get("sub")}-removal-captcha-answer',
                str(result_), app.config.get('MATH_CAPTCHA_DURATION'))
            return {'math_captcha': problem, 'timestamp': str(int(time.time()))}, 202

        if captcha_answer is None:
            return set_captcha()
        else:
            result = redis_client.get(f'account-{get_jwt().get("sub")}-removal-captcha-answer')
            if result is None or int(captcha_answer) != int(result):
                return set_captcha()

        if removal_reason is None:
            return {'error': 'Bad Request', 'message': 'Incorrect optional argument: removal_reason'}, 400

        redis_client.delete(f'account-{get_jwt().get("sub")}-removal-captcha-answer')

        user = UserDAO.get_user_by_uuid(get_jwt().get('sub'))
        user.is_deleted = True
        user.removal_reason = removal_reason
        user.deleted_at = datetime.now()
        UserDAO.commit()

        return {'message': 'Account deleted successfully!'}, 200


account_bp.add_url_rule('/', view_func=Account.as_view('account'))
