'''
import os
import time
import requests
from typing import List, Dict, Any
from config import STORES, STATE_DIR


# ==========================
# Helpers
# ==========================
def _ensure_state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)


def _sanitize_name(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip("_")


def _last_id_path(store_name: str) -> str:
    _ensure_state_dir()
    return os.path.join(STATE_DIR, f"last_order_id_{_sanitize_name(store_name)}.txt")


def _load_last_id(store_name: str) -> int:
    p = _last_id_path(store_name)
    if not os.path.exists(p):
        return 0
    with open(p, "r") as f:
        s = f.read().strip()
        return int(s) if s.isdigit() else 0


def _save_last_id(store_name: str, order_id: int) -> None:
    p = _last_id_path(store_name)
    with open(p, "w") as f:
        f.write(str(order_id))


def _safe_request(session, url, **kwargs):
    """Retry wrapper for requests with 3 attempts."""
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=60, **kwargs)  # 60s timeout
            resp.raise_for_status()
            return resp
        except requests.exceptions.ReadTimeout:
            print(f"⏳ Timeout (attempt {attempt+1}/3) for {url}, retrying...")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Request failed (attempt {attempt+1}/3): {e}")
            time.sleep(5)
    raise Exception(f"❌ Request failed after retries: {url}")


# ==========================
# WooCommerce Fetcher
# ==========================
def _fetch_woo(store: Dict[str, Any], last_id: int) -> List[Dict[str, Any]]:
    base = store["url"].rstrip("/") + "/wp-json/wc/v3/orders"
    auth = (store["consumer_key"], store["consumer_secret"])
    session = requests.Session()

    params = {"per_page": 100, "orderby": "id", "order": "asc",
              "min_id": last_id + 1, "page": 1}
    new_orders = []

    try:
        resp = _safe_request(session, base, auth=auth, params=params)
        if resp.status_code == 400:
            raise RuntimeError("min_id unsupported")
        new_orders.extend(resp.json())

        total_pages = int(resp.headers.get("X-WP-TotalPages", "1"))
        for page in range(2, total_pages + 1):
            params["page"] = page
            r = _safe_request(session, base, auth=auth, params=params)
            new_orders.extend(r.json())
    except Exception:
        # fallback (when min_id not supported)
        params_fb = {"per_page": 100, "orderby": "id", "order": "asc", "page": 1}
        r0 = _safe_request(session, base, auth=auth, params=params_fb)
        new_orders.extend([o for o in r0.json() if o.get("id", 0) > last_id])

        total_pages = int(r0.headers.get("X-WP-TotalPages", "1"))
        for page in range(2, total_pages + 1):
            params_fb["page"] = page
            r = _safe_request(session, base, auth=auth, params=params_fb)
            new_orders.extend([o for o in r.json() if o.get("id", 0) > last_id])

    return [o for o in new_orders if o.get("id", 0) > last_id]


# ==========================
# Shopify Fetcher
# ==========================
def _fetch_shopify(store: Dict[str, Any], last_id: int) -> List[Dict[str, Any]]:
    base = store["url"].rstrip("/") + "/admin/api/2023-10/orders.json"
    headers = {"X-Shopify-Access-Token": store.get("access_token", "")}
    session = requests.Session()
    session.headers.update(headers)

    params = {"limit": 250, "status": "any"}
    if last_id:
        params["since_id"] = last_id

    new_orders = []
    r = _safe_request(session, base, params=params)
    body = r.json()
    items = body.get("orders", [])
    new_orders.extend(items)

    return [o for o in new_orders if o.get("id", 0) > last_id]


# ==========================
# Main Aggregator
# ==========================
def fetch_all_new_orders() -> List[Dict[str, Any]]:
    all_found: List[Dict[str, Any]] = []

    for store in STORES:
        name = store.get("name", "unknown")
        stype = store.get("type", "woo").lower()
        last_id = _load_last_id(name)

        try:
            if stype == "woo":
                orders = _fetch_woo(store, last_id)
            elif stype == "shopify":
                orders = _fetch_shopify(store, last_id)
            else:
                print(f"⚠️ Unknown store type for {name}: {stype}")
                continue

            if not orders:
                print(f"➡️ {name}: no new orders (last_id={last_id})")
                continue

            max_id = max(o.get("id", 0) for o in orders)
            _save_last_id(name, max_id)

            for o in orders:
                all_found.append({
                    "source_name": name,
                    "platform": stype,
                    "order": o
                })

            print(f"✅ {name}: fetched {len(orders)} new orders (saved last_id={max_id})")
        except Exception as e:
            print(f"❌ Failed fetching {name}: {e}")

    return all_found


# ==========================
# CLI Execution
# ==========================
if __name__ == "__main__":
    orders = fetch_all_new_orders()
    print(f"Total fetched across stores: {len(orders)}")
'''
import os
import time
import requests
from typing import List, Dict, Any
from config import STORES, STATE_DIR


