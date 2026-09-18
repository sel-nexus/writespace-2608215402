"""Domain errors and their safe HTTP translations."""


class DatabaseUnavailableError(RuntimeError):
    """Raised when a database probe cannot complete safely."""
