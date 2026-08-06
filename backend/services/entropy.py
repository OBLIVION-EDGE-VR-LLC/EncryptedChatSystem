"""
Entropy Service - monitors system entropy pool quality
and provides TRNG status for the UI status bar.

1337_TECH DBA, Austin Texas - 2026
"""

import os
import struct
import time


class EntropyService:
    """Monitors system entropy and provides random data quality info."""

    def __init__(self):
        self._source = self._detect_source()

    def _detect_source(self) -> str:
        if os.path.exists("/dev/hwrng"):
            return "/dev/hwrng"
        return "/dev/urandom"

    def get_status(self) -> dict:
        """Get entropy pool status for the UI TRNG indicator."""
        entropy_avail = self._get_entropy_available()
        return {
            "source": self._source,
            "bits": 256,
            "available": entropy_avail,
            "healthy": entropy_avail >= 256,
            "label": "TRNG entropy pool" if "/hwrng" in self._source else "PRNG entropy pool",
        }

    def _get_entropy_available(self) -> int:
        try:
            with open("/proc/sys/kernel/random/entropy_avail", "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 4096  # default assumption for non-Linux

    def generate_seed(self, nbytes: int = 32) -> bytes:
        """Generate cryptographically secure random bytes."""
        return os.urandom(nbytes)
