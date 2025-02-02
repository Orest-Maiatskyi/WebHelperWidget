import random
import time
from datetime import datetime, timezone

import regex as re
from functools import wraps
from typing import Callable, Dict

from flask import request, jsonify
from flask_jwt_extended import get_jwt
from flask_jwt_extended.view_decorators import LocationType, verify_jwt_in_request
from werkzeug.exceptions import MethodNotAllowed

from app import redis_client, app, UserDAO
from app.apis.utils import math_captcha_answer_regexp


class View:
    """
    A Django-like class-based view for handling HTTP requests based on their method.

    This class maps HTTP methods (e.g., GET, POST, PATCH, DELETE) to corresponding
    methods within the class. It simplifies request handling by providing a structured
    and reusable way to define views.

    Attributes:
        methods (list): A list of allowed HTTP methods. Defaults to ["GET", "POST", "PATCH", "DELETE"].

    Methods:
        dispatch_request(*args, **kwargs):
            Determines the appropriate method handler for the current HTTP method
            and executes it.

        as_view(name, *class_args, **class_kwargs):
            Creates a callable view function from the class, allowing it to be used
            like a function-based view in a web framework.
    """

    methods = ["GET", "POST", "PATCH", "DELETE"]

    def dispatch_request(self, *args, **kwargs):
        """
        Dispatches the request to the appropriate method handler based on the HTTP method.

        :param args: Positional arguments passed to the method handler.
        :param kwargs: Keyword arguments passed to the method handler.
        :raises MethodNotAllowed: If the HTTP method is not implemented in the class.
        :return: The result of the executed method handler.
        """
        handler = getattr(self, request.method.lower(), None)

        if handler is None:
            raise MethodNotAllowed(valid_methods=self.methods)

        return handler(*args, **kwargs)

    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        """
        Converts the class into a callable view function that can be used
        like a function-based view.

        This is useful for integrating the class into frameworks that expect
        views as callable functions.

        :param name: The name of the view function.
        :param class_args: Positional arguments for instantiating the class.
        :param class_kwargs: Keyword arguments for instantiating the class.
        :return: A callable view function.
        """

        def view(*args, **kwargs):
            self = cls(*class_args, **class_kwargs)
            return self.dispatch_request(*args, **kwargs)

        view.__name__ = name
        view.methods = cls.methods
        return view


def arg_parser(required_args: Dict[str, str] | None = None,
               optional_args: Dict[str, str] | None = None,
               one_of_all: Dict[str, str] | None = None,
               file_required: str | None = None) -> Callable:
    """
    Decorator for smart request argument and file parsing with validation using regular expressions.

    Validates query parameters and uploaded files based on the provided rules:
    - Required arguments must be present and match the specified regex patterns.
    - Optional arguments are validated if present but are not mandatory.
    - 'one_of_all' enforces that exactly one argument from the given set must be provided.
    - File validation checks for the required file type if specified.

    :param required_args: A dictionary of required argument names and their regex patterns.
    :param optional_args: A dictionary of optional argument names and their regex patterns.
    :param one_of_all: A dictionary where exactly one argument must be present and match its regex pattern.
    :param file_required: A string indicating the required file extension (WITHOUT DOT).
    :return: A decorator function that validates request parameters before passing them to the original function.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that performs validation on request arguments and files.

            - Validates required arguments strictly for presence and pattern matching.
            - Checks optional arguments only if they are provided.
            - Ensures that exactly one argument from 'one_of_all' is present and valid;
              returns an error if none or multiple are provided.
            - Validates the presence and format of the uploaded file if 'file_required' is set.

            If any validation fails, returns a JSON error response with an appropriate HTTP status code.

            :return: JSON error response if validation fails, otherwise the original function's response.
            """
            validated_args = {}

            if required_args:
                for arg, regex in required_args.items():
                    if request.args.get(arg) is None or not re.compile(regex, re.UNICODE).fullmatch(
                            request.args.get(arg)):
                        return jsonify({'error': 'Bad Request',
                                        'message': f'Missing or incorrect required argument: {arg}'}), 400
                    validated_args[arg] = request.args.get(arg)

            if optional_args:
                for arg, regex in optional_args.items():
                    if request.args.get(arg) is not None and not re.compile(regex, re.UNICODE).fullmatch(
                            request.args.get(arg)):
                        return jsonify({'error': 'Bad Request',
                                        'message': f'Incorrect optional argument: {arg}'}), 400
                    validated_args[arg] = request.args.get(arg)

            if one_of_all:
                temp_arg: str | None = None
                for arg, regex in one_of_all.items():
                    if request.args.get(arg) is not None:
                        if not re.compile(regex, re.UNICODE).fullmatch(
                                request.args.get(arg)):
                            return jsonify({'error': 'Bad Request',
                                            'message': f'Incorrect optional argument: {arg}'}), 400
                        if temp_arg is not None:
                            return jsonify({'error': 'Bad Request',
                                            'message': f'Only one of the following arguments must be specified:\n'
                                                       f'{" ".join("".join(arg) for arg, regex in one_of_all.items())}'}), 400
                        temp_arg = arg
                if temp_arg is None:
                    return jsonify({'error': 'Bad Request',
                                    'message': f'At least one of the following arguments must be specified:\n'
                                               f'{" ".join("".join(arg) for arg, regex in one_of_all.items())}'}), 400
                validated_args[temp_arg] = request.args.get(temp_arg)

            if file_required:
                if len(request.files) == 0:
                    return jsonify({'error': 'Bad Request',
                                    'message': f'File with type .{file_required} is required'}), 400
                file = list(request.files.values())[0]
                if file.filename == '':
                    return jsonify({'error': 'Bad Request',
                                    'message': f'File must contain name'}), 400
                if file.filename.split('.')[-1].lower() != file_required:
                    return {'error': 'Unsupported Media Type', 'message': 'Supported only .jsonl file type'}, 415
                validated_args[f'{file_required}_file'] = file

            return func(*args, **kwargs, **validated_args)

        return wrapper

    return decorator


