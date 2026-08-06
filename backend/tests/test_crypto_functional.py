"""
Functional Tests - End-to-end cryptographic operations

Tests that actual encrypt/decrypt and sign/verify roundtrips work
correctly through the Strategy pattern, validating real crypto output.

1337_TECH DBA, Austin Texas - 2026
"""

import pytest
import os

from backend.crypto.pq_crypto import PostQuantumCrypto
from backend.crypto.symmetric import SymmetricCrypto
from backend.crypto.strategy.simulated_strategy import SimulatedStrategy


class TestKEMRoundtrip:
    """KEM keygen -> encapsulate -> decapsulate produces matching shared secrets."""

    def test_kem_roundtrip_simulated(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        pk, sk = pq.kem_keygen()
        ct, ss_sender = pq.kem_encapsulate(pk)
        ss_receiver = pq.kem_decapsulate(sk, ct)
        assert ss_sender == ss_receiver
        assert len(ss_sender) == 32  # HKDF output is 32 bytes

    def test_kem_keygen_produces_unique_keys(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        pk1, sk1 = pq.kem_keygen()
        pk2, sk2 = pq.kem_keygen()
        assert pk1 != pk2
        assert sk1 != sk2

    def test_kem_produces_unique_shared_secrets(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        pk, sk = pq.kem_keygen()
        ct1, ss1 = pq.kem_encapsulate(pk)
        ct2, ss2 = pq.kem_encapsulate(pk)
        # Each encapsulation uses a new ephemeral key
        assert ct1 != ct2
        assert ss1 != ss2


class TestHybridKEMRoundtrip:
    """Hybrid ML-KEM-1024 + X25519 key exchange roundtrip."""

    def test_hybrid_roundtrip(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        keys = pq.hybrid_keygen()

        ct_bundle, ss_sender = pq.hybrid_encapsulate(
            keys["pq_public_key"], keys["x25519_public_key"]
        )
        ss_receiver = pq.hybrid_decapsulate(keys, ct_bundle)

        assert ss_sender == ss_receiver
        assert len(ss_sender) == 32

    def test_hybrid_keygen_components(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        keys = pq.hybrid_keygen()

        assert "pq_public_key" in keys
        assert "pq_secret_key" in keys
        assert "x25519_public_key" in keys
        assert "x25519_secret_key" in keys

        # X25519 keys are 32 bytes
        assert len(keys["x25519_public_key"]) == 32
        assert len(keys["x25519_secret_key"]) == 32

    def test_hybrid_ct_bundle_format(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        keys = pq.hybrid_keygen()
        ct_bundle, _ = pq.hybrid_encapsulate(
            keys["pq_public_key"], keys["x25519_public_key"]
        )
        assert "pq_ciphertext" in ct_bundle
        assert "x25519_ephemeral" in ct_bundle
        # Both should be base64-encoded strings
        assert isinstance(ct_bundle["pq_ciphertext"], str)
        assert isinstance(ct_bundle["x25519_ephemeral"], str)


class TestSignatureRoundtrip:
    """Signature keygen -> sign -> verify roundtrip."""

    def test_sign_verify_valid(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        pk, sk = pq.sig_keygen()
        message = b"Riddle me this, Batman!"
        signature = pq.sig_sign(sk, message)
        assert pq.sig_verify(pk, message, signature) is True

    def test_sign_verify_different_messages(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        pk, sk = pq.sig_keygen()
        msg1 = b"First riddle"
        msg2 = b"Second riddle"
        sig1 = pq.sig_sign(sk, msg1)
        sig2 = pq.sig_sign(sk, msg2)
        assert sig1 != sig2
        assert pq.sig_verify(pk, msg1, sig1) is True
        assert pq.sig_verify(pk, msg2, sig2) is True

    def test_sig_keygen_unique(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        pk1, sk1 = pq.sig_keygen()
        pk2, sk2 = pq.sig_keygen()
        assert pk1 != pk2
        assert sk1 != sk2


class TestSymmetricEncryption:
    """AES-256-GCM encryption/decryption roundtrip."""

    def test_encrypt_decrypt_roundtrip(self, symmetric_crypto):
        plaintext = b"The Riddler was here"
        sealed = symmetric_crypto.encrypt(plaintext)
        recovered = symmetric_crypto.decrypt(sealed)
        assert recovered == plaintext

    def test_encrypt_with_aad(self, symmetric_crypto):
        plaintext = b"Authenticated data"
        aad = b"channel:riddler-chat"
        sealed = symmetric_crypto.encrypt(plaintext, aad=aad)
        recovered = symmetric_crypto.decrypt(sealed, aad=aad)
        assert recovered == plaintext

    def test_unique_ciphertexts(self, symmetric_crypto):
        plaintext = b"Same message"
        c1 = symmetric_crypto.encrypt(plaintext)
        c2 = symmetric_crypto.encrypt(plaintext)
        # Nonces differ, so ciphertexts must differ
        assert c1 != c2

    def test_rekey(self, symmetric_crypto):
        old_key = symmetric_crypto.key
        symmetric_crypto.rekey()
        assert symmetric_crypto.key != old_key


class TestFingerprint:
    """PQ fingerprint generation."""

    def test_fingerprint_format(self):
        pk = os.urandom(32)
        fp = PostQuantumCrypto.fingerprint(pk)
        # Format: XXXX·XXXX·XXXX
        parts = fp.split("\u00b7")
        assert len(parts) == 3
        for part in parts:
            assert len(part) == 4
            assert all(c in "0123456789ABCDEF" for c in part)

    def test_fingerprint_deterministic(self):
        pk = os.urandom(32)
        assert PostQuantumCrypto.fingerprint(pk) == PostQuantumCrypto.fingerprint(pk)

    def test_fingerprint_unique_per_key(self):
        pk1 = os.urandom(32)
        pk2 = os.urandom(32)
        assert PostQuantumCrypto.fingerprint(pk1) != PostQuantumCrypto.fingerprint(pk2)


class TestFullMessageFlow:
    """End-to-end: keygen -> hybrid exchange -> encrypt -> sign -> verify -> decrypt."""

    def test_complete_message_flow(self, pq_crypto_simulated):
        pq = pq_crypto_simulated

        # Alice generates her keys
        alice_keys = pq.hybrid_keygen()
        alice_sig_pk, alice_sig_sk = pq.sig_keygen()

        # Bob generates his keys
        bob_keys = pq.hybrid_keygen()

        # Alice encapsulates to Bob
        ct_bundle, shared_secret = pq.hybrid_encapsulate(
            bob_keys["pq_public_key"], bob_keys["x25519_public_key"]
        )

        # Bob decapsulates
        bob_shared_secret = pq.hybrid_decapsulate(bob_keys, ct_bundle)
        assert shared_secret == bob_shared_secret

        # Alice encrypts a message with the shared secret
        cipher = SymmetricCrypto(key=shared_secret)
        message = b"What has a head and a tail but no body?"
        sealed = cipher.encrypt(message)

        # Alice signs the plaintext
        signature = pq.sig_sign(alice_sig_sk, message)

        # Bob decrypts
        bob_cipher = SymmetricCrypto(key=bob_shared_secret)
        recovered = bob_cipher.decrypt(sealed)
        assert recovered == message

        # Bob verifies signature
        assert pq.sig_verify(alice_sig_pk, recovered, signature) is True
