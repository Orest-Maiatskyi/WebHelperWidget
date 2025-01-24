from datetime import datetime
from typing import Callable
from sqlalchemy import exc, inspect

from app import db


class DAOException(Exception):
    """ Basic DAO exception class, raises every time as something went wrong with DAO queries. """
    pass


# catch any sqlalchemy exceptions and log them than raise DAOException
def dao_error_handler(func: Callable):

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exc.SQLAlchemyError as e:
            db.session.rollback()
            print('!!! DAO EXCEPTION OCCURRED !!!', flush=True)
            with open('dao-errors.log', 'a') as log_file:
                log_file.write(datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + ' ' + str(func) + '\n' + str(e) + '\n')
            raise DAOException(datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + ' ' + str(func) + '\n' + str(e) + '\n')
    return wrapper


class SerializableMixin:
    """
    A mixin class that adds serialization functionality for SQLAlchemy models.
    This mixin provides a method to convert a SQLAlchemy model instance into a dictionary.

    Note:
        This mixin is not intended for standalone use and must be used in combination
        with a SQLAlchemy model class.
    """
    def __init__(self, *args, **kwargs):
        if type(self) is SerializableMixin:
            raise NotImplementedError("SerializableMixin can't be used directly.")
        super().__init__(*args, **kwargs)

    def to_dict(self, exclude_list: list | None = None) -> dict:
        """
        Converts the SQLAlchemy model instance into a dictionary representation.

        :param exclude_list: A list of column names to exclude from the resulting dictionary.
                             Defaults to None, which means no columns will be excluded.
        :type exclude_list: list | None
        :return: A dictionary containing all the columns of the model with their corresponding values,
                 excluding any specified in the `exclude_list`.
        :rtype: dict
        """
        exclude_list = [] if exclude_list is None else exclude_list
        return {
            c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs
            if c.key not in exclude_list
        }
