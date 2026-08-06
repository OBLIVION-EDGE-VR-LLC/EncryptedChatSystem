"""
Simulated Strategy - Classical crypto stand-ins for development/testing.

When neither oqs-provider nor liboqs are available, this strategy
provides functional encryption using X25519 (KEM stand-in) and
Ed25519 (signature stand-in) from the cryptography library.

1337_TECH DBA, Austin Texas - 2026
"""

from typing import Tuple

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey
)
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .crypto_strategy_base import CryptoStrategyBase


class SimulatedStrategy(CryptoStrategyBase):
    """
    Fallback strategy using classical cryptographic primitives.

    X25519 simulates KEM key exchange, Ed25519 simulates ML-DSA signatures.
    Always available as it uses the standard cryptography library.
    """

    def __init__(self, kem_algorithm: str = "ML-KEM-1024",
                 sig_algorithm: str = "ML-DSA-87"):
        super().__init__(kem_algorithm, sig_algorithm)

    def _probe(self) -> bool:
        """Classical crypto is always available via the cryptography library."""
        try:
            X25519PrivateKey.generate()
            Ed25519PrivateKey.generate()
            return True
        except Exception:
            return False

    # ── KEM Operations (simulated via X25519) ──

    def kem_keygen(self) -> Tuple[bytes, bytes]:
        sk = X25519PrivateKey.generate()
        pk = sk.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        sk_bytes = sk.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption()
        )
        return pk, sk_bytes

    def kem_encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        eph_sk = X25519PrivateKey.generate()
        eph_pk = eph_sk.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        peer_pk = X25519PublicKey.from_public_bytes(public_key)
        shared = eph_sk.exchange(peer_pk)
        ss = HKDF(
            algorithm=hashes.SHA256(), length=32,
            salt=None, info=b"riddlerchat-kem-sim"
        ).derive(shared)
        return eph_pk, ss

    def kem_decapsulate(self, secret_key: bytes, ciphertext: bytes) -> bytes:
        sk = X25519PrivateKey.from_private_bytes(secret_key)
        peer_pk = X25519PublicKey.from_public_bytes(ciphertext)
        shared = sk.exchange(peer_pk)
        ss = HKDF(
            algorithm=hashes.SHA256(), length=32,
            salt=None, info=b"riddlerchat-kem-sim"
        ).derive(shared)
        return ss

    # ── Signature Operations (simulated via Ed25519) ──

    def sig_keygen(self) -> Tuple[bytes, bytes]:
        sk = Ed25519PrivateKey.generate()
        pk = sk.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        sk_bytes = sk.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption()
        )
        return pk, sk_bytes

    def sig_sign(self, secret_key: bytes, message: bytes) -> bytes:
        sk = Ed25519PrivateKey.from_private_bytes(secret_key)
        return sk.sign(message)

    def sig_verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        pk = Ed25519PublicKey.from_public_bytes(public_key)
        try:
            pk.verify(signature, message)
            return True
        except Exception:
            return False

    def get_info(self) -> dict:
        info = super().get_info()
        info["note"] = "Simulated PQ using classical X25519/Ed25519 stand-ins"
        return info
