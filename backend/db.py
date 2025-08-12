# backend/db.py (sync, dùng psycopg2-binary)
import os
import socket
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# IPv4-only patch (tránh sự cố DNS/IPv6 trên host free)
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only(*args, **kwargs):
    res = _orig_getaddrinfo(*args, **kwargs)
    return [r for r in res if r[0] == socket.AF_INET] or res
socket.getaddrinfo = _ipv4_only

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Missing DATABASE_URL")

# Kết nối sync với psycopg2
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
