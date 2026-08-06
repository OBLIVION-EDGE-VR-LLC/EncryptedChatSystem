"""
Integration Tests - OQS Provider Strategy

Tests the OQSProviderStrategy when the oqs-provider is actually
available on the system. These tests are automatically skipped
if oqs-provider is not installed/built.

1337_TECH DBA, Austin Texas - 2026
"""

import pytest

from backend.crypto.strategy.oqs_provider_strategy import OQSProviderStrategy
from backend.crypto.pq_crypto import PostQuantumCrypto


@pytest.fixture
def oqs_strategy():
    s = OQSProviderStrategy()
    if not s.available:
        pytest.skip("oqs-provider not available - skipping integration tests")
    return s


class TestOQSProviderKEM:
    """Real ML-KEM operations via oqs-provider."""

    def test_kem_keygen(self, oqs_strategy):
        pk, sk = oqs_strategy.kem_keygen()
        assert isinstance(pk, bytes)
        assert isinstance(sk, bytes)
        assert len(pk) > 0
        assert len(sk) > 0

    def test_kem_roundtrip(self, oqs_strategy):
        pk, sk = oqs_strategy.kem_keygen()
        ct, ss_enc = oqs_strategy.kem_encapsulate(pk)
        ss_dec = oqs_strategy.kem_decapsulate(sk, ct)
        assert ss_enc == ss_dec

    def test_kem_unique_encapsulations(self, oqs_strategy):
        pk, sk = oqs_strategy.kem_keygen()
        ct1, ss1 = oqs_strategy.kem_encapsulate(pk)
        ct2, ss2 = oqs_strategy.kem_encapsulate(pk)
        assert ct1 != ct2
        assert ss1 != ss2


class TestOQSProviderSignatures:
    """Real ML-DSA operations via oqs-provider."""

    def test_sig_keygen(self, oqs_strategy):
        pk, sk = oqs_strategy.sig_keygen()
        assert isinstance(pk, bytes)
        assert isinstance(sk, bytes)

    def test_sign_verify(self, oqs_strategy):
        pk, sk = oqs_strategy.sig_keygen()
        msg = b"Riddle me this via oqs-provider"
        sig = oqs_strategy.sig_sign(sk, msg)
        assert oqs_strategy.sig_verify(pk, msg, sig) is True

    def test_tampered_sig_rejected(self, oqs_strategy):
        pk, sk = oqs_strategy.sig_keygen()
        msg = b"Tamper test"
        sig = oqs_strategy.sig_sign(sk, msg)
        tampered = bytearray(sig)
        tampered[0] ^= 0xFF
        assert oqs_strategy.sig_verify(pk, msg, bytes(tampered)) is False


class TestOQSProviderViaContext:
    """Test oqs-provider through the PostQuantumCrypto context."""

    def test_context_with_oqs_strategy(self, oqs_strategy):
        pq = PostQuantumCrypto(strategy=oqs_strategy)
        assert pq.backend_name == "oqs-provider"

        keys = pq.hybrid_keygen()
        assert "pq_public_key" in keys
        assert len(keys["pq_public_key"]) > 0

    def test_full_hybrid_roundtrip_via_context(self, oqs_strategy):
        pq = PostQuantumCrypto(strategy=oqs_strategy)
        keys = pq.hybrid_keygen()
        ct_bundle, ss_enc = pq.hybrid_encapsulate(
            keys["pq_public_key"], keys["x25519_public_key"]
        )
        ss_dec = pq.hybrid_decapsulate(keys, ct_bundle)
        assert ss_enc == ss_dec


class TestOQSProviderInfo:
    """Provider metadata and capability reporting."""

    def test_info_includes_provider_details(self, oqs_strategy):
        info = oqs_strategy.get_info()
        assert info["strategy"] == "OQSProviderStrategy"
        assert info["available"] is True
        assert info["openssl_kem_name"] == "mlkem1024"
        assert info["openssl_sig_name"] == "mldsa87"

    def test_algorithm_names(self, oqs_strategy):
        assert oqs_strategy.kem_algorithm == "ML-KEM-1024"
        assert oqs_strategy.sig_algorithm == "ML-DSA-87"
