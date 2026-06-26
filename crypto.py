import hashlib, os, base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as _pad

_KEY = hashlib.sha256(b"2626").digest()


def _encrypt(data: bytes) -> bytes:
    iv = os.urandom(16)
    padder = _pad.PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(_KEY), modes.CBC(iv))
    enc = cipher.encryptor()
    return iv + enc.update(padded) + enc.finalize()


def _decrypt(data: bytes) -> bytes:
    iv, ct = data[:16], data[16:]
    cipher = Cipher(algorithms.AES(_KEY), modes.CBC(iv))
    dec = cipher.decryptor()
    padded = dec.update(ct) + dec.finalize()
    unpadder = _pad.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def encrypt_text(s: str) -> bytes:
    return _encrypt(s.encode("utf-8"))


def decrypt_text(data: bytes) -> str:
    return _decrypt(data).decode("utf-8")


def encrypt_b64(s: str) -> str:
    return base64.b64encode(_encrypt(s.encode("utf-8"))).decode("ascii")
