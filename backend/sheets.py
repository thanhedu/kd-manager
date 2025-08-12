# backend/sheets.py
import os, re, json
from typing import Dict, Any, Tuple, Optional, List
import gspread

_SHEET_NAME = os.environ.get("GOOGLE_SHEETS_NAME", "Accounts")
_GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS_JSON")
_COLUMNS_RAW = (os.environ.get("GOOGLE_SHEETS_COLUMNS", "") or "").strip()

_client_cache: Optional[Dict[str, Any]] = None

def _looks_like_sheet_id(s: str) -> bool:
    # Spreadsheet ID: [A-Za-z0-9_-], thường dài > 30
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{30,}", s or ""))

def _get_client() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    global _client_cache
    if _client_cache:
        return _client_cache, None
    if not _GOOGLE_CREDENTIALS:
        return None, "MISSING_GOOGLE_CREDENTIALS_JSON"

    try:
        creds = json.loads(_GOOGLE_CREDENTIALS)
        sa_email = creds.get("client_email", "")
        gc = gspread.service_account_from_dict(creds)

        sh = None
        # Ưu tiên mở bằng ID (khỏi cần Drive API)
        if _looks_like_sheet_id(_SHEET_NAME):
            try:
                sh = gc.open_by_key(_SHEET_NAME)
            except Exception:
                sh = None
        if sh is None:
            try:
                sh = gc.open(_SHEET_NAME)  # mở theo TITLE (cần Drive API)
            except gspread.SpreadsheetNotFound:
                return None, f"SPREADSHEET_NOT_FOUND name_or_id='{_SHEET_NAME}'"

        ws = sh.sheet1   # tab đầu tiên
        _client_cache = {"gc": gc, "sh": sh, "ws": ws, "sa_email": sa_email}
        return _client_cache, None
    except Exception as e:
        return None, f"INIT_ERROR: {e.__class__.__name__}: {e}"

def _parse_columns() -> List[Tuple[str, str]]:
    """
    Trả về list (key, header). Nếu không cấu hình -> 8 cột mặc định.
    key lấy từ payload: các field đặc biệt (id/ciphertext/nonce/...) + meta[key]
    """
    if not _COLUMNS_RAW:
        return [
            ("id","id"),
            ("ciphertext","ciphertext"),
            ("nonce","nonce"),
            ("salt","salt"),
            ("title","title"),
            ("tags","tags"),
            ("created_at","created_at"),
            ("updated_at","updated_at"),
        ]
    cols: List[Tuple[str,str]] = []
    for part in _COLUMNS_RAW.split(","):
        part = part.strip()
        if not part:
            continue
        if "|" in part:
            key, header = [x.strip() for x in part.split("|", 1)]
        else:
            key, header = part, part
        cols.append((key, header))
    return cols

def _ensure_header(ws, columns: List[Tuple[str,str]]):
    try:
        first_row = ws.row_values(1)
    except Exception:
        first_row = []
    desired = [h for _, h in columns]
    if first_row != desired:
        # chỉ 1–26 cột: đủ cho case hiện tại (17 cột -> A..Q)
        end_col = chr(64 + len(desired))  # A=65
        if len(first_row) == 0:
            ws.update("A1", [desired])
        else:
            ws.update(f"A1:{end_col}1", [desired])

def append_encrypted_row(row: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    ctx, err = _get_client()
    if err:
        return False, err

    columns = _parse_columns()
    _ensure_header(ctx["ws"], columns)

    source = {
        "id": row.get("id",""),
        "ciphertext": row.get("ciphertext",""),
        "nonce": row.get("nonce",""),
        "salt": row.get("salt",""),
        "title": row.get("title",""),
        "tags": row.get("tags",""),
        "created_at": row.get("created_at",""),
        "updated_at": row.get("updated_at",""),
    }
    meta = row.get("meta") or {}
    if isinstance(meta, dict):
        source.update(meta)

    values = [str(source.get(key,"")) for key,_ in columns]
    try:
        ctx["ws"].append_row(values, value_input_option="RAW")
        return True, None
    except Exception as e:
        return False, f"APPEND_ERROR: {e.__class__.__name__}: {e}"

def debug_sheets() -> Dict[str, Any]:
    info = {"sheet_name": _SHEET_NAME, "has_credentials": bool(_GOOGLE_CREDENTIALS)}
    ctx, err = _get_client()
    if err:
        info.update({"ok": False, "error": err})
        return info
    info.update({
        "ok": True,
        "sa_email": ctx["sa_email"],
        "worksheet_title": ctx["ws"].title,
        "spreadsheet_id": ctx["sh"].id,
        "columns": _parse_columns(),
    })
    return info

def try_append_ping() -> Dict[str, Any]:
    ok, error = append_encrypted_row({
        "id":"PING","ciphertext":"PING","nonce":"PING","salt":"PING",
        "title":"ping","tags":"debug",
        "created_at":"","updated_at":"",
        "meta":{"platform":"test"}
    })
    return {"ok": ok, "error": error, "sheet_name": _SHEET_NAME}
