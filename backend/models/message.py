"""Message model for RiddlerChat."""

from pydantic import BaseModel
from typing import Optional
import time


class Message(BaseModel):
    id: Optional[str] = None
    sender: str
    recipient: str
    content: str  # plaintext (pre-encryption) or display text
    ciphertext: Optional[str] = None  # base64 encrypted content
    timestamp: float = 0.0
    sealed: bool = False  # end-to-end encrypted
    signature: Optional[str] = None  # ML-DSA-87 signature (base64)
    circuit_id: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp == 0.0:
            self.timestamp = time.time()
