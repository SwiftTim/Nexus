import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def derive_key(password: str, salt: bytes = None) -> bytes:
    """Derives a 32-byte key from a password using PBKDF2."""
    if salt is None:
        # In a real app, we'd send the salt with the message or store it.
        # For simplicity (Step 7), we'll use a fixed salt for now.
        salt = b'static_salt_for_v1' 
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_message(message: str, key: bytes) -> str:
    """Encrypts a message using Fernet (AES-128 in CBC mode with HMAC)."""
    f = Fernet(key)
    encrypted = f.encrypt(message.encode())
    return encrypted.decode()

def decrypt_message(encrypted_message: str, key: bytes) -> str:
    """Decrypts a message using Fernet."""
    f = Fernet(key)
    try:
        decrypted = f.decrypt(encrypted_message.encode())
        return decrypted.decode()
    except Exception as e:
        return f"[DECRYPTION ERROR] {str(e)}"
