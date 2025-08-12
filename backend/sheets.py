import os
import json
from typing import Dict, Any, Tuple, Optional
import gspread

_SHEET_NAME = os.environ.get("GOOGLE_SHEETS_NAME", "Accounts")
_GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS_JSON")

_client_cache = None  # type: Optional[Dict[str, Any]]

def _get_client() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Khởi tạo client và mở sheet. Trả về (ctx, error). ctx = {gc, sh, ws, sa_email}."""
    global _client_cache
    if _client_cache:
        return _client_cache, None

    if not _GOOGLE_CREDENTIALS:
        return None, "MISSING_GOOGLE_CREDENTIALS_JSON"

    try:
        creds = json.loads(_GOOGLE_CREDENTIALS)
        sa_email = creds.get("client_email", "")
        gc = gspread.service_account_from_dict(creds)
        try:
            sh = gc.open(_SHEET_NAME)  # mở theo TÊN spreadsheet (title)
        except gspread.SpreadsheetNotFound:
            return None, f"SPREADSHEET_NOT_FOUND name='{_SHEET_NAME}'"
        ws = sh.sheet1  # worksheet đầu tiên
        _client_cache = {"gc": gc, "sh": sh, "ws": ws, "sa_email": sa_email}
        return _client_cache, None
    except Exception as e:
        return None, f"INIT_ERROR: {e.__class__.__name__}: {e}"

def append_encrypted_row(row: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Ghi 1 dòng. Trả về (ok, error)."""
    ctx, err = _get_client()
    if err:
        return False, err
    try:
        ctx["ws"].append_row([
            row.get("id", ""),
            row.get("ciphertext", ""),
            row.get("nonce", ""),
            row.get("salt", ""),
            row.get("title", ""),
            row.get("tags", ""),
            row.get("created_at", ""),
            row.get("updated_at", ""),
        ], value_input_option="RAW")
        return True, None
    except Exception as e:
        return False, f"APPEND_ERROR: {e.__class__.__name__}: {e}"

def debug_sheets() -> Dict[str, Any]:
    """Trả về thông tin chẩn đoán (không ghi)."""
    info = {
        "sheet_name": _SHEET_NAME,
        "has_credentials": bool(_GOOGLE_CREDENTIALS),
    }
    ctx, err = _get_client()
    if err:
        info.update({"ok": False, "error": err})
        return info
    info.update({
        "ok": True,
        "sa_email": ctx["sa_email"],
        "worksheet_title": ctx["ws"].title,
        "spreadsheet_id": ctx["sh"].id,
    })
    return info

def try_append_ping() -> Dict[str, Any]:
    """Thử ghi 1 dòng 'PING' để test quyền."""
    ok, error = append_encrypted_row({
        "id": "PING",
        "ciphertext": "PING",
        "nonce": "PING",
        "salt": "PING",
        "title": "ping",
        "tags": "debug",
        "created_at": "",
        "updated_at": "",
    })
    return {"ok": ok, "error": error, "sheet_name": _SHEET_NAME}
