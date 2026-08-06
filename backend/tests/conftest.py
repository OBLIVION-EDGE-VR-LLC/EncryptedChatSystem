"""
Shared pytest fixtures for RiddlerChat backend tests.

1337_TECH DBA, Austin Texas - 2026
"""

import sys
import os
import pytest

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.crypto.strategy.simulated_strategy import SimulatedStrategy
from backend.crypto.strategy.liboqs_strategy import LibOQSStrategy
from backend.crypto.strategy.oqs_provider_strategy import OQSProviderStrategy
from backend.crypto.pq_crypto import PostQuantumCrypto
from backend.crypto.symmetric import SymmetricCrypto


@pytest.fixture
def simulated_strategy():
    return SimulatedStrategy()


@pytest.fixture
def pq_crypto_simulated():
    """PostQuantumCrypto forced to use SimulatedStrategy."""
    return PostQuantumCrypto(strategy=SimulatedStrategy())


@pytest.fixture
def symmetric_crypto():
    return SymmetricCrypto()


@pytest.fixture
def liboqs_strategy():
    """LibOQS strategy - may not be available on all systems."""
    s = LibOQSStrategy()
    if not s.available:
        pytest.skip("liboqs not available on this system")
    return s


@pytest.fixture
def oqs_provider_strategy():
    """OQS provider strategy - may not be available on all systems."""
    s = OQSProviderStrategy()
    if not s.available:
        pytest.skip("oqs-provider not available on this system")
    return s
