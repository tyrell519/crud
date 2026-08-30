class DomainError(Exception):
    """Base class for all domain-level errors."""


class NotFoundError(DomainError):
    """The requested aggregate does not exist (or is soft-deleted)."""


class ConflictError(DomainError):
    """The operation violates a domain or database constraint."""
