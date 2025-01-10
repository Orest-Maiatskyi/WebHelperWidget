import regex as re
from functools import wraps
from typing import Callable, Dict

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


# Decorator for smart request argument parsing and validation using regular expressions.
def arg_parser(request_args: Dict[str, str]):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that validates request arguments and passes validated arguments to the original function.

            :return: JSON response with an error if validation fails, or the result of the original function.
            """
            validated_args = {}
            for arg, regex in request_args.items():
                if request.args.get(arg) is None or not re.compile(regex, re.UNICODE).fullmatch(request.args.get(arg)):
                    return jsonify({'error': 'Bad Request',
                                    'message': f'Missing or incorrect required argument: {arg}'}), 400
                validated_args[arg] = request.args.get(arg)
            return func(*args, **kwargs, **validated_args)
        return wrapper
    return decorator
