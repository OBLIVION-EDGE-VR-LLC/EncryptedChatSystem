"""
AES-256-GCM Symmetric Encryption Module
Provides authenticated encryption with forward secrecy support.

1337_TECH DBA, Austin Texas - 2026
"""

import os
import struct
import time
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SymmetricCrypto:
    """AES-256-GCM authenticated encryption."""

    NONCE_SIZE = 12   # 96-bit nonce per NIST SP 800-38D
    KEY_SIZE = 32     # 256-bit key
    TAG_SIZE = 16     # 128-bit authentication tag

    def __init__(self, key: bytes = None):
        if key and len(key) != self.KEY_SIZE:
            raise ValueError(f"Key must be {self.KEY_SIZE} bytes")
        self._key = key or self.generate_key()
        self._aesgcm = AESGCM(self._key)
        self._message_counter = 0

    @staticmethod
    def generate_key() -> bytes:
        return AESGCM.generate_key(bit_length=256)

    @property
    def key(self) -> bytes:
        return self._key

    def encrypt(self, plaintext: bytes, aad: bytes = None) -> bytes:
        """
        Encrypt with AES-256-GCM.
        Returns: nonce (12B) || ciphertext || tag (16B)
        """
        nonce = self._generate_nonce()
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, aad)
        return nonce + ciphertext

    def decrypt(self, sealed: bytes, aad: bytes = None) -> bytes:
        """
        Decrypt AES-256-GCM sealed message.
        Input: nonce (12B) || ciphertext || tag (16B)
        """
        nonce = sealed[:self.NONCE_SIZE]
        ciphertext = sealed[self.NONCE_SIZE:]
        return self._aesgcm.decrypt(nonce, ciphertext, aad)

    def _generate_nonce(self) -> bytes:
        """
        Hybrid nonce: 4 bytes timestamp + 4 bytes counter + 4 bytes random.
        Prevents nonce reuse even under clock skew.
        """
        ts = struct.pack(">I", int(time.time()) & 0xFFFFFFFF)
        ctr = struct.pack(">I", self._message_counter & 0xFFFFFFFF)
        rand = os.urandom(4)
        self._message_counter += 1
        return ts + ctr + rand

    def rekey(self, new_key: bytes = None):
        """Rotate to a new key for forward secrecy."""
        self._key = new_key or self.generate_key()
        self._aesgcm = AESGCM(self._key)
        self._message_counter = 0
