"""Onion circuit model for RiddlerChat relay routing."""

from pydantic import BaseModel
from typing import List, Optional
import secrets
import time


class RelayNode(BaseModel):
    id: str
    name: str
    location: str
    role: str  # "guard", "middle", "exit"
    latency_ms: int = 0
    label: str = ""  # Greek letter label


class Circuit(BaseModel):
    circuit_id: str = ""
    relays: List[RelayNode] = []
    established: bool = False
    encryption: str = "AES-256-GCM per layer"
    kem: str = "ML-KEM-1024"
    hybrid: str = "ML-KEM-1024 + X25519"
    created_at: float = 0.0
    total_rtt_ms: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        if not self.circuit_id:
            self.circuit_id = secrets.token_hex(8)
        if self.created_at == 0.0:
            self.created_at = time.time()

    @staticmethod
    def build_default_circuit() -> "Circuit":
        """Build a 3-relay onion circuit with realistic nodes."""
        relays = [
            RelayNode(
                id=secrets.token_hex(4),
                name="Reykjavik", location="IS",
                role="guard", latency_ms=41, label="\u03b1"
            ),
            RelayNode(
                id=secrets.token_hex(4),
                name="Z\u00fcrich", location="CH",
                role="middle", latency_ms=88, label="\u03b2"
            ),
            RelayNode(
                id=secrets.token_hex(4),
                name="Singapore", location="SG",
                role="exit", latency_ms=63, label="\u03b3"
            ),
        ]
        circuit = Circuit(relays=relays)
        circuit.total_rtt_ms = sum(r.latency_ms for r in relays)
        circuit.established = True
        return circuit
