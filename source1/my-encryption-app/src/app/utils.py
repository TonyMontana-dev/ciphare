"""
This file contains utility functions for generating IDs, deriving keys, and generating salts. 
The generate_id function generates a random ID of a specified length. The derive_key function 
derives a key using the Scrypt KDF with the specified length. The generate_salt function generates
a random salt of a specified size. These functions are used in the encryption and decryption
processes in the application. 

The constants.py file contains constants used in the application, such as the length of the ID,
the length of the encryption key, and the length of the salt. These constants are used in the
encryption and decryption processes to ensure that the keys and salts are of the correct length.

"""


# utils.py
import base64
import os
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from .constants import ID_LENGTH, ENCRYPTION_KEY_LENGTH

def generate_id(length=ID_LENGTH):
    return base64.urlsafe_b64encode(os.urandom(length)).decode('utf-8').rstrip("=")

def derive_key(password: str, salt: bytes, length=ENCRYPTION_KEY_LENGTH) -> bytes:
    """
    Derive a key using Scrypt KDF with the specified length from constants.
    """
    kdf = Scrypt(
        salt=salt,  # Random salt generated using os.urandom
        length=length,  # Set to ENCRYPTION_KEY_LENGTH from constants
        n=2**14,  # Set to 2^14 for security purposes (higher values increase security) 
        r=8,  # Set to 8 for security purposes (higher values increase security) 
        p=1,  # Set to 1 for security purposes (higher values increase security)
    )
    return kdf.derive(password.encode())

# Function to generate a random salt of a specified size using os.urandom function
def generate_salt(size=16):
    return os.urandom(size)
