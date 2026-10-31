import base64
import hashlib
import hmac
import os

_N = 2**14
_R = 8
_P = 1
_SALT_BYTES = 16
_KEY_BYTES = 32


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def hash_password(password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    key = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=_KEY_BYTES
    )
    return f"scrypt${_N}${_R}${_P}${_b64(salt)}${_b64(key)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, key_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(key_b64)
        key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(key, expected)