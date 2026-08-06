"""
Onion Relay Service - simulates multi-hop circuit routing
with per-layer AES-256-GCM encryption.

1337_TECH DBA, Austin Texas - 2026
"""

import secrets
import time
from typing import List

from backend.models.circuit import Circuit, RelayNode
from backend.crypto.symmetric import SymmetricCrypto


# Pool of relay nodes to select from
RELAY_POOL = [
    {"name": "Reykjavik", "location": "IS", "avg_latency": 41},
    {"name": "Z\u00fcrich", "location": "CH", "avg_latency": 88},
    {"name": "Singapore", "location": "SG", "avg_latency": 63},
    {"name": "Tokyo", "location": "JP", "avg_latency": 112},
    {"name": "S\u00e3o Paulo", "location": "BR", "avg_latency": 145},
    {"name": "Frankfurt", "location": "DE", "avg_latency": 35},
    {"name": "Toronto", "location": "CA", "avg_latency": 52},
    {"name": "Sydney", "location": "AU", "avg_latency": 178},
    {"name": "Mumbai", "location": "IN", "avg_latency": 134},
    {"name": "Amsterdam", "location": "NL", "avg_latency": 29},
]

LABELS = ["\u03b1", "\u03b2", "\u03b3", "\u03b4", "\u03b5", "\u03b6"]
ROLES = ["guard", "middle", "exit"]


class RelayService:
    """Builds and manages onion routing circuits."""

    def build_circuit(self, hop_count: int = 3) -> Circuit:
        """Select random relays and build a circuit."""
        selected = []
        pool = list(RELAY_POOL)
        secrets.SystemRandom().shuffle(pool)

        for i in range(min(hop_count, len(pool))):
            node = pool[i]
            relay = RelayNode(
                id=secrets.token_hex(4),
                name=node["name"],
                location=node["location"],
                role=ROLES[min(i, len(ROLES) - 1)],
                latency_ms=node["avg_latency"] + secrets.randbelow(20) - 10,
                label=LABELS[i] if i < len(LABELS) else f"R{i}",
            )
            selected.append(relay)

        circuit = Circuit(relays=selected)
        circuit.total_rtt_ms = sum(r.latency_ms for r in selected)
        circuit.established = True
        return circuit

    def onion_encrypt(self, plaintext: bytes, circuit: Circuit) -> bytes:
        """
        Layer encryption: wrap plaintext in AES-256-GCM for each relay
        from exit to guard (innermost = exit layer).
        """
        data = plaintext
        layer_keys = []

        for relay in reversed(circuit.relays):
            cipher = SymmetricCrypto()
            layer_keys.append({"relay": relay.name, "key": cipher.key})
            data = cipher.encrypt(data)

        return data

    def onion_decrypt(self, ciphertext: bytes, layer_keys: list) -> bytes:
        """Peel layers from guard to exit."""
        data = ciphertext
        for layer in layer_keys:
            cipher = SymmetricCrypto(key=layer["key"])
            data = cipher.decrypt(data)
        return data

    def get_circuit_info(self, circuit: Circuit) -> dict:
        """Format circuit info for the UI display."""
        return {
            "circuit_id": circuit.circuit_id,
            "hop_count": len(circuit.relays),
            "total_rtt_ms": circuit.total_rtt_ms,
            "encryption": circuit.encryption,
            "kem": circuit.kem,
            "hybrid": circuit.hybrid,
            "sealed": "ML-KEM-1024 sealed",
            "established": circuit.established,
            "relays": [
                {
                    "name": r.name,
                    "role": r.role,
                    "latency_ms": r.latency_ms,
                    "label": r.label,
                }
                for r in circuit.relays
            ],
        }
