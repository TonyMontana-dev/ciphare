"""
This is the registry module for encryption algorithms. It is responsible for centralizing the registration and retrieval of encryption algorithms.
"""

from typing import Type, Optional
from api.encryption.base import EncryptionAlgorithm
from api.encryption.aes256 import AES256Encryption
import logging

logger = logging.getLogger(__name__)

class EncryptionRegistry:
    _algorithms = {}

    @classmethod
    def register(cls, name: str, algorithm: Type[EncryptionAlgorithm]):
        """Register an encryption algorithm"""
        if not issubclass(algorithm, EncryptionAlgorithm):
            raise TypeError(f"Algorithm must be a subclass of EncryptionAlgorithm")
        cls._algorithms[name.upper()] = algorithm
        logger.info(f"Registered encryption algorithm: {name}")

    @classmethod
    def get(cls, name: str) -> EncryptionAlgorithm:
        """Get an encryption algorithm instance by name"""
        name_upper = name.upper()
        if name_upper not in cls._algorithms:
            available = ", ".join(cls._algorithms.keys())
            raise ValueError(
                f"Algorithm '{name}' is not supported. Available algorithms: {available}"
            )
        try:
            return cls._algorithms[name_upper]()
        except Exception as e:
            logger.error(f"Failed to instantiate algorithm {name}: {e}")
            raise ValueError(f"Failed to initialize algorithm '{name}': {str(e)}")

    @classmethod
    def list_algorithms(cls) -> list:
        """List all registered algorithm names"""
        return list(cls._algorithms.keys())

# Register algorithms
try:
    EncryptionRegistry.register("AES256", AES256Encryption)
    logger.info("Encryption algorithms registered successfully")
except Exception as e:
    logger.error(f"Failed to register encryption algorithms: {e}")
    raise
