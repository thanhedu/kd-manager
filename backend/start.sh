#!/usr/bin/env bash
set -e
uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}

