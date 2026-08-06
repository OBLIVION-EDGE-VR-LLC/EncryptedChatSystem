"""
OpenSSL Wrapper Module
Provides OpenSSL version detection and TLS configuration
for post-quantum hybrid connections.

1337_TECH DBA, Austin Texas - 2026
"""

import ssl
import subprocess
import re
from typing import Optional


class OpenSSLWrapper:
    """Wraps OpenSSL operations and provides version/capability info."""

    def __init__(self):
        self._version = self._detect_version()
        self._pq_supported = self._check_pq_support()

    def _detect_version(self) -> str:
        try:
            result = subprocess.run(
                ["openssl", "version"],
                capture_output=True, text=True, timeout=5
            )
            match = re.search(r"OpenSSL\s+([\d.]+\w*)", result.stdout)
            if match:
                return match.group(1)
        except Exception:
            pass
        return ssl.OPENSSL_VERSION.split()[1]

    def _check_pq_support(self) -> bool:
        try:
            result = subprocess.run(
                ["openssl", "list", "-kem-algorithms"],
                capture_output=True, text=True, timeout=5
            )
            return "mlkem" in result.stdout.lower() or "kyber" in result.stdout.lower()
        except Exception:
            return False

    @property
    def version(self) -> str:
        return self._version

    @property
    def pq_supported(self) -> bool:
        return self._pq_supported

    def create_tls_context(self, certfile: Optional[str] = None,
                           keyfile: Optional[str] = None) -> ssl.SSLContext:
        """Create a TLS 1.3 context with strong cipher configuration."""
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        ctx.set_ciphers(
            "TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256"
        )
        if certfile and keyfile:
            ctx.load_cert_chain(certfile, keyfile)
        else:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def get_info(self) -> dict:
        """Return OpenSSL capability information for the UI status bar."""
        return {
            "version": f"OpenSSL {self._version}",
            "pq_kem": self._pq_supported,
            "tls_version": "TLS 1.3",
            "ciphers": ["AES-256-GCM", "CHACHA20-POLY1305"],
        }
