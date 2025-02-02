from flask import Blueprint, url_for, render_template_string

from app import UserDAO
from app.apis.utils import View, arg_parser, email_regexp, generate_confirmation_token, send_html_email, \
    MailTokenAlreadyExists, mail_token_regexp, confirm_token, MailTokenIncorrectOrExpiredException, \
    confirm_email_template

confirm_email_bp = Blueprint('confirm_email', __name__)


class ConfirmEmail(View):

    @arg_parser(one_of_all={
        'email': email_regexp,
        'token': mail_token_regexp
    })
    def get(self, email: str | None = None, token: str | None = None):
        """
        Handles email confirmation requests.

        - If the 'email' parameter is provided, sends a confirmation email to the user.
        - If the 'token' parameter is provided, verifies the token and confirms the user's email.
        - Returns an error if neither 'email' nor 'token' is provided.

        :param email: The user's email address for sending the confirmation link (optional).
        :param token: The confirmation token received from the email link (optional).
        :return: JSON response with a message and appropriate HTTP status code.
        """
        if email:
            user = UserDAO.get_user_by_email(email)
            if not user or user.email_verified:
                return {'error': 'Bad Request', 'message': "Can't send email."}, 400

            try:
                token = generate_confirmation_token(email)
            except MailTokenAlreadyExists:
                return {'error': 'Too Many Requests', 'message': 'Wait, email already sent.'}, 429

            confirm_url = url_for('api.confirm_email.confirm_email', token=token, _external=True)
            html_body = render_template_string(
                confirm_email_template,
                name=f'{user.first_name} {user.last_name}',
                confirm_link=confirm_url)

            if send_html_email('Email confirmation', html_body, email):
                return {'message': 'Email was sent.'}, 200

            return {'error': 'Service Unavailable',
                    'message': 'Service is temporarily unavailable, please try again later.'}, 503

        if token:
            try:
                email = confirm_token(token)
            except MailTokenIncorrectOrExpiredException:
                return {'error': 'Bad Request', 'message': 'Link is incorrect or expired.'}, 400

            user = UserDAO.get_user_by_email(email)
            if user is None or user.email_verified:
                return {'error': 'Bad Request', 'message': "Invalid or expired link."}, 400

            user.email_verified = True
            UserDAO.commit()
            return {'message': 'Account email confirmed.'}, 200


confirm_email_bp.add_url_rule('/', view_func=ConfirmEmail.as_view('confirm_email'))
