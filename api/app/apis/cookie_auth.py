from datetime import datetime, timezone
from typing import Tuple, Dict

from flask import Blueprint, jsonify, Response
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, get_jwt, decode_token, \
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies

from app import bcrypt, redis_client, app
from app.apis.utils import View, arg_parser, email_regexp, password_regexp, name_regexp, authenticator
from app.database import UserDAO


_get_post_type = tuple[dict[str, str], int] | tuple[Response, int]
_patch_type = tuple[Response, int]
_delete_type = tuple[Response, int]

cookie_auth_bp = Blueprint('auth', __name__)


class Auth(View):

    @arg_parser({'email': email_regexp, 'password': password_regexp})
    def get(self, email: str, password: str) -> _get_post_type:
        """
        Authenticates the user by checking email and password.
        Set up JWT tokens to cookies if the credentials are valid.

        :param email: The user's email address
        :param password: The user's password
        :return: JSON response and HTTP status code
        """
        user = UserDAO.get_user_by_email(email)
        if user is None or not bcrypt.check_password_hash(user.password, password):
            return jsonify({'err': 'Unauthorized', 'msg': 'Email or password is incorrect'}), 401

        if not user.email_verified:
            return jsonify({'err': 'Forbidden', 'msg': 'Email address not verified'}), 403

        if user.is_deleted:
            return jsonify({'err': 'Gone', 'msg': 'Account was deleted'}), 410

        if user.is_blocked:
            if user.blocked_until.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
                return jsonify({
                    'err': 'Locked',
                    'msg': 'Account blocked',
                    'blocked_until': user.blocked_until,
                    'block_reason': user.blocked_reason
                }), 423
            else:
                user.is_blocked = False
                user.blocked_reason = None
                user.blocked_until = None
                UserDAO.commit()

        refresh_token = create_refresh_token(identity=user.uuid)
        access_token = create_access_token(
                           identity=user.uuid,
                           fresh=True,
                           additional_claims={'refresh_jti': decode_token(refresh_token)['jti']})
        resp = jsonify({'msg': 'Successful login'})
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)
        return resp, 200

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
            return jsonify({'err': 'Conflict', 'msg': 'Email already exists!'}), 409

        UserDAO.create_user(first_name, last_name, email, bcrypt.generate_password_hash(password))
        return jsonify({'msg': 'Account created!'}), 201

    @authenticator(refresh=True)
    def patch(self) -> _patch_type:
        """
        Refreshes the access token by verifying the refresh token.
        Returns a new access token and sets the 'fresh' status to False.

        :return: JSON response and HTTP status code
        """

        resp = jsonify({'msg': 'Token successfully updated'})
        set_access_cookies(resp, create_access_token(
            identity=get_jwt_identity(),
            fresh=False,
            additional_claims={'refresh_jti': get_jwt()['jti']}))
        return resp, 200

    @authenticator(refresh=False)
    def delete(self) -> _delete_type:
        """
        Revokes the user's current token (either access or refresh).
        The token is marked as deleted in Redis for the specified expiration time.

        :return: JSON response and HTTP status code
        """
        redis_client.set(get_jwt()["jti"], 'access token revoked',
                         ex=app.config.get('JWT_ACCESS_TOKEN_EXPIRES'))
        redis_client.set(get_jwt()["refresh_jti"], 'refresh token revoked',
                         ex=app.config.get('JWT_REFRESH_TOKEN_EXPIRES'))
        resp = jsonify({'msg': 'Tokens successfully revoked'})
        unset_jwt_cookies(resp)
        return resp, 200


cookie_auth_bp.add_url_rule('/', view_func=Auth.as_view('auth'))
