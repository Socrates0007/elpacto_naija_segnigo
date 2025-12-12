'''# order_distributor.py
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import CREDS_FILE, MASTER_SHEET_ID, HEADERS, STATE_DIR
from personal_sheets import PEOPLE

TRACK_FILE = os.path.join(STATE_DIR, "last_distributed_row.txt")


def _ensure_state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)


def _load_last_distributed_row() -> int:
    _ensure_state_dir()
    if not os.path.exists(TRACK_FILE):
        return 1
    with open(TRACK_FILE, "r") as f:
        s = f.read().strip()
        return int(s) if s.isdigit() else 1


def _save_last_distributed_row(n: int) -> None:
    _ensure_state_dir()
    with open(TRACK_FILE, "w") as f:
        f.write(str(n))


def _gs_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    return gspread.authorize(creds)


def _ensure_headers(ws):
    current_headers = ws.row_values(1)
    if not current_headers:
        ws.append_row(HEADERS, value_input_option="USER_ENTERED")
    elif current_headers != HEADERS:
        ws.update("1:1", [HEADERS])  # overwrite with correct headers


def manual_split(client, master, data, total_rows, person_sheets):
    while True:
        try:
            start = int(input("Enter start row (relative to data, not including header): "))
            end = int(input("Enter end row: "))

            if start < 1 or end > total_rows or start > end:
                print("❌ Invalid range. Try again.")
                continue

            print("Available agents: ", [p["name"] for p in PEOPLE])
            agent_name = input("Assign to which agent? ").strip()

            if agent_name not in person_sheets:
                print("❌ Invalid agent. Try again.")
                continue

            ws = person_sheets[agent_name]

            rows_raw = data[start - 1:end]
            rows_to_assign = []
            for r in rows_raw:
                r = r + [""] * (len(HEADERS) - len(r))  # pad properly
                rows_to_assign.append(r)

            ws.append_rows(rows_to_assign, value_input_option="USER_ENTERED")

            # mark agent in Master (col M)
            update_range = f"M{start+1}:M{end+1}"
            master.update(update_range, [[agent_name]] * (end - start + 1))

            print(f"✅ Assigned rows {start} → {end} to {agent_name} and marked in Master.")

            _save_last_distributed_row(end)

            cont = input("Do you want to continue? (y/n): ").lower()
            if cont != "y":
                print("✅ Finished manual distribution.")
                break

        except Exception as e:
            print("⚠️ Error:", e)
            break


def auto_split(client, master, data, last_idx, total_rows, person_sheets):
    new_rows = data[last_idx:]
    if not new_rows:
        print("✅ No new rows to distribute.")
        return

    people = [p["name"] for p in PEOPLE]
    num_agents = len(people)

    for i, row in enumerate(new_rows, start=last_idx + 1):
        agent = people[(i - 1) % num_agents]  # round-robin
        ws = person_sheets[agent]

        row = row + [""] * (len(HEADERS) - len(row))
        ws.append_row(row, value_input_option="USER_ENTERED")

        # mark agent in Master
        master.update(f"M{i+1}", [[agent]])  # +1 for header

        print(f"✅ Row {i} assigned to {agent}")

    _save_last_distributed_row(total_rows)
    print("✅ Auto distribution complete.")


def main():
    client = _gs_client()
    master = client.open_by_key(MASTER_SHEET_ID).sheet1

    all_vals = master.get_all_values()
    if not all_vals:
        print("Master is empty.")
        return

    header, data = all_vals[0], all_vals[1:]
    last_idx = _load_last_distributed_row()
    total_rows = len(data)

    print(f"Master sheet has {total_rows} rows (excluding header).")
    print(f"Last distributed row: {last_idx}")

    person_sheets = {}
    for person in PEOPLE:
        ws = client.open_by_key(person["sheet_id"]).sheet1
        _ensure_headers(ws)
        person_sheets[person["name"]] = ws

    mode = input("Choose mode: (m)anual or (a)uto? ").strip().lower()
    if mode == "m":
        manual_split(client, master, data, total_rows, person_sheets)
    elif mode == "a":
        auto_split(client, master, data, last_idx, total_rows, person_sheets)
    else:
        print("❌ Invalid mode.")


if __name__ == "__main__":
    main()
'''
# order_distributor.py
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import CREDS_FILE, MASTER_SHEET_ID, HEADERS, STATE_DIR
from personal_sheets import PEOPLE

