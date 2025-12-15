import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List
from config import CREDS_FILE, MASTER_SHEET_ID, HEADERS
from multi_store_fetcher import fetch_all_new_orders
from normalizer import normalize_order


# ==========================
# Google Sheets Helpers
# ==========================
def _gs_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    return gspread.authorize(creds)


def _ensure_headers(worksheet):
    first = worksheet.row_values(1)
    if not first:
        worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")


def _load_existing_ids(ws) -> set:
    """Load ORDER NUMBERs already in master sheet to avoid duplicates."""
    try:
        all_vals = ws.get_all_values()[1:]  # skip headers
        return {r[1] for r in all_vals if len(r) > 1 and r[1]}
    except Exception:
        return set()


# ==========================
# Main Appender
# ==========================
def append_new_orders_to_master() -> int:
    # 1. Fetch from all stores
    orders = fetch_all_new_orders()
    if not orders:
        print("✅ No new orders fetched from stores.")
        return 0

    # 2. Connect to sheet
    client = _gs_client()
    #ws = client.open_by_key(MASTER_SHEET_ID).sheet1
    ws = client.open_by_key(MASTER_SHEET_ID).worksheet("test")

    _ensure_headers(ws)

    # 3. Avoid duplicates
    existing_ids = _load_existing_ids(ws)

    # 4. Normalize → rows
    rows: List[List[str]] = []
    for entry in orders:
        normalized = normalize_order(entry)
        for r in normalized:
            if str(r[1]) not in existing_ids:  # ORDER NUMBER column
                rows.append(r)

    if not rows:
        print("✅ Nothing new to append (all duplicates).")
        return 0

    # ✅ Sort rows by ORDER NUMBER (column index 1)
    def order_number_key(val: List[str]):
        raw = str(val[1]).lstrip("#")
        return int(raw) if raw.isdigit() else raw

    rows.sort(key=order_number_key)

    # 5. Append rows
    ws.append_rows(rows, value_input_option="USER_ENTERED")
    print(f"✅ Added {len(rows)} new rows to Master.")
    return len(rows)


# ==========================
# CLI Execution
# ==========================
if __name__ == "__main__":
    append_new_orders_to_master()
