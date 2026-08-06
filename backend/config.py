"""
RiddlerChat Backend Configuration
1337_TECH DBA, Austin Texas - 2026
"""

import os

HOST = os.getenv("RIDDLER_HOST", "127.0.0.1")
PORT = int(os.getenv("RIDDLER_PORT", "7575"))
WS_PORT = int(os.getenv("RIDDLER_WS_PORT", "7576"))

# Post-Quantum Algorithm Configuration (NIST FIPS 203/204)
PQ_KEM_ALGORITHM = "ML-KEM-1024"       # FIPS 203 - Key Encapsulation
PQ_SIG_ALGORITHM = "ML-DSA-87"         # FIPS 204 - Digital Signatures
SYMMETRIC_ALGORITHM = "AES-256-GCM"    # NIST approved symmetric
HYBRID_KEX = True                       # ML-KEM + X25519 hybrid

# Onion Routing
DEFAULT_RELAY_COUNT = 3
CIRCUIT_TIMEOUT_SECONDS = 300

# Entropy
ENTROPY_BITS = 256
ENTROPY_SOURCE = "/dev/hwrng" if os.path.exists("/dev/hwrng") else "/dev/urandom"

# OpenSSL
OPENSSL_MIN_VERSION = "3.3.0"

# OQS Provider (oqs-provider-0.10.0 for OpenSSL 3.x post-quantum support)
OQS_PROVIDER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "oqs-provider-0.10.0"
)
