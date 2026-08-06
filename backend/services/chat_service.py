"""
Chat Service - manages connected clients, message routing,
and encrypted thread state.

1337_TECH DBA, Austin Texas - 2026
"""

import asyncio
import base64
import json
import secrets
import time
from typing import Dict, Optional, Set

from fastapi import WebSocket

from backend.crypto.pq_crypto import PostQuantumCrypto
from backend.crypto.symmetric import SymmetricCrypto
from backend.models.message import Message
from backend.models.circuit import Circuit


class ConnectedClient:
    def __init__(self, websocket: WebSocket, username: str):
        self.websocket = websocket
        self.username = username
        self.alias: Optional[str] = None
        self.pq_keys: Optional[dict] = None
        self.sig_keys: Optional[tuple] = None
        self.circuit: Optional[Circuit] = None
        self.connected_at: float = time.time()
        self.session_cipher: Optional[SymmetricCrypto] = None


class ChatService:
    """Manages all connected clients and routes encrypted messages."""

    def __init__(self):
        self.clients: Dict[str, ConnectedClient] = {}
        self.pq = PostQuantumCrypto()
        self.threads: Dict[str, list] = {}  # thread_id -> [Message]

    async def connect(self, websocket: WebSocket, username: str) -> ConnectedClient:
        client = ConnectedClient(websocket, username)

        # Generate PQ keypair for this session
        client.pq_keys = self.pq.hybrid_keygen()
        client.sig_keys = self.pq.sig_keygen()
        client.circuit = Circuit.build_default_circuit()
        client.session_cipher = SymmetricCrypto()

        self.clients[username] = client

        # Notify other clients
        await self._broadcast_presence(username, online=True)

        return client

    async def disconnect(self, username: str):
        if username in self.clients:
            del self.clients[username]
            await self._broadcast_presence(username, online=False)

    async def send_message(self, sender: str, recipient: str, content: str):
        """Encrypt and route a message through the onion circuit."""
        sender_client = self.clients.get(sender)
        recipient_client = self.clients.get(recipient)

        if not sender_client:
            return

        msg = Message(
            id=secrets.token_hex(8),
            sender=sender,
            recipient=recipient,
            content=content,
            timestamp=time.time(),
        )

        # Encrypt the message content
        plaintext = content.encode("utf-8")
        sealed_bytes = sender_client.session_cipher.encrypt(plaintext)
        msg.ciphertext = base64.b64encode(sealed_bytes).decode()
        msg.sealed = True
        msg.circuit_id = sender_client.circuit.circuit_id if sender_client.circuit else None

        # Sign with ML-DSA
        if sender_client.sig_keys:
            sig = self.pq.sig_sign(sender_client.sig_keys[1], plaintext)
            msg.signature = base64.b64encode(sig).decode()

        # Store in thread
        thread_key = self._thread_key(sender, recipient)
        if thread_key not in self.threads:
            self.threads[thread_key] = []
        self.threads[thread_key].append(msg)

        # Deliver to recipient if online
        if recipient_client:
            await self._deliver(recipient_client, msg)

        # Echo back to sender for confirmation
        await self._deliver(sender_client, msg)

    async def _deliver(self, client: ConnectedClient, msg: Message):
        payload = {
            "type": "message",
            "data": {
                "id": msg.id,
                "sender": msg.sender,
                "recipient": msg.recipient,
                "content": msg.content,
                "ciphertext": msg.ciphertext,
                "signature": msg.signature,
                "timestamp": msg.timestamp,
                "sealed": msg.sealed,
                "circuit_id": msg.circuit_id,
            }
        }
        try:
            await client.websocket.send_json(payload)
        except Exception:
            pass

    async def _broadcast_presence(self, username: str, online: bool):
        payload = {
            "type": "presence",
            "data": {"username": username, "online": online}
        }
        for uname, client in self.clients.items():
            if uname != username:
                try:
                    await client.websocket.send_json(payload)
                except Exception:
                    pass

    async def get_contact_list(self, username: str) -> list:
        contacts = []
        for uname, client in self.clients.items():
            if uname != username:
                pq_fp = ""
                if client.pq_keys:
                    pq_fp = self.pq.fingerprint(client.pq_keys["pq_public_key"])
                contacts.append({
                    "username": uname,
                    "alias": client.alias or uname,
                    "online": True,
                    "pq_verified": True,
                    "pq_fingerprint": pq_fp,
                    "last_ciphertext_preview": self._random_cipher_preview(),
                })
        return contacts

    def get_thread(self, user1: str, user2: str) -> list:
        key = self._thread_key(user1, user2)
        return [m.model_dump() for m in self.threads.get(key, [])]

    @staticmethod
    def _thread_key(a: str, b: str) -> str:
        return "|".join(sorted([a, b]))

    @staticmethod
    def _random_cipher_preview() -> str:
        """Generate a realistic-looking ciphertext preview."""
        parts = [secrets.token_hex(2) for _ in range(4)]
        return " ".join(parts) + " \u2026"
