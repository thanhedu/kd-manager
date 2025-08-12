import os
import re
import json
from typing import Dict, Any, Tuple, Optional, List

import gspread
from datetime import datetime, timezone
from zoneinfo import ZoneInfo  # có sẵn từ Python 3.9+

# ====== ENV ======
_SHEET_NAME = os.environ.get("GOOGLE_SHEETS_NAME", "Accounts")  # khuyên dùng ID spreadsheet
_GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS_JSON")
_COLUMNS_RAW = (os.environ.get("GOOGLE_SHEETS_COLUMNS", "") or "").strip()

# múi giờ & định dạng thời gian khi ghi ra Google Sheet
_SHEETS_TZ = os.environ.get("GOOGLE_SHEETS_TZ", "Asia/Ho_Chi_Minh")
_SHEETS_TIME_FMT = os.environ.get("GOOGLE_SHEETS_TIME_FORMAT", "%Y-%m-%d %H:%M:%S")

# cache client
_client_cache: Optional[Dict[str, Any]] = None


def _looks_like_sheet_id(s: str) -> bool:
    # Spreadsheet ID: [A-Za-z0-9_-], thường dài > 30
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{30,}", s or ""))


def _get_client() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Khởi tạo gspread client + lấy worksheet đầu tiên (sheet1)."""
    global _client_cache
    if _client_cache:
        return _client_cache, None
    if not _GOOGLE_CREDENTIALS:
        return None, "MISSING_GOOGLE_CREDENTIALS_JSON"

    try:
        creds = json.loads(_GOOGLE_CREDENTIALS)
        sa_email = creds.get("client_email", "")
        gc = gspread.service_account_from_dict(creds)

        # Mở bằng ID trước (khỏi cần Drive API). Nếu không phải ID thì mở theo TITLE.
        sh = None
        if _looks_like_sheet_id(_SHEET_NAME):
            try:
                sh = gc.open_by_key(_SHEET_NAME)
            except Exception:
                sh = None
        if sh is None:
            try:
                sh = gc.open(_SHEET_NAME)
            except gspread.SpreadsheetNotFound:
                return None, f"SPREADSHEET_NOT_FOUND name_or_id='{_SHEET_NAME}'"

        ws = sh.sheet1  # tab đầu tiên
        _client_cache = {"gc": gc, "sh": sh, "ws": ws, "sa_email": sa_email}
        return _client_cache, None
    except Exception as e:
        return None, f"INIT_ERROR: {e.__class__.__name__}: {e}"


def _parse_columns() -> List[Tuple[str, str]]:
    """
    Trả về list (key, header).
    - Nếu không cấu hình GOOGLE_SHEETS_COLUMNS -> dùng 8 cột mặc định.
    - key lấy từ payload: field đặc biệt (id/ciphertext/nonce/salt/title/tags/created_at/updated_at)
      + các key trong payload['meta'].
    Ví dụ cấu hình:
      platform|Ten_nen_tang, url|Link_web, ..., updated_at|Ngay_cap_nhat
    """
    if not _COLUMNS_RAW:
        return [
            ("id", "id"),
            ("ciphertext", "ciphertext"),
            ("nonce", "nonce"),
            ("salt", "salt"),
            ("title", "title"),
            ("tags", "tags"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
        ]
    cols: List[Tuple[str, str]] = []
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


def _excel_col_letter(n: int) -> str:
    """Đổi số cột -> chữ cái cột (A..Z, AA..). Đủ an toàn cho vài chục cột."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _ensure_header(ws, columns: List[Tuple[str, str]]):
    try:
        first_row = ws.row_values(1)
    except Exception:
        first_row = []
    desired = [h for _, h in columns]
    if first_row != desired:
        end_col = _excel_col_letter(len(desired))
        if len(first_row) == 0:
            ws.update("A1", [desired])
        else:
            ws.update(f"A1:{end_col}1", [desired])


def _to_local_str(value) -> str:
    """
    Nhận datetime hoặc chuỗi ISO (có thể có 'Z' / thiếu tzinfo).
    Nếu thiếu tz -> coi là UTC. Trả về chuỗi theo TZ & format đã cấu hình.
    """
    if not value:
        return ""
    try:
        if isinstance(value, str):
            s = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
        else:
            dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local = dt.astimezone(ZoneInfo(_SHEETS_TZ))
        return local.strftime(_SHEETS_TIME_FMT)
    except Exception:
        return str(value)


def append_encrypted_row(row: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Ghi 1 dòng vào sheet theo cấu hình cột.
    row gồm các field đặc biệt + meta (dict) cho các cột tuỳ biến.
    """
    ctx, err = _get_client()
    if err:
        return False, err

    columns = _parse_columns()
    _ensure_header(ctx["ws"], columns)

    # build source
    source: Dict[str, Any] = {
        "id": row.get("id", ""),
        "ciphertext": row.get("ciphertext", ""),
        "nonce": row.get("nonce", ""),
        "salt": row.get("salt", ""),
        "title": row.get("title", ""),
        "tags": row.get("tags", ""),
        "created_at": _to_local_str(row.get("created_at")),
        "updated_at": _to_local_str(row.get("updated_at")),
    }
    meta = row.get("meta") or {}
    if isinstance(meta, dict):
        source.update(meta)

    values = [str(source.get(key, "")) for key, _ in columns]

    try:
        ctx["ws"].append_row(values, value_input_option="RAW")
        return True, None
    except Exception as e:
        return False, f"APPEND_ERROR: {e.__class__.__name__}: {e}"


# ====== DEBUG HELPERS ======
def debug_sheets() -> Dict[str, Any]:
    info = {
        "sheet_name": _SHEET_NAME,
        "has_credentials": bool(_GOOGLE_CREDENTIALS),
        "tz": _SHEETS_TZ,
        "time_format": _SHEETS_TIME_FMT,
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
        "columns": _parse_columns(),
    })
    return info


def try_append_ping() -> Dict[str, Any]:
    now = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    ok, error = append_encrypted_row({
        "id": "PING",
        "ciphertext": "PING",
        "nonce": "PING",
        "salt": "PING",
        "title": "ping",
        "tags": "debug",
        "created_at": now,
        "updated_at": now,
        "meta": {"platform": "test"},
    })
    return {"ok": ok, "error": error, "sheet_name": _SHEET_NAME}
