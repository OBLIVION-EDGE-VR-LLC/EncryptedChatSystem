"""
Crypto Strategy Package - Gang of Four Strategy Pattern
for post-quantum cryptographic backend selection.

Mirrors the design from chatclient/TheRiddlerChatSystem/Model/stateful_messaging/
where CommunicationBase defines the abstract interface and concrete strategies
(PlainTextCOMM, SymmetricCryptoMessaging) provide implementations.

1337_TECH DBA, Austin Texas - 2026
"""

from .crypto_strategy_base import CryptoStrategyBase
from .oqs_provider_strategy import OQSProviderStrategy
from .liboqs_strategy import LibOQSStrategy
from .simulated_strategy import SimulatedStrategy
