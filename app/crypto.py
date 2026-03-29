import base64
import hashlib
import os
from cryptography.fernet import Fernet


def _fernet() -> Fernet:
    raw = os.environ["SECRET_KEY"].encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(raw + b"fernet-v1").digest())
    return Fernet(key)


def encrypt(plaintext: str) -> bytes:
    return _fernet().encrypt(plaintext.encode())


def decrypt(ciphertext: bytes) -> str:
    return _fernet().decrypt(ciphertext).decode()
