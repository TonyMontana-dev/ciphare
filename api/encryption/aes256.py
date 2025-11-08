from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from typing import Tuple
import os

from api.encryption.base import EncryptionAlgorithm

class AES256Encryption(EncryptionAlgorithm):
    ENCRYPTION_KEY_LENGTH = 32  # For AES-256

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = Scrypt(salt=salt, length=self.ENCRYPTION_KEY_LENGTH, n=2**14, r=8, p=1, backend=default_backend())
        return kdf.derive(password.encode())

    def encrypt(self, data: bytes, key: str) -> Tuple[bytes, dict]:
        salt = os.urandom(16)
        iv = os.urandom(12)
        derived_key = self._derive_key(key, salt)
        cipher = Cipher(algorithms.AES(derived_key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        return encrypted_data, {"iv": iv, "salt": salt, "tag": encryptor.tag}

    def decrypt(self, data: bytes, key: str, metadata: dict) -> bytes:
        derived_key = self._derive_key(key, metadata["salt"])
        cipher = Cipher(algorithms.AES(derived_key), modes.GCM(metadata["iv"], metadata["tag"]), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(data) + decryptor.finalize()
    
    def get_name(self) -> str:
        return "AES-256"
    
    def get_description(self) -> str:
        return "AES-256 encryption with GCM mode for authenticated encryption with associated data (AEAD)"
    


# BACKUP CODE FOR REFERENCE
"""

# Constants for encryption
ENCRYPTION_KEY_LENGTH = 32  # For AES-256
DOMAIN = os.getenv("DOMAIN", "https://ciphare.vercel.app/")  # For generating shareable links

# Derive encryption key using Scrypt
def derive_key(password: str, salt: bytes) -> bytes:
    # Scrypt parameters: n=2^14, r=8, p=1 for 256-bit key length (32 bytes) with default backend (OpenSSL)
    kdf = Scrypt(salt=salt, length=ENCRYPTION_KEY_LENGTH, n=2**14, r=8, p=1, backend=default_backend())
    return kdf.derive(password.encode())

# AES-256 encryption function with GCM mode for authenticated encryption with associated data (AEAD) 
# using a randomly generated IV and tag for authentication and integrity protection
def encrypt_aes256(data: bytes, password: str, salt: bytes) -> Tuple[bytes, bytes, bytes]:
    key = derive_key(password, salt)
    iv = os.urandom(12)  # 12-byte IV for GCM mode
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(data) + encryptor.finalize()
    return encrypted_data, iv, encryptor.tag

# AES-256 decryption function with GCM mode for authenticated decryption with associated data (AEAD) using the provided tag and IV
def decrypt_aes256(encrypted_data: bytes, password: str, salt: bytes, iv: bytes, tag: bytes) -> bytes:
    key = derive_key(password, salt)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted_data) + decryptor.finalize()

"""
