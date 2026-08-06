"""
Post-Quantum Cryptography Module
Implements NIST FIPS 203 (ML-KEM) and FIPS 204 (ML-DSA)
with X25519 hybrid key exchange for forward secrecy.

Refactored to use the Gang of Four Strategy Pattern:
  - CryptoStrategyBase (ABC) defines the interface
  - OQSProviderStrategy uses OpenSSL 3.x oqs-provider
  - LibOQSStrategy uses liboqs Python bindings
  - SimulatedStrategy uses classical crypto stand-ins

The Context (this class) auto-detects the best available backend
and delegates all PQ operations to the selected strategy.
Strategy can be switched at runtime via set_strategy().

Design reference: chatclient/TheRiddlerChatSystem/Model/stateful_messaging/
  CommunicationBase -> PlainTextCOMM | SymmetricCryptoMessaging

1337_TECH DBA, Austin Texas - 2026
"""

import hashlib
import base64
import os
from typing import Tuple, Optional, List

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey
)
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from backend.crypto.strategy.crypto_strategy_base import CryptoStrategyBase
from backend.crypto.strategy.oqs_provider_strategy import OQSProviderStrategy
from backend.crypto.strategy.liboqs_strategy import LibOQSStrategy
from backend.crypto.strategy.simulated_strategy import SimulatedStrategy


# Default path to the local oqs-provider build
_DEFAULT_OQS_PROVIDER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "oqs-provider-0.10.0"
)


