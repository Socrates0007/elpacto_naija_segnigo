'''from typing import Dict, Any, List
from datetime import datetime
from config import HEADERS


def _safe_get(d: Dict, keys: List[str], default=""):
    """Nested get with default fallback."""
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d


def normalize_woo(order: Dict[str, Any], source_name: str) -> List[List[str]]:
    """Convert WooCommerce order JSON → list of rows for Google Sheets."""
    rows = []
    order_id = order.get("id")
    created_at = order.get("date_created", "")[:10]

    billing = order.get("billing", {})
    first_name = billing.get("first_name", "")
    last_name = billing.get("last_name", "")
    phone = billing.get("phone", "")
    address = ", ".join(filter(None, [
        billing.get("address_1", ""), billing.get("address_2", ""),
        billing.get("city", ""), billing.get("state", ""), billing.get("country", "")
    ]))

    status = order.get("status", "")
    line_items = order.get("line_items", [])

    for item in line_items:
        product = item.get("name", "")
        qty = item.get("quantity", 1)
        price = item.get("total", "0")

        row = [
            created_at,             # DATE
            order_id,               # ORDER NUMBER
            first_name,             # FIRST NAME
            last_name,              # LAST NAME
            billing.get("city", ""),# LOCATION
            product,                # PRODUCT
            qty,                    # QUANTITY
            price,                  # PRICE
            phone,                  # PHONE NUMBER
            status,                 # Status
            "",                     # comments
            "",                     # (blank column)
            "",                     # agent in charge
            "",                     # (blank column)
            "",                     # shopify name id (not applicable)
            address,                # ADDRESS
            source_name,            # source
            "WooCommerce",          # SOURCE (platform)
        ]
        rows.append(row)

    return rows


def normalize_shopify(order: Dict[str, Any], source_name: str) -> List[List[str]]:
    """Convert Shopify order JSON → list of rows for Google Sheets."""
    rows = []
    order_id = order.get("id")
    created_at = order.get("created_at", "")[:10]

    customer = order.get("customer", {})
    first_name = customer.get("first_name", "")
    last_name = customer.get("last_name", "")
    phone = customer.get("phone", "")

    address_obj = (order.get("shipping_address") or
                   order.get("billing_address") or {})
    address = ", ".join(filter(None, [
        address_obj.get("address1", ""), address_obj.get("address2", ""),
        address_obj.get("city", ""), address_obj.get("province", ""),
        address_obj.get("country", "")
    ]))

    line_items = order.get("line_items", [])
    status = order.get("financial_status", "")

    for item in line_items:
        product = item.get("title", "")
        qty = item.get("quantity", 1)
        price = item.get("price", "0")

        row = [
            created_at,             # DATE
            order_id,               # ORDER NUMBER
            first_name,             # FIRST NAME
            last_name,              # LAST NAME
            address_obj.get("city", ""), # LOCATION
            product,                # PRODUCT
            qty,                    # QUANTITY
            price,                  # PRICE
            phone,                  # PHONE NUMBER
            status,                 # Status
            "",                     # comments
            "",                     # (blank column)
            "",                     # agent in charge
            "",                     # (blank column)
            order.get("name", ""),  # shopify name id
            address,                # ADDRESS
            source_name,            # source
            "Shopify",              # SOURCE (platform)
        ]
        rows.append(row)

    return rows


def normalize_order(order_entry: Dict[str, Any]) -> List[List[str]]:
    """Normalize an order entry from fetch_all_new_orders into rows."""
    platform = order_entry.get("platform")
    source = order_entry.get("source_name")
    raw = order_entry.get("order", {})

    if platform == "woo":
        return normalize_woo(raw, source)
    elif platform == "shopify":
        return normalize_shopify(raw, source)
    else:
        return []
'''
from typing import Dict, Any, List
from datetime import datetime
from config import HEADERS


def _safe_get(d: Dict, keys: List[str], default=""):
    """Nested get with default fallback."""
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d


def _get_note_attr(order: Dict[str, Any], key: str) -> str:
    """Find a value in Shopify note_attributes by key name."""
    for attr in order.get("note_attributes", []):
        if attr.get("name", "").strip().lower() == key.strip().lower():
            return attr.get("value", "")
    return ""


def normalize_woo(order: Dict[str, Any], source_name: str) -> List[List[str]]:
    """Convert WooCommerce order JSON → list of rows for Google Sheets."""
    rows = []
    order_id = order.get("id")
    created_at = order.get("date_created", "")[:10]

    billing = order.get("billing", {})
    first_name = billing.get("first_name", "")
    last_name = billing.get("last_name", "")
    phone = billing.get("phone", "")
    address = ", ".join(filter(None, [
        billing.get("address_1", ""), billing.get("address_2", ""),
        billing.get("city", ""), billing.get("state", ""), billing.get("country", "")
    ]))

    status = order.get("status", "")
    line_items = order.get("line_items", [])

    for item in line_items:

        product = item.get("name", "")
        qty = item.get("quantity", 1)
        price = item.get("total", "0")

        row = [
            created_at,             # DATE
            order_id,               # ORDER NUMBER
            first_name,             # FIRST NAME
            last_name,              # LAST NAME
            billing.get("city", ""),# LOCATION
            product,                # PRODUCT
            qty,                    # QUANTITY
            price,                  # PRICE
            phone,                  # PHONE NUMBER
            status,                 # Status
            "",                     # comments
            "",                     # (blank column)
            "",                     # agent in charge
            "",                     # (blank column)
            "",                     # shopify name id (not applicable)
            address,                # ADDRESS
            source_name,            # source
            "WooCommerce",          # SOURCE (platform)
        ]
        rows.append(row)

    return rows


