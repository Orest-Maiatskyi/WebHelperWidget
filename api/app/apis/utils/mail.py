from datetime import datetime
from typing import Any

from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer as Serializer

from app import app, redis_client, mail


class MailTokenException(Exception):
    """
    Base exception for mail token methods.
    """
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MailTokenAlreadyExists(MailTokenException):
    """
    Exception raised when a confirmation token already exists for the given email.

    This exception is used to prevent generating multiple tokens for the same email
    within a short period.
    """
    def __init__(self) -> None:
        super().__init__('A token already exists for this email.')


class MailTokenIncorrectOrExpiredException(MailTokenException):
    """
    Exception raised when a provided confirmation token is either incorrect or expired.

    This exception indicates that the token cannot be used to confirm the user's email.
    """
    def __init__(self) -> None:
        super().__init__('A token is incorrect or expired.')


def generate_confirmation_token(email) -> str:
    """
    Generates a confirmation token for the provided email address.

    Checks if a token already exists in Redis for the email; if so, raises
    MailTokenAlreadyExists. Otherwise, creates a new token with an expiration
    time defined in the configuration, and returns the token as a string.

    :param email: The email address for which to generate the token.
    :return: A URL-safe confirmation token.
    :raises MailTokenAlreadyExists: If a token for the email already exists.
    """
    if redis_client.get(f'{email}-confirmation-token') is not None:
        raise MailTokenAlreadyExists

    redis_client.set(f'{email}-confirmation-token', str(datetime.now()), ex=app.config.get('MAIL_TOKEN_EXP'))

    return Serializer(
        app.config.get('MAIL_TOKEN_SECRET_KEY')
    ).dumps(email, salt=app.config.get('MAIL_TOKEN_SECRET_SALT'))


def confirm_token(token) -> Any:
    """
    Validates the provided confirmation token and retrieves the associated email.

    Attempts to deserialize the token using the secret key and salt from the
    configuration. If the token is invalid or has expired, raises
    MailTokenIncorrectOrExpiredException.

    :param token: The confirmation token to validate.
    :return: The email address contained within the token if it is valid.
    :raises MailTokenIncorrectOrExpiredException: If the token is incorrect or expired.
    """
    try:
        email = Serializer(
            app.config.get('MAIL_TOKEN_SECRET_KEY')
        ).loads(token, salt=app.config.get('MAIL_TOKEN_SECRET_SALT'), max_age=app.config.get('MAIL_TOKEN_EXP'))
    except Exception:
        raise MailTokenIncorrectOrExpiredException
    return email


def send_html_email(subject: str, html_content: str, recipient: str) -> bool:
    """
    Sends an HTML email to the specified recipient.

    Constructs an email message with the given subject and HTML content, and sends
    it to the recipient. In case of any sending failure, logs the error details
    and returns False.

    :param subject: The subject of the email.
    :param html_content: The HTML content of the email.
    :param recipient: The email address of the recipient.
    :return: True if the email was sent successfully; False otherwise.
    """
    msg = Message(subject, recipients=[recipient], html=html_content)
    try:
        mail.send(msg)
    except Exception as e:
        print(f'!!! EMAIL FAILED TO SEND !!!\n{e}', flush=True)
        with open('email-errors.log', 'a') as log_file:
            log_file.write(datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + '\n' + str(e) + '\n')
        return False
    return True
