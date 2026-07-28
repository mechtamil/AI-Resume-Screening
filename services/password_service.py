"""Password validation, generation, hashing, and verification."""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import string

from config.settings import (
    AUTH_PERMANENT_PASSWORD_MIN_LENGTH,
    AUTH_TEMP_PASSWORD_MIN_LENGTH,
)


class PasswordService:
    """PBKDF2 password storage with per-user salts and purpose-aware policy."""

    ALGORITHM = "sha256"
    DEFAULT_ITERATIONS = 310_000
    SALT_BYTES = 16
    MAX_LENGTH = 1024

    @classmethod
    def validate_temporary_password(cls, password: str) -> None:
        cls._validate_common(password, minimum=AUTH_TEMP_PASSWORD_MIN_LENGTH)

    @classmethod
    def validate_permanent_password(cls, password: str) -> None:
        cls._validate_common(password, minimum=AUTH_PERMANENT_PASSWORD_MIN_LENGTH)
        value = str(password or "")
        # A modest pilot policy. The service is deliberately configurable and
        # does not force users into one specific symbol pattern.
        if value.casefold() in {
            "password",
            "password123",
            "alten@123",
            "recruitos",
            "qwerty123",
        }:
            raise ValueError("Choose a password that is not commonly used.")

    @classmethod
    def generate_temporary_password(cls, length: int = 14) -> str:
        """Generate a unique temporary password for one-time distribution."""
        length = max(int(length), AUTH_TEMP_PASSWORD_MIN_LENGTH, 12)
        alphabet = string.ascii_letters + string.digits + "@#%+-_!"
        while True:
            value = "".join(secrets.choice(alphabet) for _ in range(length))
            if (
                any(character.islower() for character in value)
                and any(character.isupper() for character in value)
                and any(character.isdigit() for character in value)
                and any(character in "@#%+-_!" for character in value)
            ):
                return value

    @classmethod
    def hash_password(
        cls,
        password: str,
        *,
        temporary: bool = False,
        iterations: int | None = None,
    ) -> tuple[str, str, int]:
        if temporary:
            cls.validate_temporary_password(password)
        else:
            cls.validate_permanent_password(password)
        round_count = int(iterations or cls.DEFAULT_ITERATIONS)
        if round_count < 100_000:
            raise ValueError("Password iteration count is below the supported minimum.")

        salt = secrets.token_bytes(cls.SALT_BYTES)
        digest = hashlib.pbkdf2_hmac(
            cls.ALGORITHM,
            str(password).encode("utf-8"),
            salt,
            round_count,
        )
        return (
            base64.b64encode(digest).decode("ascii"),
            base64.b64encode(salt).decode("ascii"),
            round_count,
        )

    @classmethod
    def verify_password(
        cls,
        password: str,
        expected_hash: str,
        salt: str,
        iterations: int,
    ) -> bool:
        try:
            decoded_salt = base64.b64decode(str(salt).encode("ascii"), validate=True)
            expected = base64.b64decode(str(expected_hash).encode("ascii"), validate=True)
            actual = hashlib.pbkdf2_hmac(
                cls.ALGORITHM,
                str(password or "").encode("utf-8"),
                decoded_salt,
                int(iterations),
            )
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(actual, expected)

    @classmethod
    def _validate_common(cls, password: str, *, minimum: int) -> None:
        value = str(password or "")
        if len(value) < int(minimum):
            raise ValueError(f"Password must contain at least {int(minimum)} characters.")
        if len(value) > cls.MAX_LENGTH:
            raise ValueError("Password is too long.")
        if not any(not character.isspace() for character in value):
            raise ValueError("Password cannot contain only whitespace.")