def normalize_shopify(order: Dict[str, Any], source_name: str) -> List[List[str]]:
    """Convert Shopify order JSON → list of rows for Google Sheets."""
    rows = []
    order_id = order.get("id")
    created_at = order.get("created_at", "")[:10]

    # Pull from note_attributes if present
    full_name = _get_note_attr(order, "Full name")
    phone = _get_note_attr(order, "Phone")
    email = _get_note_attr(order, "Email")
    address_note = _get_note_attr(order, "Address")
    state = _get_note_attr(order, "State")
    city = _get_note_attr(order, "City")
    comments = _get_note_attr(order, "Note")

    # Split full name if available
    if full_name:
        parts = full_name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""
    else:
        customer = order.get("customer", {}) or {}
        first_name = customer.get("first_name", "")
        last_name = customer.get("last_name", "")

    # Fallback to shipping/billing if note fields missing
    address_obj = (order.get("shipping_address") or
                   order.get("billing_address") or {})
    address = address_note or ", ".join(filter(None, [
        address_obj.get("address1", ""), address_obj.get("address2", ""),
        address_obj.get("city", ""), address_obj.get("province", ""),
        address_obj.get("country", "")
    ]))

    line_items = order.get("line_items", [])
    status = ""   # leave blank so you can fill manually in Sheets

    for item in line_items:
        try:
            
            qty = int(item.get("quantity", 1))
        except Exception:
            qty = 1

    # unit price (string from API) -> float safely
        try:
            unit_price = float(item.get("price", 0) or 0)
        except Exception:
            # if price contains commas or currency symbols, strip them
            p = str(item.get("price", 0))
            p = p.replace(",", "").replace("₦", "").replace("$", "").strip()
            try:
                unit_price = float(p) if p else 0.0
            except Exception:
                unit_price = 0.0

    # 1) Prefer `total_discount` (some API versions supply this)
    discount_value = 0.0
    raw_td = item.get("total_discount", None)
    if raw_td is not None:
        try:
            discount_value = float(raw_td)
        except Exception:
            # strip currency/commas then try again
            s = str(raw_td).replace(",", "").replace("₦", "").replace("$", "").strip()
            try:
                discount_value = float(s) if s else 0.0
            except Exception:
                discount_value = 0.0

    # 2) Fallback: check discount_allocations (array of { amount, ... })
    if (not discount_value) and item.get("discount_allocations"):
        # sum absolute amounts found
        for alloc in item.get("discount_allocations", []):
            # new shopify shape: alloc.get("amount") OR alloc.amount_set.shop_money.amount
            amt = alloc.get("amount") or (
                alloc.get("amount_set", {})
                     .get("shop_money", {})
                     .get("amount")
            )
            if amt is None:
                continue
            try:
                discount_value += abs(float(amt))
            except Exception:
                # try sanitizing
                s = str(amt).replace(",", "").replace("₦", "").replace("$", "").strip()
                try:
                    discount_value += abs(float(s))
                except Exception:
                    pass

    # 3) If discount_value is negative (API sometimes provides negative displays),
    #    treat it as magnitude to subtract.
    if discount_value < 0:
        discount_value = abs(discount_value)

    # compute line total = (unit * qty) - discount_assigned_to_this_line
    line_total = (unit_price * qty) - discount_value

    # Optional: round to 2 decimals
    line_total = round(line_total, 2)

    # Debugging helper: if something odd (discount exists but not applied), print details once
    if discount_value and line_total == (unit_price * qty):
        print("⚠️ Discount found but line_total unchanged. debug:", {
            "item_id": item.get("id"),
            "title": item.get("title"),
            "price": item.get("price"),
            "qty": qty,
            "total_discount": item.get("total_discount"),
            "discount_allocations": item.get("discount_allocations"),
        })

    # build row (same as before)
    row = [
        created_at,             # DATE
        order.get("name", ""),  # ORDER NUMBER
        first_name,             # FIRST NAME
        last_name,              # LAST NAME
        city or address_obj.get("city", ""), # LOCATION
        item.get("title", ""),  # PRODUCT
        qty,                    # QUANTITY
        str(line_total),        # PRICE (line total after discount)
        phone or address_obj.get("phone", ""), # PHONE NUMBER
        status,                 # Status
        comments,               # comments
        "",                     # (blank column)
        "",                     # agent in charge
        "",                     # (blank column)
        order_id,               # shopify raw id
        address,                # ADDRESS
        source_name,            # source
        "Shopify",              # SOURCE (platform)
    ]
    rows.append(row)

    return rows


def normalize_order(order_entry: Dict[str, Any]) -> List[List[str]]:
    """Normalize an order entry from fetch_all_new_orders into rows."""
    platform = order_entry.get("platform")
    source = order_entry.get("source_name")
    raw = order_entry.get("order", {})

    if platform == "woo":
        return normalize_woo(raw, source)
    elif platform == "shopify":
        return normalize_shopify(raw, source)
    else:
        return []
