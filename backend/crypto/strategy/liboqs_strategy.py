"""
LibOQS Strategy - Post-quantum crypto via liboqs Python bindings.

Uses the liboqs-python package (import oqs) for direct access to
ML-KEM-1024 (FIPS 203) and ML-DSA-87 (FIPS 204) without requiring
OpenSSL oqs-provider.

1337_TECH DBA, Austin Texas - 2026
"""

from typing import Tuple

from .crypto_strategy_base import CryptoStrategyBase


class LibOQSStrategy(CryptoStrategyBase):
    """
    Concrete strategy using liboqs Python bindings directly.

    Requires: pip install liboqs-python (and liboqs shared library installed).
    """

    def __init__(self, kem_algorithm: str = "ML-KEM-1024",
                 sig_algorithm: str = "ML-DSA-87"):
        super().__init__(kem_algorithm, sig_algorithm)

    def _probe(self) -> bool:
        """Check if liboqs Python bindings are importable and functional."""
        try:
            import oqs
            kem = oqs.KeyEncapsulation(self._kem_algorithm)
            kem.free()
            return True
        except Exception:
            return False

    # ── KEM Operations (FIPS 203) ──

    def kem_keygen(self) -> Tuple[bytes, bytes]:
        import oqs
        kem = oqs.KeyEncapsulation(self._kem_algorithm)
        pk = kem.generate_keypair()
        sk = kem.export_secret_key()
        kem.free()
        return pk, sk

    def kem_encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        import oqs
        kem = oqs.KeyEncapsulation(self._kem_algorithm)
        ct, ss = kem.encap_secret(public_key)
        kem.free()
        return ct, ss

    def kem_decapsulate(self, secret_key: bytes, ciphertext: bytes) -> bytes:
        import oqs
        kem = oqs.KeyEncapsulation(self._kem_algorithm, secret_key=secret_key)
        ss = kem.decap_secret(ciphertext)
        kem.free()
        return ss

    # ── Signature Operations (FIPS 204) ──

    def sig_keygen(self) -> Tuple[bytes, bytes]:
        import oqs
        sig = oqs.Signature(self._sig_algorithm)
        pk = sig.generate_keypair()
        sk = sig.export_secret_key()
        sig.free()
        return pk, sk

    def sig_sign(self, secret_key: bytes, message: bytes) -> bytes:
        import oqs
        sig = oqs.Signature(self._sig_algorithm, secret_key=secret_key)
        signature = sig.sign(message)
        sig.free()
        return signature

    def sig_verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        import oqs
        sig = oqs.Signature(self._sig_algorithm)
        result = sig.verify(message, signature, public_key)
        sig.free()
        return result
