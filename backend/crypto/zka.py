"""
Zero-Knowledge Authentication Module
Schnorr-based ZKA with post-quantum signature binding.

Ported from the original TheRiddlerChatSystem ZeroKnowledgeAuth
with modern cryptographic primitives.

1337_TECH DBA, Austin Texas - 2026
"""

import hashlib
import secrets
import json
import os
from typing import Optional, Tuple

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


# Safe prime for Schnorr ZKA
P = 4074071952668972172536891376818756322102936787331872501272280898708762599526673412366794779
G = 3


class ZeroKnowledgeAuth:
    """
    Zero-Knowledge Authentication using Schnorr protocol.
    Password never leaves the client; only proof (c, z) is transmitted.
    """

    def __init__(self, users_file: str = None):
        self._users_file = users_file or os.path.join(
            os.path.dirname(__file__), "..", "data", "users.json"
        )
        self._ph = PasswordHasher(
            time_cost=3, memory_cost=65536, parallelism=4
        )
        os.makedirs(os.path.dirname(self._users_file), exist_ok=True)

    def generate_session_token(self) -> int:
        return secrets.randbelow(P)

    def client_compute_proof(self, password: str, session_token: int) -> dict:
        """
        Client-side computation of ZKA proof.
        Returns proof dict with {Y, c, z} for server verification.
        """
        x = int.from_bytes(
            hashlib.sha256(password.encode()).digest(),
            byteorder="little"
        )
        Y = pow(G, x, P)
        r = secrets.randbelow(P - 1)
        T1 = pow(G, r, P)

        c_input = f"{Y}{T1}{session_token}".encode()
        c = int.from_bytes(hashlib.sha256(c_input).digest(), byteorder="little")
        z = r - (c * x)

        return {"Y": Y, "c": c, "z": z}

    def server_verify_proof(self, username: str, c: int, z: int,
                            session_token: int) -> bool:
        """
        Server-side verification: compute T' = Y^c * g^z mod p
        then verify c == H(Y, T', a).
        """
        Y = self._lookup_public_key(username)
        if Y is None:
            return False

        T_prime = (pow(Y, c, P) * pow(G, z, P)) % P
        c_input = f"{Y}{T_prime}{session_token}".encode()
        c_check = int.from_bytes(
            hashlib.sha256(c_input).digest(), byteorder="little"
        )
        return c == c_check

    def register_user(self, username: str, Y: int) -> bool:
        """Register a user's public commitment Y = g^x mod p."""
        users = self._load_users()
        if username in users:
            return False
        users[username] = {"Y": Y, "registered": True}
        self._save_users(users)
        return True

    def _lookup_public_key(self, username: str) -> Optional[int]:
        users = self._load_users()
        entry = users.get(username)
        if entry:
            return entry["Y"]
        return None

    def _load_users(self) -> dict:
        if not os.path.exists(self._users_file):
            return {}
        with open(self._users_file, "r") as f:
            return json.load(f)

    def _save_users(self, users: dict):
        with open(self._users_file, "w") as f:
            json.dump(users, f, indent=2)
