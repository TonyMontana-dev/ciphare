"""
This is the registry module for encryption algorithms. It is responsible for centralizing the registration and retrieval of encryption algorithms.
"""

from typing import Type
from api.encryption.base import EncryptionAlgorithm
from api.encryption.aes256 import AES256Encryption

class EncryptionRegistry:
    _algorithms = {}

    @classmethod
    def register(cls, name: str, algorithm: Type[EncryptionAlgorithm]):
        cls._algorithms[name] = algorithm

    @classmethod
    def get(cls, name: str) -> EncryptionAlgorithm:
        if name not in cls._algorithms:
            raise ValueError(f"Algorithm '{name}' is not supported")
        return cls._algorithms[name]()

# Register algorithms
EncryptionRegistry.register("AES256", AES256Encryption)
# Future: EncryptionRegistry.register("NAME OF SAMPLE ALGORITHM", ALGORITHM_CLASS)
