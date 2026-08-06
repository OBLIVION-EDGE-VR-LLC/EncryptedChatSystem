"""User model for RiddlerChat."""

from pydantic import BaseModel
from typing import Optional
import base64


class User(BaseModel):
    username: str
    alias: Optional[str] = None
    pq_fingerprint: Optional[str] = None
    pq_public_key: Optional[str] = None  # base64
    x25519_public_key: Optional[str] = None  # base64
    sig_public_key: Optional[str] = None  # base64
    online: bool = False
    pq_verified: bool = False

    def display_name(self) -> str:
        return self.alias or self.username