def authenticator(
        optional: bool = False,
        fresh: bool = False,
        refresh: bool = False,
        locations: LocationType | None = None,
        verify_type: bool = True,
        skip_revocation_check: bool = False) -> Callable:
    """
    A decorator to protect a Flask endpoint with JSON Web Tokens + validating user account

    :param optional:
        If ``True``, allow the decorated endpoint to be accessed if no JWT is present in
        the request. Defaults to ``False``.

    :param fresh:
        If ``True``, require a JWT marked with ``fresh`` to be able to access this
        endpoint. Defaults to ``False``.

    :param refresh:
        If ``True``, requires a refresh JWT to access this endpoint. If ``False``,
        requires an access JWT to access this endpoint. Defaults to ``False``.

    :param locations:
        A location or list of locations to look for the JWT in this request, for
        example ``'headers'`` or ``['headers', 'cookies']``. Defaults to ``None``
        which indicates that JWTs will be looked for in the locations defined by the
        ``JWT_TOKEN_LOCATION`` configuration option.

    :param verify_type:
        If ``True``, the token type (access or refresh) will be checked according
        to the ``refresh`` argument. If ``False``, type will not be checked and both
        access and refresh tokens will be accepted.

    :param skip_revocation_check:
        If ``True``, revocation status of the token will be *not* checked. If ``False``,
        revocation status of the token will be checked.
    """
    def decorator(func: Callable):
        """
        A decorator for validating user account status based on JWT claims and user data from the database.

        This checks:
        - If the JWT is valid (returning a 401 if app was rebooted and jwt is still valid).
        - If the account email is verified, returning a 403 Forbidden response.
        - If the account is deleted, returning a 410 Gone response.
        - If the account is blocked, returning a 423 Locked response with details.
        - If the block has expired, it updates the user's block status in the database.

        :param func: The function to decorate.
        :type func: Callable
        :return: The wrapped function.
        :rtype: Callable
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request(optional, fresh, refresh, locations, verify_type, skip_revocation_check)

            if not optional:
                user = UserDAO.get_user_by_uuid(get_jwt().get("sub"))

                if user is None:
                    return jsonify({'error': 'Unauthorized', 'message': 'Invalid or expired JWT token'}), 401

                if not user.email_verified:
                    return jsonify({'error': 'Forbidden', 'message': 'Email address not verified'}), 403

                if user.is_deleted:
                    return jsonify({'error': 'Gone', 'message': 'Account was deleted'}), 410

                if user.is_blocked:
                    if user.blocked_until.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
                        return jsonify({
                            'error': 'Locked',
                            'message': 'Account blocked',
                            'blocked_until': user.blocked_until,
                            'block_reason': user.blocked_reason
                        }), 423
                    else:
                        user.is_blocked = False
                        user.blocked_reason = None
                        user.blocked_until = None
                        UserDAO.commit()

            return func(*args, **kwargs)

        return wrapper

    return decorator


def generate_math_problem():
    """
    Generates a random mathematical problem involving two numbers and a random operation (+, -, *, /).
    Ensures the result is an integer within the range of 1 to 1000.

    Returns:
        tuple:
            - problem (str): A string representation of the math problem (e.g., "12 + 345").
            - result (int): The correct answer to the problem.

    Logic:
        - Two random integers are generated between 1 and 1000.
        - A random operation is selected from +, -, *, /.
        - For division (/), ensures the divisor is not zero and the result is an integer.
        - Filters out problems where the result is outside the range [1, 1000].
    """
    while True:
        num1 = random.randint(1, 1000)
        num2 = random.randint(1, 1000)

        operation = random.choice(['+', '-', '*', '/'])

        result = None

        if operation == '+':
            result = num1 + num2
        elif operation == '-':
            result = num1 - num2
        elif operation == '*':
            result = num1 * num2
        elif operation == '/':
            if num2 != 0 and num1 % num2 == 0:
                result = num1 // num2
            else:
                continue

        if 1 <= result <= 1000:
            problem = f"{num1} {operation} {num2} = "
            return problem, result


def math_captcha():
    """
    A decorator that enforces a math CAPTCHA as part of a request workflow.
    It checks for the correctness of a provided CAPTCHA answer or generates
    a new math problem if none is provided or if the answer is incorrect.
    If route decorated with it, 'captcha_answer' arg should be in request!
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if request.args.get('captcha_answer'):

                if not re.compile(math_captcha_answer_regexp, re.UNICODE).fullmatch(
                        request.args.get('captcha_answer')):
                    return {'error': 'Bad Request',
                            'message': 'Missing or incorrect required argument: captcha_answer'}, 400

                result = redis_client.get(f'account-{get_jwt().get("sub")}-removal-captcha-answer')
                if result is not None and int(request.args.get('captcha_answer')) == int(result):
                    redis_client.delete(f'account-{get_jwt().get("sub")}-removal-captcha-answer')
                    return func(*args, **kwargs)

            problem, result = generate_math_problem()
            redis_client.set(
                f'account-{get_jwt().get("sub")}-removal-captcha-answer',
                str(result), app.config.get('MATH_CAPTCHA_DURATION'))
            return {'math_captcha': problem, 'timestamp': str(int(time.time()))}, 202

        return wrapper

    return decorator
