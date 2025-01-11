import random

import regex as re
from functools import wraps
from typing import Callable, Dict, Optional

from flask import request, jsonify
from werkzeug.exceptions import MethodNotAllowed


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


def arg_parser(required_args: Optional[Dict[str, str]] = None, optional_args: Optional[Dict[str, str]] = None):
    """
    Decorator for smart request argument parsing and validation using regular expressions.

    :param required_args: A dictionary of required argument names and their regex patterns.
    :param optional_args: A dictionary of optional argument names and their regex patterns.
    :return: A decorator function.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that validates request arguments and passes validated arguments to the original function.

            :return: JSON response with an error if validation fails, or the result of the original function.
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

            return func(*args, **kwargs, **validated_args)

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
