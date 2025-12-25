import logging
from typing import Optional, List, Type

from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    OperationalError,
    DataError,
    ProgrammingError,
    TimeoutError,
)
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase

from psycopg2.errors import UniqueViolation


logger = logging.getLogger(__name__)


# =========================================================
# Base Application Exception
# =========================================================

class DatabaseException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# =========================================================
# Unique Constraint Resolver (MODEL-AWARE)
# =========================================================

def resolve_unique_fields_from_constraint(
    model: Type[DeclarativeBase],
    constraint_name: Optional[str],
) -> Optional[List[str]]:
    """
    Dynamically resolves which field(s) caused a UNIQUE violation.

    Supports:
    - unique=True on columns
    - UniqueConstraint(...)
    - composite unique constraints
    """
    if not constraint_name or not model:
        return None

    table = model.__table__

    # 1. Explicit UniqueConstraint
    # for constraint in table.constraints:
    #     print("constraint")
    #     print(constraint)
    #     if isinstance(constraint, UniqueConstraint):
    #         if constraint.name == constraint_name:
    #             return [col.name for col in constraint.columns]
    
    for column in table.columns._all_columns:
        if column.name in constraint_name:
            return [column.name]

    # 2. Column-level unique=True (auto-generated constraint)
    # for column in table.columns:
    #     if column.unique:
    #         auto_name = f"{table.name}_{column.name}_key"
    #         if auto_name == constraint_name:
    #             return [column.name]

    return None


# =========================================================
# Main SQLAlchemy Exception Mapper
# =========================================================

def map_sqlalchemy_exception(
    exc: Exception,
    model: Optional[Type[DeclarativeBase]] = None,
) -> DatabaseException:
    """
    Converts SQLAlchemy exceptions into safe, user-facing errors.
    """

    # ---------- ORM lookup errors ----------
    if isinstance(exc, NoResultFound):
        return DatabaseException("Resource not found.", 404)

    if isinstance(exc, MultipleResultsFound):
        return DatabaseException("Multiple records found.", 409)

    # ---------- Integrity / constraint errors ----------
    if isinstance(exc, IntegrityError):
        orig = getattr(exc, "orig", None)

        # ---- UNIQUE violation (PostgreSQL) ----
        if isinstance(orig, UniqueViolation):
            fields = resolve_unique_fields_from_constraint(
                model,
                orig.diag.constraint_name,
            )

            if fields:
                field_list = ", ".join(fields)
                return DatabaseException(
                    message=f"{field_list} already exists.",
                    status_code=409,
                )

            return DatabaseException(
                "A record with the same value already exists.",
                409,
            )

        # ---- Generic integrity error ----
        return DatabaseException(
            "Operation violates database constraints.",
            409,
        )

    # ---------- Invalid data ----------
    if isinstance(exc, DataError):
        return DatabaseException(
            "Invalid data provided.",
            400,
        )

    # ---------- DB unavailable / connection ----------
    if isinstance(exc, OperationalError):
        return DatabaseException(
            "Database service unavailable. Please try again later.",
            503,
        )

    # ---------- Timeout ----------
    if isinstance(exc, TimeoutError):
        return DatabaseException(
            "Database request timed out.",
            504,
        )

    # ---------- Programming / mapping bugs ----------
    if isinstance(exc, ProgrammingError):
        logger.exception("SQL programming error", exc_info=exc)
        return DatabaseException(
            "Internal server error.",
            500,
        )

    # ---------- Generic SQLAlchemy error ----------
    if isinstance(exc, SQLAlchemyError):
        logger.exception("Unhandled SQLAlchemy error", exc_info=exc)
        return DatabaseException(
            "Unexpected database error occurred.",
            500,
        )

    # ---------- Non-SQLAlchemy fallback ----------
    logger.exception("Unhandled exception", exc_info=exc)
    return DatabaseException(
        "Unexpected server error.",
        500,
    )