class PostQuantumCrypto:
    """
    Strategy Context for post-quantum cryptographic operations.

    Auto-detects the best available backend on initialization:
      1. OQSProviderStrategy (OpenSSL 3.x + oqs-provider)
      2. LibOQSStrategy (liboqs Python bindings)
      3. SimulatedStrategy (classical crypto fallback)

    Supports runtime strategy switching for testing or upgrades.
    """

    KEM_ALG = "ML-KEM-1024"
    SIG_ALG = "ML-DSA-87"

    def __init__(self, strategy: Optional[CryptoStrategyBase] = None,
                 oqs_provider_path: Optional[str] = None):
        self._oqs_provider_path = oqs_provider_path or _DEFAULT_OQS_PROVIDER_PATH
        self._strategies: List[CryptoStrategyBase] = []
        self._strategy: Optional[CryptoStrategyBase] = None

        if strategy:
            self._strategy = strategy
        else:
            self._strategy = self._auto_detect()

    def _auto_detect(self) -> CryptoStrategyBase:
        """
        Probe backends in priority order and select the first available.
        Mirrors the original _detect_backend() logic but uses Strategy objects.
        """
        candidates = [
            OQSProviderStrategy(
                self.KEM_ALG, self.SIG_ALG,
                provider_path=self._resolve_provider_path()
            ),
            LibOQSStrategy(self.KEM_ALG, self.SIG_ALG),
            SimulatedStrategy(self.KEM_ALG, self.SIG_ALG),
        ]

        self._strategies = candidates

        for candidate in candidates:
            if candidate.available:
                return candidate

        # SimulatedStrategy should always be available, but just in case
        return candidates[-1]

    def _resolve_provider_path(self) -> Optional[str]:
        """Resolve the oqs-provider shared library directory."""
        # Check for built provider in standard locations
        for subdir in ["_build/lib", "build/lib", "lib", ""]:
            candidate = os.path.join(self._oqs_provider_path, subdir)
            if os.path.isdir(candidate):
                # Look for the .so/.dylib file
                for f in os.listdir(candidate) if os.path.isdir(candidate) else []:
                    if "oqsprovider" in f and (f.endswith(".so") or f.endswith(".dylib")):
                        return candidate
        # Fall back to env var or None
        return os.environ.get("OPENSSL_MODULES")

    # ── Strategy Management ──

    @property
    def strategy(self) -> CryptoStrategyBase:
        return self._strategy

    def set_strategy(self, strategy: CryptoStrategyBase):
        """Switch the crypto strategy at runtime."""
        self._strategy = strategy

    @property
    def backend_name(self) -> str:
        """Backward-compatible property returning the strategy name."""
        name_map = {
            "OQSProviderStrategy": "oqs-provider",
            "LibOQSStrategy": "liboqs",
            "SimulatedStrategy": "simulated",
        }
        return name_map.get(self._strategy.name, self._strategy.name)

    @property
    def available_strategies(self) -> List[dict]:
        """Return info about all probed strategies and their availability."""
        return [s.get_info() for s in self._strategies]

    # ── KEM Delegation (FIPS 203) ──

    def kem_keygen(self) -> Tuple[bytes, bytes]:
        """Generate ML-KEM-1024 keypair via the active strategy."""
        return self._strategy.kem_keygen()

    def kem_encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """Encapsulate a shared secret via the active strategy."""
        return self._strategy.kem_encapsulate(public_key)

    def kem_decapsulate(self, secret_key: bytes, ciphertext: bytes) -> bytes:
        """Decapsulate to recover shared secret via the active strategy."""
        return self._strategy.kem_decapsulate(secret_key, ciphertext)

    # ── Hybrid Key Exchange: ML-KEM-1024 + X25519 ──

    def hybrid_keygen(self) -> dict:
        """Generate hybrid keypair combining ML-KEM-1024 and X25519."""
        pq_pk, pq_sk = self.kem_keygen()
        x_sk = X25519PrivateKey.generate()
        x_pk = x_sk.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        x_sk_bytes = x_sk.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption()
        )
        return {
            "pq_public_key": pq_pk,
            "pq_secret_key": pq_sk,
            "x25519_public_key": x_pk,
            "x25519_secret_key": x_sk_bytes,
        }

    def hybrid_encapsulate(self, pq_pk: bytes, x25519_pk: bytes) -> Tuple[dict, bytes]:
        """
        Hybrid encapsulation: ML-KEM-1024 + X25519.
        Returns (ciphertext_bundle, combined_shared_secret).
        """
        pq_ct, pq_ss = self.kem_encapsulate(pq_pk)

        eph_sk = X25519PrivateKey.generate()
        eph_pk = eph_sk.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        peer_pk = X25519PublicKey.from_public_bytes(x25519_pk)
        x_ss = eph_sk.exchange(peer_pk)

        # Combine both shared secrets via HKDF
        combined = HKDF(
            algorithm=hashes.SHA256(), length=32,
            salt=None, info=b"riddlerchat-hybrid-mlkem1024-x25519"
        ).derive(pq_ss + x_ss)

        ct_bundle = {
            "pq_ciphertext": base64.b64encode(pq_ct).decode(),
            "x25519_ephemeral": base64.b64encode(eph_pk).decode(),
        }
        return ct_bundle, combined

    def hybrid_decapsulate(self, keys: dict, ct_bundle: dict) -> bytes:
        """Hybrid decapsulation recovering combined shared secret."""
        pq_ct = base64.b64decode(ct_bundle["pq_ciphertext"])
        eph_pk_bytes = base64.b64decode(ct_bundle["x25519_ephemeral"])

        pq_ss = self.kem_decapsulate(keys["pq_secret_key"], pq_ct)

        x_sk = X25519PrivateKey.from_private_bytes(keys["x25519_secret_key"])
        eph_pk = X25519PublicKey.from_public_bytes(eph_pk_bytes)
        x_ss = x_sk.exchange(eph_pk)

        combined = HKDF(
            algorithm=hashes.SHA256(), length=32,
            salt=None, info=b"riddlerchat-hybrid-mlkem1024-x25519"
        ).derive(pq_ss + x_ss)

        return combined

    # ── Signature Delegation (FIPS 204) ──

    def sig_keygen(self) -> Tuple[bytes, bytes]:
        """Generate ML-DSA-87 signing keypair via the active strategy."""
        return self._strategy.sig_keygen()

    def sig_sign(self, secret_key: bytes, message: bytes) -> bytes:
        """Sign a message via the active strategy."""
        return self._strategy.sig_sign(secret_key, message)

    def sig_verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Verify a signature via the active strategy."""
        return self._strategy.sig_verify(public_key, message, signature)

    # ── PQ Fingerprint ──

    @staticmethod
    def fingerprint(public_key: bytes) -> str:
        """Generate a human-readable PQ fingerprint like A4F0-11C9-8E32."""
        digest = hashlib.sha256(public_key).hexdigest().upper()
        return f"{digest[:4]}\u00b7{digest[4:8]}\u00b7{digest[8:12]}"
