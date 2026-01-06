import hashlib
import os

def make_salt() -> bytes:
    return os.urandom(16)

def hash_password_with_salt(password: str, salt: bytes) -> bytes:
    # SQL Server NVARCHAR is UTF-16LE onder water
    password_bytes = password.encode("utf-16le")
    return hashlib.sha256(salt + password_bytes).digest()
