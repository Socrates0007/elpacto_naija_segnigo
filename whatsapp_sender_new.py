# whatsapp_sender.py
import os
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List
from config import CREDS_FILE, STATE_DIR, WHATSAPP_DELAY_SECONDS, TWILIO_SID, TWILIO_AUTH, TWILIO_FROM
from personal_sheets import PEOPLE
from twilio.rest import Client

# Twilio client
twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

def _gs_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    return gspread.authorize(creds)

def _sanitize(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip("_")

def _person_tracker_file(name: str) -> str:
    os.makedirs(STATE_DIR, exist_ok=True)
    return os.path.join(STATE_DIR, f"last_sent_row_{_sanitize(name)}.txt")

def _load_last_sent_row(name: str) -> int:
    path = _person_tracker_file(name)
    if not os.path.exists(path):
        return 1
    with open(path, "r") as f:
        s = f.read().strip()
        return int(s) if s.isdigit() else 1

def _save_last_sent_row(name: str, row: int) -> None:
    path = _person_tracker_file(name)
    with open(path, "w") as f:
        f.write(str(row))

def _row_to_message(row: List[str], header: List[str]) -> str:
    # Map actual sheet header → row values
    kv = {header[i].strip(): (row[i] if i < len(row) else "") for i in range(len(header))}

    lines = [
        "New Order Assigned 🛍️",
        f"Order #{kv.get('ORDER NUMBER', 'N/A')}",
        f"Customer: {kv.get('FIRST NAME', '')} {kv.get('LAST NAME', '')}",
        f"Phone: {kv.get('PHONE NUMBER', '')}",
    ]

    # ✅ Address first
    address = kv.get("ADDRESS", "")
    if address.strip():
        lines.append(f"Address: {address}")

    # ✅ Then Location
    lines.append(f"Location: {kv.get('LOCATION', '')}")

    # ✅ Items last
    lines.append("Items:")
    lines.append(f" - {kv.get('PRODUCT', '')} x{kv.get('QUANTITY', '')} @ NGN {kv.get('PRICE', '')}")

    return "\n".join(lines)

def _send_whatsapp(phone: str, message: str):
    try:
        msg = twilio_client.messages.create(
            from_=f"whatsapp:{TWILIO_FROM}",   # your Twilio WhatsApp number
            to=f"whatsapp:{phone}",           # recipient
            body=message
        )
        return msg.sid
    except Exception as e:
        print(f"❌ Twilio send failed: {e}")
        return None

def send_new_personal_rows_via_whatsapp():
    client = _gs_client()
    total_msgs = 0

    for person in PEOPLE:
        name = person["name"]
        phone = person["whatsapp"]
        ws = client.open_by_key(person["sheet_id"]).worksheet("December")

        all_vals = ws.get_all_values()
        if not all_vals:
            continue

        header, data = all_vals[0], all_vals[1:]
        last_sent_abs = _load_last_sent_row(name)
        start_idx = max(0, last_sent_abs - 1)
        new_rows = data[start_idx:]

        if not new_rows:
            print(f"✅ No new rows to WhatsApp for {name}.")
            continue

        for row in new_rows:
            msg = _row_to_message(row, header)
            print(f"📲 Sending WhatsApp to {name} ({phone}) ...")
            sid = _send_whatsapp(phone, msg)
            if sid:
                print(f"✅ Sent to {name}, SID={sid}")
                total_msgs += 1
                time.sleep(WHATSAPP_DELAY_SECONDS)

        new_abs = 1 + len(data)
        _save_last_sent_row(name, new_abs)
        print(f"✅ Updated last_sent_row for {name} -> {new_abs}")

    print(f"📦 Total WhatsApp messages sent: {total_msgs}")
    return total_msgs

if __name__ == "__main__":
    send_new_personal_rows_via_whatsapp()
