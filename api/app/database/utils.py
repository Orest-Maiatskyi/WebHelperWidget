from datetime import datetime
from typing import Callable
from sqlalchemy import exc

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
