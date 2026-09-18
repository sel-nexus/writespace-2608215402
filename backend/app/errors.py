"""Domain errors and their safe HTTP translations."""


class DomainError(RuntimeError):
    """Represent a safe, client-visible domain failure."""

    status_code = 400
    code = "domain_error"
    message = "The request could not be completed."


class InvalidCredentialsError(DomainError):
    """Hide all login failures behind one safe response."""

    status_code = 401
    code = "invalid_credentials"
    message = "Invalid username or password."


class InvalidTokenError(DomainError):
    """Represent any missing, malformed, expired, or inactive bearer token."""

    status_code = 401
    code = "invalid_token"
    message = "Authentication is required."


class DuplicateUsernameError(DomainError):
    """Report a username conflict without revealing credential details."""

    status_code = 409
    code = "username_conflict"
    message = "That username is already in use."


class DatabaseUnavailableError(RuntimeError):
    """Raised when a database probe cannot complete safely."""
