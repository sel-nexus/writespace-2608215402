"""Password hashing helpers for WriteSpace authentication."""

import bcrypt

_DUMMY_PASSWORD = b"writespace-invalid-credential-padding"
DUMMY_HASH = bcrypt.hashpw(_DUMMY_PASSWORD, bcrypt.gensalt())


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt.

    Args:
        password: The plaintext password to protect.

    Returns:
        A UTF-8 bcrypt hash suitable for persistence.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str | bytes) -> bool:
    """Compare a plaintext password with a bcrypt hash.

    Args:
        password: The candidate plaintext password.
        password_hash: The stored or dummy bcrypt hash.

    Returns:
        Whether the password matches the hash.
    """
    encoded_hash = password_hash.encode("utf-8") if isinstance(password_hash, str) else password_hash
    return bcrypt.checkpw(password.encode("utf-8"), encoded_hash)