TRACK_FILE = os.path.join(STATE_DIR, "last_distributed_row.txt")


def _ensure_state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)


def _load_last_distributed_row() -> int:
    _ensure_state_dir()
    if not os.path.exists(TRACK_FILE):
        return 1
    with open(TRACK_FILE, "r") as f:
        s = f.read().strip()
        return int(s) if s.isdigit() else 1


def _save_last_distributed_row(n: int) -> None:
    _ensure_state_dir()
    with open(TRACK_FILE, "w") as f:
        f.write(str(n))


def _gs_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    return gspread.authorize(creds)


def _ensure_headers(ws):
    current_headers = ws.row_values(1)
    if not current_headers:
        ws.append_row(HEADERS, value_input_option="USER_ENTERED")
    elif current_headers != HEADERS:
        ws.update("1:1", [HEADERS])  # overwrite with correct headers


def _agent_col_index() -> int:
    """Find the 1-based column index for 'agent in charge' in HEADERS."""
    if "agent in charge" in HEADERS:
        return HEADERS.index("agent in charge") + 1
    raise ValueError("'agent in charge' column not found in HEADERS")


def manual_split(client, master, data, total_rows, person_sheets):
    agent_col = _agent_col_index()

    while True:
        try:
            start = int(input("Enter start row (relative to data, not including header): "))
            end = int(input("Enter end row: "))

            if start < 1 or end > total_rows or start > end:
                print("❌ Invalid range. Try again.")
                continue

            print("Available agents: ", [p["name"] for p in PEOPLE])
            agent_name = input("Assign to which agent? ").strip()

            if agent_name not in person_sheets:
                print("❌ Invalid agent. Try again.")
                continue

            ws = person_sheets[agent_name]

            rows_raw = data[start - 1:end]
            rows_to_assign = []
            for r in rows_raw:
                r = r + [""] * (len(HEADERS) - len(r))  # pad properly
                rows_to_assign.append(r)

            ws.append_rows(rows_to_assign, value_input_option="USER_ENTERED")

            # mark agent in Master
            for row_num in range(start, end + 1):
                master.update_cell(row_num + 1, agent_col, agent_name)

            print(f"✅ Assigned rows {start} → {end} to {agent_name} and marked in Master.")

            _save_last_distributed_row(end)

            cont = input("Do you want to continue? (y/n): ").lower()
            if cont != "y":
                print("✅ Finished manual distribution.")
                break

        except Exception as e:
            print("⚠️ Error:", e)
            break


def auto_split(client, master, data, last_idx, total_rows, person_sheets):
    new_rows = data[last_idx:]
    if not new_rows:
        print("✅ No new rows to distribute.")
        return

    people = [p["name"] for p in PEOPLE]
    num_agents = len(people)
    agent_col = _agent_col_index()

    for i, row in enumerate(new_rows, start=last_idx + 1):
        agent = people[(i - 1) % num_agents]  # round-robin
        ws = person_sheets[agent]

        row = row + [""] * (len(HEADERS) - len(row))
        ws.append_row(row, value_input_option="USER_ENTERED")

        # mark agent in Master
        master.update_cell(i + 1, agent_col, agent)  # +1 for header row

        print(f"✅ Row {i} assigned to {agent}")

    _save_last_distributed_row(total_rows)
    print("✅ Auto distribution complete.")


def main():
    client = _gs_client()
    master = client.open_by_key(MASTER_SHEET_ID).sheet1

    all_vals = master.get_all_values()
    if not all_vals:
        print("Master is empty.")
        return

    header, data = all_vals[0], all_vals[1:]
    last_idx = _load_last_distributed_row()
    total_rows = len(data)

    print(f"Master sheet has {total_rows} rows (excluding header).")
    print(f"Last distributed row: {last_idx}")

    person_sheets = {}
    for person in PEOPLE:
        ws = client.open_by_key(person["sheet_id"]).worksheets()[1]
        _ensure_headers(ws)
        person_sheets[person["name"]] = ws

    mode = input("Choose mode: (m)anual or (a)uto? ").strip().lower()
    if mode == "m":
        manual_split(client, master, data, total_rows, person_sheets)
    elif mode == "a":
        auto_split(client, master, data, last_idx, total_rows, person_sheets)
    else:
        print("❌ Invalid mode.")


if __name__ == "__main__":
    main()
