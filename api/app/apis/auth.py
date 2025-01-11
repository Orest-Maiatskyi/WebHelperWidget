from typing import Tuple, Dict

from flask import Blueprint, jsonify, Response
from flask_jwt_extended import create_access_token, jwt_required, create_refresh_token, get_jwt_identity, get_jwt

from app import bcrypt, redis_client, app
from app.apis.utils import View, arg_parser, email_regexp, password_regexp, name_regexp
from app.database import UserDAO


_get_post_type = tuple[dict[str, str], int] | tuple[Response, int]
_patch_type = tuple[Response, int]
_delete_type = Tuple[Dict[str, str], int]

auth_bp = Blueprint('auth', __name__)


class Auth(View):

    # Handles user login by validating email and password, and returning tokens if valid
    @arg_parser({'email': email_regexp, 'password': password_regexp})
    def get(self, email: str, password: str) -> _get_post_type:
        """
        Authenticates the user by checking email and password.
        Returns JWT tokens if the credentials are valid.

        :param email: The user's email address
        :param password: The user's password
        :return: JSON response with success or error message, and HTTP status code
        """
        user = UserDAO.get_user_by_email(email)
        if user is None or not bcrypt.check_password_hash(user.password, password):
            # Return error if email or password is incorrect
            return {'error': 'Unauthorized', 'message': 'Email or password is incorrect!'}, 401

        # Return success with JWT tokens if login is successful
        return jsonify(message='Successful login',
                       access_token=create_access_token(identity=user.uuid, fresh=True),
                       refresh_token=create_refresh_token(identity=user.uuid)), 200

    # Handles user registration by creating a new account
    @arg_parser({'first_name': name_regexp,
                 'last_name': name_regexp,
                 'email': email_regexp,
                 'password': password_regexp})
    def post(self, first_name: str, last_name: str, email: str, password: str) -> _get_post_type:
        """
        Registers a new user by creating an account with provided details.
        Checks if the email already exists and creates a new user if not.

        :param first_name: The user's first name
        :param last_name: The user's last name
        :param email: The user's email address
        :param password: The user's password
        :return: JSON response with success or error message, and HTTP status code
        """
        if UserDAO.get_user_by_email(email) is not None:
            # Return error if the email already exists
            return jsonify({'error': 'Conflict', 'message': 'Email already exists!'}), 409

        # Create a new user and hash the password
        UserDAO.create_user(first_name, last_name, email, bcrypt.generate_password_hash(password))
        return {'message': 'Account created!'}, 201

    # Refreshes the user's access token by using the refresh token
    @jwt_required(refresh=True)
    def patch(self) -> _patch_type:
        """
        Refreshes the access token by verifying the refresh token.
        Returns a new access token and sets the 'fresh' status to False.

        :return: JSON response with the new access token and status, and HTTP status code
        """
        redis_client.set(get_jwt()["jti"], "refreshed", ex=app.config.get('JWT_ACCESS_TOKEN_EXPIRES'))
        return jsonify(access_token=create_access_token(identity=get_jwt_identity()), fresh=False), 200

    # Revokes the user's current token
    @jwt_required(verify_type=False)
    def delete(self) -> _delete_type:
        """
        Revokes the user's current token (either access or refresh).
        The token is marked as deleted in Redis for the specified expiration time.

        :return: JSON response with the revocation message and HTTP status code
        """
        redis_client.set(get_jwt()["jti"], f'{get_jwt()["type"]} revoked',
                         ex=app.config.get('JWT_ACCESS_TOKEN_EXPIRES'))
        return {'message': f'{get_jwt()['type'].capitalize()} token successfully revoked'}, 200


auth_bp.add_url_rule('/', view_func=Auth.as_view('auth'))
