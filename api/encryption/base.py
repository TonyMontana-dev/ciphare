"""
Use a base class to define a common interface for encryption algorithms.
"""

from typing import Any, Tuple

# Base class for all encryption algorithms
class EncryptionAlgorithm:
    """Base interface for encryption algorithms."""
    def encrypt(self, data: bytes, key: Any) -> Tuple[bytes, dict]:
        """Encrypt data and return encrypted data + metadata."""
        raise NotImplementedError

    def decrypt(self, data: bytes, key: Any, metadata: dict) -> bytes:
        """Decrypt data using metadata."""
        raise NotImplementedError
