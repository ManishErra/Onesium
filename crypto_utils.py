import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_SIZE = 16
PBKDF2_ITERATIONS = 600_000
KEY_LENGTH = 32


def generate_salt():
    """Generates a secure random 16-byte salt."""
    return os.urandom(SALT_SIZE)


def hash_password(master_password, salt):
    """
    Derives a password verification hash using PBKDF2-HMAC-SHA256.
    Returns 32 derived bytes for database storage.
    """
    if not isinstance(master_password, str):
        raise TypeError("master_password must be a string")
    if not isinstance(salt, bytes):
        raise TypeError("salt must be bytes")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(master_password.encode("utf-8"))


def derive_key(master_password, salt):
    """
    Derives a Fernet-compatible 32-byte base64-encoded key from the master password and salt.
    """
    if not isinstance(master_password, str):
        raise TypeError("master_password must be a string")
    if not isinstance(salt, bytes):
        raise TypeError("salt must be bytes")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    raw_key = kdf.derive(master_password.encode("utf-8"))
    return base64.urlsafe_b64encode(raw_key)


def encrypt_password(plaintext, key):
    """
    Encrypts a plaintext password using Fernet.
    Returns the encrypted token as bytes.
    """
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")

    f = Fernet(key)
    return f.encrypt(plaintext.encode("utf-8"))


def decrypt_password(ciphertext, key):
    """
    Decrypts a Fernet ciphertext token.
    Returns the original plaintext string.
    Raises InvalidToken on invalid or tampered ciphertext.
    """
    if not isinstance(ciphertext, bytes):
        raise TypeError("ciphertext must be bytes")

    f = Fernet(key)
    return f.decrypt(ciphertext).decode("utf-8")


def encrypt_data(data_bytes, key):
    """
    Encrypts raw bytes (e.g., JSON backup payload) using Fernet.
    Returns the encrypted token as bytes.
    """
    if not isinstance(data_bytes, bytes):
        raise TypeError("data_bytes must be bytes")

    f = Fernet(key)
    return f.encrypt(data_bytes)


def decrypt_data(ciphertext_bytes, key):
    """
    Decrypts raw Fernet ciphertext bytes.
    Returns the decrypted raw bytes.
    Raises InvalidToken on invalid or tampered ciphertext.
    """
    if not isinstance(ciphertext_bytes, bytes):
        raise TypeError("ciphertext_bytes must be bytes")

    f = Fernet(key)
    return f.decrypt(ciphertext_bytes)
