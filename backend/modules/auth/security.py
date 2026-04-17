"""Security helpers for password and session management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import hmac
import re
import secrets

from fastapi import HTTPException, status

from backend.modules.config import settings


PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{3,}$")


def normalize_email(email: str) -> str:
    """Normalize user email for storage and lookup."""
    return email.strip().lower()


def validate_password_strength(password: str) -> None:
    """Reject weak passwords before hashing."""
    if not PASSWORD_PATTERN.match(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parola en az 3 karakter, bir büyük harf, bir küçük harf ve bir rakam içermeli.",
        )


def hash_password(password: str) -> str:
    """Hash password with PBKDF2-HMAC."""
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310_000,
    )
    return f"{salt.hex()}:{derived.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password using constant-time compare."""
    try:
        salt_hex, hash_hex = password_hash.split(":", 1)
    except ValueError:
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        310_000,
    )
    return hmac.compare_digest(derived.hex(), hash_hex)


def generate_session_token() -> str:
    """Create random session token for cookie storage."""
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    """Hash session token before storing in database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_session_expiry() -> datetime:
    """Return session expiry timestamp."""
    return datetime.utcnow() + timedelta(minutes=settings.AUTH_SESSION_TTL_MINUTES)


@dataclass
class LoginAttemptWindow:
    """Simple in-memory rate limiting window for auth endpoints."""

    attempts: list[datetime]


class LoginRateLimiter:
    """Protect login/setup endpoints from brute force bursts."""

    def __init__(self, limit: int, window_minutes: int):
        self.limit = limit
        self.window = timedelta(minutes=window_minutes)
        self._store: dict[str, LoginAttemptWindow] = {}

    def hit(self, key: str) -> None:
        now = datetime.utcnow()
        bucket = self._store.setdefault(key, LoginAttemptWindow(attempts=[]))
        bucket.attempts = [attempt for attempt in bucket.attempts if now - attempt < self.window]
        if len(bucket.attempts) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Çok fazla giriş denemesi. Birkaç dakika sonra tekrar deneyin.",
            )
        bucket.attempts.append(now)


auth_rate_limiter = LoginRateLimiter(
    limit=settings.AUTH_RATE_LIMIT_ATTEMPTS,
    window_minutes=settings.AUTH_RATE_LIMIT_WINDOW_MINUTES,
)
