-- Bật extension uuid nếu cần
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS accounts (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  ciphertext text NOT NULL,
  nonce varchar(64) NOT NULL,
  salt varchar(64) NOT NULL,
  title varchar(255),
  tags varchar(255),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

