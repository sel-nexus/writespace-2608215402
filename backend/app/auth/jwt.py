"""Minimal HS256 JWT creation and verification utilities."""

import base64
import hashlib
import hmac
import json
import time
import uuid
from datetime import UTC, datetime, timedelta

from app.config import Settings
from app.errors import InvalidTokenError


def _base64url_encode(value: bytes) -> str:
    """Encode bytes using unpadded base64url.

    Args:
        value: Bytes to encode.

    Returns:
        A JWT-safe string.
    """
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    """Decode an unpadded base64url value.

    Args:
        value: Encoded JWT segment.

    Returns:
        Decoded bytes.

    Raises:
        InvalidTokenError: If the segment is malformed.
    """
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, UnicodeEncodeError) as exc:
        raise InvalidTokenError() from exc


def create_access_token(user_id: int, role: str, settings: Settings) -> str:
    """Create a signed, expiring access token.

    Args:
        user_id: Persisted account identifier.
        role: Informational account role.
        settings: Runtime JWT settings.

    Returns:
        A compact HS256 JWT.
    """
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expiration_minutes)).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        (_base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")), _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")))
    )
    signature = hmac.new(settings.jwt_secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def decode_access_token(token: str, settings: Settings) -> dict[str, object]:
    """Verify and decode a WriteSpace access token.

    Args:
        token: JWT supplied by a client.
        settings: Runtime JWT settings.

    Returns:
        The verified JWT claims.

    Raises:
        InvalidTokenError: If the token is malformed, unsigned, or expired.
    """
    pieces = token.split(".")
    if len(pieces) != 3:
        raise InvalidTokenError()
    header_raw, payload_raw, signature_raw = pieces
    expected = hmac.new(settings.jwt_secret.encode("utf-8"), f"{header_raw}.{payload_raw}".encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _base64url_decode(signature_raw)):
        raise InvalidTokenError()
    try:
        header = json.loads(_base64url_decode(header_raw))
        payload = json.loads(_base64url_decode(payload_raw))
        if header != {"alg": "HS256", "typ": "JWT"} or not isinstance(payload.get("sub"), str):
            raise ValueError("unsupported token")
        if not isinstance(payload.get("exp"), int) or payload["exp"] <= int(time.time()):
            raise ValueError("expired token")
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise InvalidTokenError() from exc
    return payload
