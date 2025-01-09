from abc import ABC
from typing import Optional, List, Any, Type

from sqlalchemy import Select
from sqlalchemy.orm import DeclarativeMeta, Query

from app import db
from app.database.utils import dao_error_handler


class Base(ABC):
    """
    Base Data Access Object (DAO) class for common database operations.

    This class provides reusable methods for interacting with the database,
    including basic CRUD operations, pagination, and query execution. It is
    intended to be inherited by specific DAO classes for individual models.

    Methods:
    - execute_query: Executes a raw SQLAlchemy query and returns all results.
    - scalar_query: Executes a query and returns a single scalar value.
    - scalars_query: Executes a query and returns a list of scalar values.
    - insert: Inserts a model instance into the database.
    - count: Counts the number of rows in a table, with optional filters.
    - pagination: Retrieves paginated results for a given query.
    - commit: Commits the current database transaction.
    - delete: Deletes a model instance from the database.
    """

    @staticmethod
    @dao_error_handler
    def execute_query(query: Select) -> Optional[List[Any]]:
        """
        Executes an SQL query and returns all rows from the result.

        :param query: SQLAlchemy Select query.
        :return: List of rows or None if no rows are found.
        """
        rows = db.session.execute(query).all()
        return None if len(rows) == 0 else rows

    @staticmethod
    @dao_error_handler
    def scalar_query(query: Select) -> Optional[Any]:
        """
        Executes an SQL query and returns a single scalar value.

        :param query: SQLAlchemy Select query.
        :return: A single scalar value or None if the query returns nothing.
        """
        return db.session.scalar(query)

    @staticmethod
    @dao_error_handler
    def scalars_query(query: Select) -> List[Any]:
        """
        Executes an SQL query and returns all rows as a list of scalar values.

        :param query: SQLAlchemy Select query.
        :return: List of scalar values.
        """
        rows = db.session.scalars(query).all()
        return rows

    @staticmethod
    @dao_error_handler
    def insert(model_obj_instance: DeclarativeMeta) -> None:
        """
        Inserts a new model instance into the database.

        :param model_obj_instance: Instance of a SQLAlchemy model to insert.
        """
        db.session.add(model_obj_instance)
        db.session.commit()

    @staticmethod
    @dao_error_handler
    def count(model_obj: Type[DeclarativeMeta], filter_conditions: Optional[Any] = None) -> int:
        """
        Counts the number of rows in a given model's table.

        :param model_obj: SQLAlchemy model class.
        :param filter_conditions: Optional filtering conditions (SQLAlchemy expressions).
        :return: The count of rows matching the conditions.
        """
        query = db.session.query(model_obj)
        if filter_conditions:
            query = query.filter(filter_conditions)
        return query.count()

    @staticmethod
    @dao_error_handler
    def pagination(query: Query, page: int, per_page: int) -> List[Any]:
        """
        Paginates a query to retrieve a subset of rows.

        :param query: SQLAlchemy Query object.
        :param page: Current page number (starting from 1).
        :param per_page: Number of rows per page.
        :return: List of rows for the given page.
        """
        return query.offset((page - 1) * per_page).limit(per_page).all()

    @staticmethod
    @dao_error_handler
    def commit() -> None:
        """
        Commits the current transaction.

        :return: None
        """
        db.session.commit()

    @staticmethod
    @dao_error_handler
    def delete(model_obj_instance: DeclarativeMeta) -> None:
        """
        Deletes a model instance from the database.

        :param model_obj_instance: Instance of a SQLAlchemy model to delete.
        """
        db.session.delete(model_obj_instance)
        db.session.commit()