# ==========================
# Helpers
# ==========================
def _ensure_state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)


def _sanitize_name(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip("_")


def _last_id_path(store_name: str) -> str:
    _ensure_state_dir()
    return os.path.join(STATE_DIR, f"last_order_id_{_sanitize_name(store_name)}.txt")


def _load_last_id(store_name: str) -> int:
    p = _last_id_path(store_name)
    if not os.path.exists(p):
        return 0
    with open(p, "r") as f:
        s = f.read().strip()
        return int(s) if s.isdigit() else 0


def _save_last_id(store_name: str, order_id: int) -> None:
    p = _last_id_path(store_name)
    with open(p, "w") as f:
        f.write(str(order_id))


def _safe_request(session, url, **kwargs):
    """Retry wrapper for requests with 3 attempts."""
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=60, **kwargs)  # 60s timeout
            resp.raise_for_status()
            return resp
        except requests.exceptions.ReadTimeout:
            print(f"⏳ Timeout (attempt {attempt+1}/3) for {url}, retrying...")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Request failed (attempt {attempt+1}/3): {e}")
            time.sleep(5)
    raise Exception(f"❌ Request failed after retries: {url}")


# ==========================
# WooCommerce Fetcher
# ==========================
def _fetch_woo(store: Dict[str, Any], last_id: int) -> List[Dict[str, Any]]:
    base = store["url"].rstrip("/") + "/wp-json/wc/v3/orders"
    auth = (store["consumer_key"], store["consumer_secret"])
    session = requests.Session()

    params = {"per_page": 100, "orderby": "id", "order": "asc",
              "min_id": last_id + 1, "page": 1}
    new_orders = []

    try:
        resp = _safe_request(session, base, auth=auth, params=params)
        if resp.status_code == 400:
            raise RuntimeError("min_id unsupported")
        new_orders.extend(resp.json())

        total_pages = int(resp.headers.get("X-WP-TotalPages", "1"))
        for page in range(2, total_pages + 1):
            params["page"] = page
            r = _safe_request(session, base, auth=auth, params=params)
            new_orders.extend(r.json())
    except Exception:
        # fallback (when min_id not supported)
        params_fb = {"per_page": 100, "orderby": "id", "order": "asc", "page": 1}
        r0 = _safe_request(session, base, auth=auth, params=params_fb)
        new_orders.extend([o for o in r0.json() if o.get("id", 0) > last_id])

        total_pages = int(r0.headers.get("X-WP-TotalPages", "1"))
        for page in range(2, total_pages + 1):
            params_fb["page"] = page
            r = _safe_request(session, base, auth=auth, params=params_fb)
            new_orders.extend([o for o in r.json() if o.get("id", 0) > last_id])

    return [o for o in new_orders if o.get("id", 0) > last_id]


