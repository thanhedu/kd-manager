# backend/main.py
import os
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .db import SessionLocal, engine, Base
from .models import AccountCipher
from .schemas import AccountIn, AccountOut, HealthOut
from .sheets import append_encrypted_row

app = FastAPI(title="Account Vault", version="1.0.0")

# ---------- DB session ----------
async def get_db():
    async with SessionLocal() as session:
        yield session

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ---------- API router (prefix /api) ----------
api = APIRouter(prefix="/api")

@api.get("/debug/db", response_model=HealthOut)
async def debug_db():
    return HealthOut(ok=True)

@api.get("/accounts", response_model=list[AccountOut])
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

@api.post("/accounts", response_model=AccountOut, status_code=201)
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

@api.delete("/accounts/{account_id}", status_code=204)
async def delete_account(account_id: UUID, db: AsyncSession = Depends(get_db)):
    q = delete(AccountCipher).where(AccountCipher.id == account_id)
    await db.execute(q)
    await db.commit()
    return

app.include_router(api)

# ---------- Static frontend (Vite build copied to backend/static) ----------
DIST_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        index_file = os.path.join(DIST_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Not Found")
