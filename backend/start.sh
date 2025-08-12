#!/usr/bin/env bash
set -e

# Render sẽ đặt biến môi trường PORT (ví dụ 10000).
# Dùng PORT nếu có, mặc định 8000 khi chạy local.
PORT="${PORT:-8000}"

# Chạy uvicorn trỏ đúng module FastAPI
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT"
