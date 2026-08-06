"""
OQS Provider Strategy - Post-quantum crypto via OpenSSL 3.x oqs-provider.

Uses the oqs-provider-0.10.0 shared library loaded into OpenSSL 3.x to
access ML-KEM-1024 (FIPS 203) and ML-DSA-87 (FIPS 204) algorithms
through OpenSSL's provider framework.

The provider is activated via:
  - OPENSSL_MODULES env var pointing to the built provider .so
  - Or openssl.cnf configuration
  - Or explicit -provider/-provider-path CLI flags

1337_TECH DBA, Austin Texas - 2026
"""

import os
import subprocess
import tempfile
from typing import Tuple, Optional

from .crypto_strategy_base import CryptoStrategyBase


# Map our algorithm names to oqs-provider OpenSSL names
_KEM_ALG_MAP = {
    "ML-KEM-1024": "mlkem1024",
    "ML-KEM-768": "mlkem768",
    "ML-KEM-512": "mlkem512",
}

_SIG_ALG_MAP = {
    "ML-DSA-87": "mldsa87",
    "ML-DSA-65": "mldsa65",
    "ML-DSA-44": "mldsa44",
}


class OQSProviderStrategy(CryptoStrategyBase):
    """
    Concrete strategy using the oqs-provider OpenSSL 3.x provider.

    Integrates with the local oqs-provider-0.10.0 build to perform
    real post-quantum KEM and signature operations through OpenSSL CLI.
    """

    def __init__(self, kem_algorithm: str = "ML-KEM-1024",
                 sig_algorithm: str = "ML-DSA-87",
                 provider_path: Optional[str] = None,
                 openssl_bin: str = "openssl"):
        self._provider_path = provider_path
        self._openssl_bin = openssl_bin
        self._oqs_kem_name = _KEM_ALG_MAP.get(kem_algorithm, "mlkem1024")
        self._oqs_sig_name = _SIG_ALG_MAP.get(sig_algorithm, "mldsa87")
        super().__init__(kem_algorithm, sig_algorithm)

    def _probe(self) -> bool:
        """Check if OpenSSL 3.x with oqs-provider is available."""
        try:
            cmd = [self._openssl_bin, "list", "-kem-algorithms"]
            cmd += self._provider_flags()
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5
            )
            if self._oqs_kem_name in result.stdout.lower():
                return True

            # Also check via signature algorithms for sig support
            cmd_sig = [self._openssl_bin, "list", "-signature-algorithms"]
            cmd_sig += self._provider_flags()
            result_sig = subprocess.run(
                cmd_sig, capture_output=True, text=True, timeout=5
            )
            return self._oqs_sig_name in result_sig.stdout.lower()
        except Exception:
            return False

    def _provider_flags(self) -> list:
        """Build -provider and -provider-path flags for OpenSSL commands."""
        flags = ["-provider", "oqsprovider", "-provider", "default"]
        if self._provider_path:
            flags += ["-provider-path", self._provider_path]
        return flags

    def _run_openssl(self, args: list, stdin_data: bytes = None,
                     timeout: int = 10) -> subprocess.CompletedProcess:
        """Run an OpenSSL command with oqs-provider loaded."""
        cmd = [self._openssl_bin] + args + self._provider_flags()
        return subprocess.run(
            cmd, input=stdin_data, capture_output=True, timeout=timeout
        )

    # ── KEM Operations (FIPS 203) ──

    def kem_keygen(self) -> Tuple[bytes, bytes]:
        """Generate ML-KEM keypair via oqs-provider."""
        # Generate private key in DER format
        result = self._run_openssl([
            "genpkey", "-algorithm", self._oqs_kem_name, "-outform", "DER"
        ])
        if result.returncode != 0:
            raise RuntimeError(
                f"oqs-provider KEM keygen failed: {result.stderr.decode()}"
            )
        sk_der = result.stdout

        # Extract public key from private key
        result2 = self._run_openssl(
            ["pkey", "-pubout", "-outform", "DER", "-inform", "DER"],
            stdin_data=sk_der
        )
        if result2.returncode != 0:
            raise RuntimeError(
                f"oqs-provider public key extraction failed: {result2.stderr.decode()}"
            )
        pk_der = result2.stdout

        return pk_der, sk_der

    def kem_encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """
        Encapsulate a shared secret using the oqs-provider.

        Uses OpenSSL pkeyutl with the -encap operation for KEM.
        """
        with tempfile.NamedTemporaryFile(suffix=".der", delete=False) as pk_file:
            pk_file.write(public_key)
            pk_path = pk_file.name

        try:
            # Use pkeyutl -encap for KEM encapsulation
            with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as ct_file:
                ct_path = ct_file.name
            with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as ss_file:
                ss_path = ss_file.name

            result = self._run_openssl([
                "pkeyutl", "-encap",
                "-pubin", "-inkey", pk_path, "-keyform", "DER",
                "-out", ct_path, "-secret", ss_path
            ])

            if result.returncode != 0:
                raise RuntimeError(
                    f"oqs-provider KEM encapsulation failed: {result.stderr.decode()}"
                )

            with open(ct_path, "rb") as f:
                ciphertext = f.read()
            with open(ss_path, "rb") as f:
                shared_secret = f.read()

            return ciphertext, shared_secret
        finally:
            for path in [pk_path, ct_path, ss_path]:
                try:
                    os.unlink(path)
                except OSError:
                    pass

    def kem_decapsulate(self, secret_key: bytes, ciphertext: bytes) -> bytes:
        """
        Decapsulate to recover the shared secret using oqs-provider.

        Uses OpenSSL pkeyutl with the -decap operation for KEM.
        """
        with tempfile.NamedTemporaryFile(suffix=".der", delete=False) as sk_file:
            sk_file.write(secret_key)
            sk_path = sk_file.name
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as ct_file:
            ct_file.write(ciphertext)
            ct_path = ct_file.name

        try:
            with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as ss_file:
                ss_path = ss_file.name

            result = self._run_openssl([
                "pkeyutl", "-decap",
                "-inkey", sk_path, "-keyform", "DER",
                "-in", ct_path, "-secret", ss_path
            ])

            if result.returncode != 0:
                raise RuntimeError(
                    f"oqs-provider KEM decapsulation failed: {result.stderr.decode()}"
                )

            with open(ss_path, "rb") as f:
                return f.read()
        finally:
            for path in [sk_path, ct_path, ss_path]:
                try:
                    os.unlink(path)
                except OSError:
                    pass

    # ── Signature Operations (FIPS 204) ──

    def sig_keygen(self) -> Tuple[bytes, bytes]:
        """Generate ML-DSA signing keypair via oqs-provider."""
        result = self._run_openssl([
            "genpkey", "-algorithm", self._oqs_sig_name, "-outform", "DER"
        ])
        if result.returncode != 0:
            raise RuntimeError(
                f"oqs-provider sig keygen failed: {result.stderr.decode()}"
            )
        sk_der = result.stdout

        result2 = self._run_openssl(
            ["pkey", "-pubout", "-outform", "DER", "-inform", "DER"],
            stdin_data=sk_der
        )
        if result2.returncode != 0:
            raise RuntimeError(
                f"oqs-provider sig pubkey extraction failed: {result2.stderr.decode()}"
            )
        pk_der = result2.stdout

        return pk_der, sk_der

    def sig_sign(self, secret_key: bytes, message: bytes) -> bytes:
        """Sign a message with ML-DSA via oqs-provider."""
        with tempfile.NamedTemporaryFile(suffix=".der", delete=False) as sk_file:
            sk_file.write(secret_key)
            sk_path = sk_file.name
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as msg_file:
            msg_file.write(message)
            msg_path = msg_file.name

        try:
            with tempfile.NamedTemporaryFile(suffix=".sig", delete=False) as sig_file:
                sig_path = sig_file.name

            result = self._run_openssl([
                "pkeyutl", "-sign",
                "-inkey", sk_path, "-keyform", "DER",
                "-in", msg_path, "-out", sig_path,
                "-rawin"
            ])

            if result.returncode != 0:
                raise RuntimeError(
                    f"oqs-provider signing failed: {result.stderr.decode()}"
                )

            with open(sig_path, "rb") as f:
                return f.read()
        finally:
            for path in [sk_path, msg_path, sig_path]:
                try:
                    os.unlink(path)
                except OSError:
                    pass

    def sig_verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Verify an ML-DSA signature via oqs-provider."""
        with tempfile.NamedTemporaryFile(suffix=".der", delete=False) as pk_file:
            pk_file.write(public_key)
            pk_path = pk_file.name
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as msg_file:
            msg_file.write(message)
            msg_path = msg_file.name
        with tempfile.NamedTemporaryFile(suffix=".sig", delete=False) as sig_file:
            sig_file.write(signature)
            sig_path = sig_file.name

        try:
            result = self._run_openssl([
                "pkeyutl", "-verify",
                "-pubin", "-inkey", pk_path, "-keyform", "DER",
                "-in", msg_path, "-sigfile", sig_path,
                "-rawin"
            ])

            return result.returncode == 0
        finally:
            for path in [pk_path, msg_path, sig_path]:
                try:
                    os.unlink(path)
                except OSError:
                    pass

    def get_info(self) -> dict:
        info = super().get_info()
        info["provider_path"] = self._provider_path
        info["openssl_kem_name"] = self._oqs_kem_name
        info["openssl_sig_name"] = self._oqs_sig_name
        return info
