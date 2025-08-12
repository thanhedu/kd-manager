from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class AccountIn(BaseModel):
    ciphertext: str
    nonce: str
    salt: str
    title: Optional[str] = None
    tags: Optional[str] = None

class AccountOut(AccountIn):
    id: UUID
    created_at: datetime
    updated_at: datetime

class HealthOut(BaseModel):
    ok: bool = Field(default=True)

