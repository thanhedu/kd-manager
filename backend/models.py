from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .db import Base

class AccountCipher(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Dữ liệu đều là chuỗi base64/utf8 (server không giải mã)
    ciphertext = Column(Text, nullable=False)
    nonce = Column(String(64), nullable=False)
    salt = Column(String(64), nullable=False)

    # metadata không nhạy cảm (có thể rỗng)
    title = Column(String(255), nullable=True)   # ví dụ: "github main"
    tags = Column(String(255), nullable=True)    # ví dụ: "work,devops"

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

