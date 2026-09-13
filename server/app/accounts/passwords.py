"""Password hashing delegated to pwdlib's recommended Argon2 hasher."""

from secrets import token_urlsafe

from pwdlib import PasswordHash

_password_hasher = PasswordHash.recommended()
# One process-local dummy hash ensures unknown users still incur verification work.
DUMMY_PASSWORD_HASH = _password_hasher.hash(token_urlsafe(32))


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hasher.verify(password, password_hash)
