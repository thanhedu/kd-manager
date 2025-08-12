from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class AccountIn(BaseModel):
    ciphertext: str
    nonce: str
    salt: str
    title: Optional[str] = None
    tags: Optional[str] = None
    # các trường tuỳ biến để ghi ra Google Sheet
    meta: Optional[Dict[str, Any]] = None


class AccountOut(BaseModel):
    id: UUID
    ciphertext: str
    nonce: str
    salt: str
    title: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class HealthOut(BaseModel):
    ok: bool
