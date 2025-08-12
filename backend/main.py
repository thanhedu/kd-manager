import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from .db import SessionLocal, engine, Base
from .models import AccountCipher
from .schemas import AccountIn, AccountOut, HealthOut
from .sheets import append_encrypted_row

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")

app = FastAPI(title="Account Vault API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db():
    async with SessionLocal() as session:
        yield session

@app.on_event("startup")
async def on_startup():
    # Tạo bảng nếu chưa có (đơn giản, thay alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/debug/db", response_model=HealthOut)
async def debug_db():
    return HealthOut(ok=True)

@app.get("/accounts", response_model=list[AccountOut])
async def list_accounts(db: AsyncSession = Depends(get_db)):
    q = select(AccountCipher).order_by(AccountCipher.created_at.desc())
    res = (await db.execute(q)).scalars().all()
    return [
        AccountOut(
            id=r.id, ciphertext=r.ciphertext, nonce=r.nonce, salt=r.salt,
            title=r.title, tags=r.tags, created_at=r.created_at, updated_at=r.updated_at
        )
        for r in res
    ]

@app.post("/accounts", response_model=AccountOut, status_code=201)
async def create_account(payload: AccountIn, db: AsyncSession = Depends(get_db)):
    item = AccountCipher(
        ciphertext=payload.ciphertext,
        nonce=payload.nonce,
        salt=payload.salt,
        title=payload.title,
        tags=payload.tags,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    # Backup Sheets (best-effort)
    try:
        append_encrypted_row({
            "id": str(item.id),
            "ciphertext": item.ciphertext,
            "nonce": item.nonce,
            "salt": item.salt,
            "title": item.title or "",
            "tags": item.tags or "",
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        })
    except Exception:
        pass
    return AccountOut(
        id=item.id, ciphertext=item.ciphertext, nonce=item.nonce, salt=item.salt,
        title=item.title, tags=item.tags, created_at=item.created_at, updated_at=item.updated_at
    )

@app.put("/accounts/{account_id}", response_model=AccountOut)
async def update_account(account_id: UUID, payload: AccountIn, db: AsyncSession = Depends(get_db)):
    q = select(AccountCipher).where(AccountCipher.id == account_id)
    row = (await db.execute(q)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    row.ciphertext = payload.ciphertext
    row.nonce = payload.nonce
    row.salt = payload.salt
    row.title = payload.title
    row.tags = payload.tags
    await db.commit()
    await db.refresh(row)
    return AccountOut(
        id=row.id, ciphertext=row.ciphertext, nonce=row.nonce, salt=row.salt,
        title=row.title, tags=row.tags, created_at=row.created_at, updated_at=row.updated_at
    )

@app.delete("/accounts/{account_id}", status_code=204)
async def delete_account(account_id: UUID, db: AsyncSession = Depends(get_db)):
    q = delete(AccountCipher).where(AccountCipher.id == account_id)
    await db.execute(q)
    await db.commit()
    return

