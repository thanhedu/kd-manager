# backend/main.py (sync + debug Sheets)
import os
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from .db import SessionLocal, engine, Base
from .models import AccountCipher
from .schemas import AccountIn, AccountOut, HealthOut
from .sheets import append_encrypted_row, debug_sheets, try_append_ping

app = FastAPI(title="Account Vault", version="1.0.0")

# ---------- DB session ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# ---------- API router (prefix /api) ----------
api = APIRouter(prefix="/api")

@api.get("/debug/db", response_model=HealthOut)
def debug_db():
    return HealthOut(ok=True)

# NEW: debug Sheets (không ghi)
@api.get("/debug/sheets")
def debug_sheets_info():
    return debug_sheets()

# NEW: thử ghi 1 dòng "PING" vào sheet
@api.get("/debug/sheets/ping")
def debug_sheets_ping():
    return try_append_ping()

@api.get("/accounts", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db)):
    res = db.execute(select(AccountCipher).order_by(AccountCipher.created_at.desc())).scalars().all()
    return [
        AccountOut(
            id=r.id, ciphertext=r.ciphertext, nonce=r.nonce, salt=r.salt,
            title=r.title, tags=r.tags, created_at=r.created_at, updated_at=r.updated_at
        )
        for r in res
    ]

@api.post("/accounts", response_model=AccountOut, status_code=201)
def create_account(payload: AccountIn, db: Session = Depends(get_db)):
    item = AccountCipher(
        ciphertext=payload.ciphertext,
        nonce=payload.nonce,
        salt=payload.salt,
        title=payload.title,
        tags=payload.tags,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    # Backup Sheets: kết quả/ lỗi sẽ được kiểm tra qua endpoint debug
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
def delete_account(account_id: UUID, db: Session = Depends(get_db)):
    db.execute(delete(AccountCipher).where(AccountCipher.id == account_id))
    db.commit()
    return

app.include_router(api)

# ---------- Static frontend (Vite build trong backend/static) ----------
DIST_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        index_file = os.path.join(DIST_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Not Found")
