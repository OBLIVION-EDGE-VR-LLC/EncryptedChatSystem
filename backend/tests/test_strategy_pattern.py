"""
Unit Tests - Strategy Pattern Structure and Interface Compliance

Verifies that the GoF Strategy pattern is correctly implemented:
  - CryptoStrategyBase ABC cannot be instantiated
  - All concrete strategies implement the required interface
  - Strategy switching works at runtime
  - Auto-detection selects the best available backend

1337_TECH DBA, Austin Texas - 2026
"""

import pytest
from abc import ABC

from backend.crypto.strategy.crypto_strategy_base import CryptoStrategyBase
from backend.crypto.strategy.simulated_strategy import SimulatedStrategy
from backend.crypto.strategy.liboqs_strategy import LibOQSStrategy
from backend.crypto.strategy.oqs_provider_strategy import OQSProviderStrategy
from backend.crypto.pq_crypto import PostQuantumCrypto


class TestAbstractBaseCannotInstantiate:
    """CryptoStrategyBase is abstract and must not be instantiable."""

    def test_abc_raises_on_instantiation(self):
        with pytest.raises(TypeError):
            CryptoStrategyBase("ML-KEM-1024", "ML-DSA-87")

    def test_abc_is_abstract(self):
        assert issubclass(CryptoStrategyBase, ABC)

    def test_abc_has_required_abstract_methods(self):
        abstract_methods = CryptoStrategyBase.__abstractmethods__
        required = {"_probe", "kem_keygen", "kem_encapsulate", "kem_decapsulate",
                     "sig_keygen", "sig_sign", "sig_verify"}
        assert required.issubset(abstract_methods)


class TestConcreteStrategyInterface:
    """All concrete strategies must implement the full interface."""

    @pytest.mark.parametrize("strategy_cls", [
        SimulatedStrategy, LibOQSStrategy, OQSProviderStrategy
    ])
    def test_is_subclass_of_base(self, strategy_cls):
        assert issubclass(strategy_cls, CryptoStrategyBase)

    @pytest.mark.parametrize("method", [
        "kem_keygen", "kem_encapsulate", "kem_decapsulate",
        "sig_keygen", "sig_sign", "sig_verify",
        "_probe", "get_info"
    ])
    def test_simulated_has_method(self, method):
        s = SimulatedStrategy()
        assert hasattr(s, method)
        assert callable(getattr(s, method))

    def test_simulated_properties(self):
        s = SimulatedStrategy()
        assert s.kem_algorithm == "ML-KEM-1024"
        assert s.sig_algorithm == "ML-DSA-87"
        assert isinstance(s.name, str)
        assert isinstance(s.available, bool)


class TestStrategyAutoDetection:
    """PostQuantumCrypto (Context) auto-detects the best backend."""

    def test_auto_detect_returns_strategy(self):
        pq = PostQuantumCrypto()
        assert isinstance(pq.strategy, CryptoStrategyBase)

    def test_auto_detect_selects_available_backend(self):
        pq = PostQuantumCrypto()
        assert pq.strategy.available is True

    def test_backend_name_is_valid(self):
        pq = PostQuantumCrypto()
        assert pq.backend_name in ("oqs-provider", "liboqs", "simulated")

    def test_available_strategies_populated(self):
        pq = PostQuantumCrypto()
        strats = pq.available_strategies
        assert isinstance(strats, list)
        assert len(strats) >= 1


class TestStrategySwitching:
    """Runtime strategy switching (the core of the Strategy pattern)."""

    def test_switch_to_simulated(self):
        pq = PostQuantumCrypto()
        sim = SimulatedStrategy()
        pq.set_strategy(sim)
        assert pq.strategy is sim
        assert pq.backend_name == "simulated"

    def test_switch_preserves_functionality(self):
        pq = PostQuantumCrypto()
        pq.set_strategy(SimulatedStrategy())
        pk, sk = pq.kem_keygen()
        assert isinstance(pk, bytes)
        assert isinstance(sk, bytes)

    def test_explicit_strategy_in_constructor(self):
        sim = SimulatedStrategy()
        pq = PostQuantumCrypto(strategy=sim)
        assert pq.strategy is sim

    def test_switch_between_strategies(self):
        pq = PostQuantumCrypto(strategy=SimulatedStrategy())
        assert pq.backend_name == "simulated"

        # Switch to a new SimulatedStrategy instance (since others may not be available)
        new_sim = SimulatedStrategy("ML-KEM-768", "ML-DSA-65")
        pq.set_strategy(new_sim)
        assert pq.strategy is new_sim
        assert pq.strategy.kem_algorithm == "ML-KEM-768"


class TestStrategyGetInfo:
    """Each strategy reports its capabilities correctly."""

    def test_simulated_info(self):
        s = SimulatedStrategy()
        info = s.get_info()
        assert info["strategy"] == "SimulatedStrategy"
        assert info["available"] is True
        assert info["kem_algorithm"] == "ML-KEM-1024"
        assert info["sig_algorithm"] == "ML-DSA-87"
        assert "note" in info

    def test_liboqs_info(self):
        s = LibOQSStrategy()
        info = s.get_info()
        assert info["strategy"] == "LibOQSStrategy"
        assert isinstance(info["available"], bool)

    def test_oqs_provider_info(self):
        s = OQSProviderStrategy()
        info = s.get_info()
        assert info["strategy"] == "OQSProviderStrategy"
        assert "provider_path" in info
        assert "openssl_kem_name" in info
