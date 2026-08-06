"""
CryptoStrategyBase - Abstract base for post-quantum crypto strategies.

Modeled after chatclient/TheRiddlerChatSystem/Model/stateful_messaging/COM/communication_base.py
which defines an ABC with abstract send/recv/handle_cmd methods that concrete
strategies (PlainTextCOMM, SymmetricCryptoMessaging) override.

Here, we define abstract KEM and signature operations that each backend
(oqs-provider, liboqs, simulated) must implement.

1337_TECH DBA, Austin Texas - 2026
"""

from abc import ABC, abstractmethod
from typing import Tuple


class CryptoStrategyBase(ABC):
    """
    Abstract strategy interface for post-quantum cryptographic operations.

    Concrete strategies must implement:
      - kem_keygen()       -> (public_key, secret_key)
      - kem_encapsulate()  -> (ciphertext, shared_secret)
      - kem_decapsulate()  -> shared_secret
      - sig_keygen()       -> (public_key, secret_key)
      - sig_sign()         -> signature
      - sig_verify()       -> bool
    """

    def __init__(self, kem_algorithm: str, sig_algorithm: str):
        self._kem_algorithm = kem_algorithm
        self._sig_algorithm = sig_algorithm
        self._available = False
        self._init_backend()

    def _init_backend(self):
        """Initialize and probe the backend. Sets self._available."""
        try:
            self._available = self._probe()
        except Exception:
            self._available = False

    @abstractmethod
    def _probe(self) -> bool:
        """Probe whether this backend is available on the current system."""
        raise NotImplementedError("Subclasses must implement _probe")

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def kem_algorithm(self) -> str:
        return self._kem_algorithm

    @property
    def sig_algorithm(self) -> str:
        return self._sig_algorithm

    @abstractmethod
    def kem_keygen(self) -> Tuple[bytes, bytes]:
        """Generate a KEM keypair. Returns (public_key, secret_key)."""
        raise NotImplementedError("Subclasses must implement kem_keygen")

    @abstractmethod
    def kem_encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """Encapsulate a shared secret. Returns (ciphertext, shared_secret)."""
        raise NotImplementedError("Subclasses must implement kem_encapsulate")

    @abstractmethod
    def kem_decapsulate(self, secret_key: bytes, ciphertext: bytes) -> bytes:
        """Decapsulate to recover the shared secret."""
        raise NotImplementedError("Subclasses must implement kem_decapsulate")

    @abstractmethod
    def sig_keygen(self) -> Tuple[bytes, bytes]:
        """Generate a signing keypair. Returns (public_key, secret_key)."""
        raise NotImplementedError("Subclasses must implement sig_keygen")

    @abstractmethod
    def sig_sign(self, secret_key: bytes, message: bytes) -> bytes:
        """Sign a message. Returns the signature bytes."""
        raise NotImplementedError("Subclasses must implement sig_sign")

    @abstractmethod
    def sig_verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Verify a signature. Returns True if valid."""
        raise NotImplementedError("Subclasses must implement sig_verify")

    def get_info(self) -> dict:
        """Return backend capability information for status display."""
        return {
            "strategy": self.name,
            "available": self._available,
            "kem_algorithm": self._kem_algorithm,
            "sig_algorithm": self._sig_algorithm,
        }