# ==========================
# Shopify Fetcher (Fixed)
'''# ==========================
def _fetch_shopify(store: Dict[str, Any], last_id: int) -> List[Dict[str, Any]]:
    base = store["url"].rstrip("/") + "/admin/api/2023-10/orders.json"
    headers = {"X-Shopify-Access-Token": store.get("access_token", "")}
    session = requests.Session()
    session.headers.update(headers)

    params = {
        "limit": 250,
        "status": "any",
        "order": "created_at asc"  # 👈 oldest first
    }
    if last_id:
        params["since_id"] = last_id

    new_orders = []
    url = base

    while url:
        resp = _safe_request(session, url, params=params)
        body = resp.json()
        items = body.get("orders", [])
        new_orders.extend(items)

        # Shopify pagination via `Link` header
        link = resp.headers.get("Link") or resp.headers.get("link")
        if link and 'rel="next"' in link:
            # Extract the "next" page URL from link header
            url = link.split(";")[0].strip(" <>")
            params = {}  # next page URL already contains params
        else:
            url = None

    # Only return orders newer than last_id
    return [o for o in new_orders if o.get("id", 0) > last_id]

'''
# ==========================
# Main Aggregator
# ==========================
def fetch_all_new_orders() -> List[Dict[str, Any]]:
    all_found: List[Dict[str, Any]] = []

    for store in STORES:
        name = store.get("name", "unknown")
        stype = store.get("type", "woo").lower()
        last_id = _load_last_id(name)

        try:
            if stype == "woo":
                orders = _fetch_woo(store, last_id)
            elif stype == "shopify":
                orders = _fetch_shopify(store, last_id)
            else:
                print(f"⚠️ Unknown store type for {name}: {stype}")
                continue

            if not orders:
                print(f"➡️ {name}: no new orders (last_id={last_id})")
                continue

            max_id = max(o.get("id", 0) for o in orders)
            _save_last_id(name, max_id)

            for o in orders:
                all_found.append({
                    "source_name": name,
                    "platform": stype,
                    "order": o
                })

            print(f"✅ {name}: fetched {len(orders)} new orders (saved last_id={max_id})")
        except Exception as e:
            print(f"❌ Failed fetching {name}: {e}")

    return all_found
'''
# ==========================
# Shopify Fetcher (Fixed + Notes Support)
# ==========================
def _fetch_shopify(store: Dict[str, Any], last_id: int) -> List[Dict[str, Any]]:
    base = store["url"].rstrip("/") + "/admin/api/2023-10/orders.json"
    headers = {"X-Shopify-Access-Token": store.get("access_token", "")}
    session = requests.Session()
    session.headers.update(headers)

    params = {
        "limit": 250,
        "status": "any",
        "order": "created_at asc"  # oldest first
    }
    if last_id:
        params["since_id"] = last_id

    new_orders = []
    url = base

    while url:
        resp = _safe_request(session, url, params=params)
        body = resp.json()
        orders = body.get("orders", [])

        # ✅ stop if nothing new
        if not orders:
            break

        # Only keep orders newer than last_id
        fresh = [o for o in orders if o.get("id", 0) > last_id]
        if not fresh:
            break

        for o in fresh:
            # 👇 Extract Notes Attributes (special fields)
            notes = o.get("note_attributes", [])
            if notes:
                o["_parsed_notes"] = {n.get("name"): n.get("value") for n in notes}

            new_orders.append(o)

        # Shopify pagination via Link header
        link = resp.headers.get("Link") or resp.headers.get("link")
        if link and 'rel="next"' in link:
            url = link.split(";")[0].strip(" <>")
            params = {}  # next page URL already includes params
        else:
            url = None

    return new_orders

'''
def _fetch_shopify(store: Dict[str, Any], last_id: int) -> List[Dict[str, Any]]:
    base = store["url"].rstrip("/") + "/admin/api/2023-10/orders.json"
    headers = {"X-Shopify-Access-Token": store.get("access_token", "")}
    session = requests.Session()
    session.headers.update(headers)

    params = {
        "limit": 250,
        "status": "any" # 👈 most recent first
    }
    if last_id:
        params["since_id"] = last_id

    new_orders = []
    url = base

    for _ in range(2):  # fetch only 2 pages = 500 max
        if not url:
            break
        resp = _safe_request(session, url, params=params)
        body = resp.json()
        items = body.get("orders", [])
        new_orders.extend(items)

        # Pagination check
        link = resp.headers.get("Link") or resp.headers.get("link")
        if link and 'rel="next"' in link and len(new_orders) < 500:
            url = link.split(";")[0].strip(" <>")
            params = {}  # next URL already contains params
        else:
            url = None

    # Only orders newer than last_id
    filtered = [o for o in new_orders if o.get("id", 0) > last_id]

    # Reverse to oldest → newest before returning
    return list(reversed(filtered))

# ==========================
# CLI Execution
# ==========================
if __name__ == "__main__":
    orders = fetch_all_new_orders()
    print(f"Total fetched across stores: {len(orders)}")
