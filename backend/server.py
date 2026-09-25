"""
RiddlerChat Backend Server
FastAPI + WebSocket server providing encrypted chat,
post-quantum key exchange, and onion circuit routing.

1337_TECH DBA, Austin Texas - 2026
"""

import asyncio
import json
import os
import sys
import time
import base64
import secrets

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.crypto.pq_crypto import PostQuantumCrypto
from backend.crypto.openssl_wrapper import OpenSSLWrapper
from backend.crypto.zka import ZeroKnowledgeAuth
from backend.services.chat_service import ChatService
from backend.services.relay_service import RelayService
from backend.services.entropy import EntropyService
from backend.models.circuit import Circuit

app = FastAPI(title="RiddlerChat", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Services ──
chat_service = ChatService()
relay_service = RelayService()
entropy_service = EntropyService()
openssl = OpenSSLWrapper()
pq_crypto = PostQuantumCrypto()
zka = ZeroKnowledgeAuth()


# ── REST Endpoints ──

@app.get("/api/status")
async def get_status():
    """System status for the top bar."""
    circuit = Circuit.build_default_circuit()
    return {
        "openssl": openssl.get_info(),
        "pq_backend": pq_crypto.backend_name,
        "pq_strategy": pq_crypto.strategy.get_info(),
        "available_strategies": pq_crypto.available_strategies,
        "entropy": entropy_service.get_status(),
        "circuit": relay_service.get_circuit_info(circuit),
        "algorithms": {
            "kem": "ML-KEM-1024",
            "sig": "ML-DSA-87",
            "symmetric": "AES-256-GCM",
            "hybrid": "ML-KEM-1024 + X25519",
        },
        "connected_users": len(chat_service.clients),
    }


class RegisterRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    proof = zka.client_compute_proof(req.password, 0)
    success = zka.register_user(req.username, proof["Y"])
    if not success:
        raise HTTPException(400, "Username already exists")

    # Generate PQ identity keys for this user
    sig_pk, sig_sk = pq_crypto.sig_keygen()
    hybrid_keys = pq_crypto.hybrid_keygen()

    return {
        "success": True,
        "username": req.username,
        "pq_fingerprint": pq_crypto.fingerprint(hybrid_keys["pq_public_key"]),
        "sig_public_key": base64.b64encode(sig_pk).decode(),
        "pq_public_key": base64.b64encode(hybrid_keys["pq_public_key"]).decode(),
    }


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    session_token = zka.generate_session_token()
    proof = zka.client_compute_proof(req.password, session_token)

    # For demo: auto-register if not exists
    if not zka._lookup_public_key(req.username):
        zka.register_user(req.username, proof["Y"])

    verified = zka.server_verify_proof(
        req.username, proof["c"], proof["z"], session_token
    )

    if not verified:
        raise HTTPException(401, "Authentication failed")

    hybrid_keys = pq_crypto.hybrid_keygen()
    token = secrets.token_urlsafe(32)

    return {
        "success": True,
        "token": token,
        "username": req.username,
        "pq_fingerprint": pq_crypto.fingerprint(hybrid_keys["pq_public_key"]),
        "pq_public_key": base64.b64encode(hybrid_keys["pq_public_key"]).decode(),
    }


@app.get("/api/circuit/new")
async def new_circuit():
    circuit = relay_service.build_circuit(3)
    return relay_service.get_circuit_info(circuit)


# ── WebSocket Chat ──

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()

    client = await chat_service.connect(websocket, username)

    # Send initial state
    circuit_info = relay_service.get_circuit_info(client.circuit)
    contacts = await chat_service.get_contact_list(username)
    pq_fp = pq_crypto.fingerprint(client.pq_keys["pq_public_key"])

    await websocket.send_json({
        "type": "init",
        "data": {
            "username": username,
            "pq_fingerprint": pq_fp,
            "pq_public_key": base64.b64encode(
                client.pq_keys["pq_public_key"]
            ).decode(),
            "sig_public_key": base64.b64encode(client.sig_keys[0]).decode(),
            "circuit": circuit_info,
            "contacts": contacts,
            "entropy": entropy_service.get_status(),
            "openssl": openssl.get_info(),
            "algorithms": {
                "kem": "ML-KEM-1024",
                "sig": "ML-DSA-87",
                "symmetric": "AES-256-GCM",
                "forward_secrecy": True,
            },
        }
    })

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data["type"] == "message":
                await chat_service.send_message(
                    sender=username,
                    recipient=data["data"]["recipient"],
                    content=data["data"]["content"],
                )

            elif data["type"] == "get_contacts":
                contacts = await chat_service.get_contact_list(username)
                await websocket.send_json({
                    "type": "contacts",
                    "data": contacts
                })

            elif data["type"] == "get_thread":
                thread = chat_service.get_thread(
                    username, data["data"]["contact"]
                )
                await websocket.send_json({
                    "type": "thread",
                    "data": {
                        "contact": data["data"]["contact"],
                        "messages": thread,
                    }
                })

            elif data["type"] == "new_circuit":
                client.circuit = relay_service.build_circuit(3)
                await websocket.send_json({
                    "type": "circuit",
                    "data": relay_service.get_circuit_info(client.circuit)
                })

    except WebSocketDisconnect:
        await chat_service.disconnect(username)
    except Exception as e:
        print(f"[RiddlerChat] WebSocket error for {username}: {e}")
        await chat_service.disconnect(username)


if __name__ == "__main__":
    import uvicorn
    from backend.config import HOST, WS_PORT
    uvicorn.run(app, host=HOST, port=WS_PORT)
