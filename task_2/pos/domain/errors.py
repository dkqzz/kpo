"""Errors raised when a POS domain rule or application use case is violated."""


class PosError(Exception):
    """Base class for errors that can be shown to a console user."""


class ValidationError(PosError, ValueError):
    """A domain value is invalid."""


class DuplicateEntryError(PosError):
    """An entity or evaluation with the same identity already exists."""


class EntityNotFoundError(PosError):
    """A requested student or criterion does not exist."""


class EvaluationNotFoundError(EntityNotFoundError):
    """A requested evaluation does not exist."""
