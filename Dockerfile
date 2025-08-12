# ---------- Stage 1: build frontend ----------
FROM node:20-alpine AS fe
WORKDIR /app/frontend
COPY frontend/package.json ./
# Nếu có package-lock.json thì copy luôn (không bắt buộc)
COPY frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

# ---------- Stage 2: backend runtime ----------
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# psycopg2 deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# install python deps
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# copy backend
COPY backend/ backend/

# copy built frontend into backend/static
RUN mkdir -p backend/static
COPY --from=fe /app/frontend/dist/ backend/static/

EXPOSE 8000
CMD ["bash", "backend/start.sh"]
