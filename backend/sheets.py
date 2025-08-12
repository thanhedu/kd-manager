import os
import json
import gspread
from typing import Dict, Any

_SHEET_NAME = os.environ.get("GOOGLE_SHEETS_NAME", "Accounts")
_GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS_JSON")

_gclient = None
_gsheet = None

def _ensure_client():
    global _gclient, _gsheet
    if _gclient is not None and _gsheet is not None:
        return _gsheet
    if not _GOOGLE_CREDENTIALS:
        # Không cấu hình thì bỏ qua backup, backend vẫn chạy
        return None
    creds_dict = json.loads(_GOOGLE_CREDENTIALS)
    sa = gspread.service_account_from_dict(creds_dict)
    sh = sa.open(_SHEET_NAME)
    _gclient = sa
    _gsheet = sh.sheet1
    return _gsheet

def append_encrypted_row(row: Dict[str, Any]):
    ws = _ensure_client()
    if ws is None:
        return
    # Ghi đúng dữ liệu ciphertext, KHÔNG plaintext
    ws.append_row([
        row.get("id", ""),
        row.get("ciphertext", ""),
        row.get("nonce", ""),
        row.get("salt", ""),
        row.get("title", ""),
        row.get("tags", ""),
        row.get("created_at", ""),
        row.get("updated_at", ""),
    ], value_input_option="RAW")

