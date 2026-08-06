"""
Security Tests - Verifies cryptographic security properties

Tests attack resistance, key isolation, tamper detection, and
proper nonce/IV handling to ensure the crypto layer is sound.

1337_TECH DBA, Austin Texas - 2026
"""

import os
import struct
import time
import pytest

from cryptography.exceptions import InvalidTag

from backend.crypto.pq_crypto import PostQuantumCrypto
from backend.crypto.symmetric import SymmetricCrypto
from backend.crypto.strategy.simulated_strategy import SimulatedStrategy


class TestTamperDetection:
    """Tampering with ciphertext or signatures must be detected."""

    def test_tampered_ciphertext_rejected(self, symmetric_crypto):
        plaintext = b"Sensitive riddle"
        sealed = symmetric_crypto.encrypt(plaintext)

        # Flip a bit in the ciphertext body (after the 12-byte nonce)
        tampered = bytearray(sealed)
        tampered[14] ^= 0xFF
        tampered = bytes(tampered)

        with pytest.raises(InvalidTag):
            symmetric_crypto.decrypt(tampered)

    def test_tampered_nonce_rejected(self, symmetric_crypto):
        plaintext = b"Another riddle"
        sealed = symmetric_crypto.encrypt(plaintext)

        # Corrupt the nonce (first 12 bytes)
        tampered = bytearray(sealed)
        tampered[0] ^= 0xFF
        tampered = bytes(tampered)

        with pytest.raises(InvalidTag):
            symmetric_crypto.decrypt(tampered)

    def test_tampered_aad_rejected(self, symmetric_crypto):
        plaintext = b"AAD protected"
        aad = b"correct-channel"
        sealed = symmetric_crypto.encrypt(plaintext, aad=aad)

        # Decrypt with wrong AAD
        with pytest.raises(InvalidTag):
            symmetric_crypto.decrypt(sealed, aad=b"wrong-channel")

    def test_wrong_key_rejected(self):
        cipher1 = SymmetricCrypto()
        cipher2 = SymmetricCrypto()
        plaintext = b"Key isolation test"
        sealed = cipher1.encrypt(plaintext)

        with pytest.raises(InvalidTag):
            cipher2.decrypt(sealed)

    def test_tampered_signature_rejected(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        pk, sk = pq.sig_keygen()
        message = b"Sign this riddle"
        signature = pq.sig_sign(sk, message)

        # Tamper with signature
        tampered_sig = bytearray(signature)
        tampered_sig[0] ^= 0xFF
        tampered_sig = bytes(tampered_sig)

        assert pq.sig_verify(pk, message, tampered_sig) is False

    def test_wrong_message_signature_rejected(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        pk, sk = pq.sig_keygen()
        signature = pq.sig_sign(sk, b"Original message")

        assert pq.sig_verify(pk, b"Different message", signature) is False

    def test_wrong_key_signature_rejected(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        pk1, sk1 = pq.sig_keygen()
        pk2, sk2 = pq.sig_keygen()
        message = b"Cross-key test"
        signature = pq.sig_sign(sk1, message)

        # Verify with wrong public key
        assert pq.sig_verify(pk2, message, signature) is False


class TestKeyIsolation:
    """Keys from one session must not work in another."""

    def test_kem_cross_session_isolation(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        pk1, sk1 = pq.kem_keygen()
        pk2, sk2 = pq.kem_keygen()

        # Encapsulate with pk1
        ct, ss = pq.kem_encapsulate(pk1)

        # Decapsulate with sk2 should produce a different shared secret
        ss2 = pq.kem_decapsulate(sk2, ct)
        assert ss != ss2

    def test_hybrid_cross_session_isolation(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        alice_keys = pq.hybrid_keygen()
        bob_keys = pq.hybrid_keygen()

        ct_bundle, ss_for_alice = pq.hybrid_encapsulate(
            alice_keys["pq_public_key"], alice_keys["x25519_public_key"]
        )

        # Bob tries to decapsulate something meant for Alice
        # This should produce a different shared secret
        ss_bob_got = pq.hybrid_decapsulate(bob_keys, ct_bundle)
        assert ss_for_alice != ss_bob_got

    def test_symmetric_key_independence(self):
        key1 = SymmetricCrypto.generate_key()
        key2 = SymmetricCrypto.generate_key()
        assert key1 != key2
        assert len(key1) == 32
        assert len(key2) == 32


class TestNonceProperties:
    """Nonces must be unique and properly structured."""

    def test_nonce_uniqueness(self, symmetric_crypto):
        plaintext = b"Nonce test"
        sealed1 = symmetric_crypto.encrypt(plaintext)
        sealed2 = symmetric_crypto.encrypt(plaintext)

        nonce1 = sealed1[:12]
        nonce2 = sealed2[:12]
        assert nonce1 != nonce2

    def test_nonce_has_timestamp_component(self, symmetric_crypto):
        plaintext = b"Timestamp nonce"
        sealed = symmetric_crypto.encrypt(plaintext)
        nonce = sealed[:12]

        # First 4 bytes are timestamp
        ts_bytes = nonce[:4]
        ts = struct.unpack(">I", ts_bytes)[0]
        now = int(time.time()) & 0xFFFFFFFF
        # Should be within a few seconds of current time
        assert abs(ts - now) < 5

    def test_nonce_counter_increments(self, symmetric_crypto):
        sealed1 = symmetric_crypto.encrypt(b"msg1")
        sealed2 = symmetric_crypto.encrypt(b"msg2")

        # Counter is bytes 4-8
        ctr1 = struct.unpack(">I", sealed1[4:8])[0]
        ctr2 = struct.unpack(">I", sealed2[4:8])[0]
        assert ctr2 == ctr1 + 1

    def test_nonce_has_random_component(self, symmetric_crypto):
        sealed1 = symmetric_crypto.encrypt(b"rand1")
        sealed2 = symmetric_crypto.encrypt(b"rand2")

        # Random is bytes 8-12; very unlikely to collide
        rand1 = sealed1[8:12]
        rand2 = sealed2[8:12]
        assert rand1 != rand2


class TestKeySize:
    """Cryptographic keys must meet minimum size requirements."""

    def test_symmetric_key_is_256_bits(self):
        cipher = SymmetricCrypto()
        assert len(cipher.key) == 32  # 256 bits

    def test_symmetric_rejects_wrong_key_size(self):
        with pytest.raises(ValueError):
            SymmetricCrypto(key=b"too_short")

    def test_kem_keys_are_nonempty(self, pq_crypto_simulated):
        pk, sk = pq_crypto_simulated.kem_keygen()
        assert len(pk) > 0
        assert len(sk) > 0

    def test_sig_keys_are_nonempty(self, pq_crypto_simulated):
        pk, sk = pq_crypto_simulated.sig_keygen()
        assert len(pk) > 0
        assert len(sk) > 0


class TestForwardSecrecy:
    """Rekeying provides forward secrecy."""

    def test_rekey_changes_key(self):
        cipher = SymmetricCrypto()
        old_key = cipher.key
        cipher.rekey()
        new_key = cipher.key
        assert old_key != new_key

    def test_old_ciphertext_fails_after_rekey(self):
        cipher = SymmetricCrypto()
        sealed = cipher.encrypt(b"Before rekey")
        old_key = cipher.key

        cipher.rekey()

        # Old ciphertext should fail with new key
        with pytest.raises(InvalidTag):
            cipher.decrypt(sealed)

        # But old key still decrypts it
        old_cipher = SymmetricCrypto(key=old_key)
        assert old_cipher.decrypt(sealed) == b"Before rekey"

    def test_rekey_resets_counter(self):
        cipher = SymmetricCrypto()
        cipher.encrypt(b"msg1")
        cipher.encrypt(b"msg2")
        assert cipher._message_counter == 2

        cipher.rekey()
        assert cipher._message_counter == 0


class TestEntropyQuality:
    """Generated keys should have high entropy."""

    def test_symmetric_keys_have_sufficient_entropy(self):
        keys = [SymmetricCrypto.generate_key() for _ in range(100)]
        # All keys should be unique
        assert len(set(keys)) == 100

    def test_kem_keys_have_sufficient_entropy(self, pq_crypto_simulated):
        pairs = [pq_crypto_simulated.kem_keygen() for _ in range(20)]
        pks = [p[0] for p in pairs]
        sks = [p[1] for p in pairs]
        assert len(set(pks)) == 20
        assert len(set(sks)) == 20

    def test_shared_secrets_have_sufficient_entropy(self, pq_crypto_simulated):
        pq = pq_crypto_simulated
        pk, sk = pq.kem_keygen()
        secrets = [pq.kem_encapsulate(pk)[1] for _ in range(20)]
        assert len(set(secrets)) == 20
