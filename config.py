import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv()
BASE_DIR = os.path.dirname(__file__)
# ==========================
# Stores (WooCommerce + Shopify)
# ==========================
STORES = [
    {
        "name": os.getenv("WOO1_NAME"),
        "url": os.getenv("WOO1_URL"),
        "consumer_key": os.getenv("WOO1_CONSUMER_KEY"),
        "consumer_secret": os.getenv("WOO1_CONSUMER_SECRET"),
        "type": "woo",
    },
    {
        "name": os.getenv("WOO2_NAME"),
        "url": os.getenv("WOO2_URL"),
        "consumer_key": os.getenv("WOO2_CONSUMER_KEY"),
        "consumer_secret": os.getenv("WOO2_CONSUMER_SECRET"),
        "type": "woo",
    },
    {
        "name": os.getenv("SHOPIFY_NAME"),
        "url": os.getenv("SHOPIFY_URL"),
        "access_token": os.getenv("SHOPIFY_ACCESS_TOKEN"),
        "type": "shopify",
    },
]

# ==========================
# Google Sheets
# ==========================
CREDS_FILE = os.getenv("CREDS_FILE")
MASTER_SHEET_ID = os.getenv("MASTER_SHEET_ID")

# ==========================
# Twilio WhatsApp
# ==========================
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_WHATSAPP = os.getenv("TWILIO_WHATSAPP")

# ==========================
# Headers
# ==========================
HEADERS = [
    "DATE",
    "ORDER NUMBER",
    "FIRST NAME",
    "LAST NAME",
    "LOCATION",
    "PRODUCT",
    "QUANTITY",
    "PRICE",
    "PHONE NUMBER",
    "Status",
    "comments",
    "",
    "agent in charge",
    "",
    "shopify name id",
    "ADDRESS",
    "source",
    "SOURCE",
]

# ==========================
# State directory
# ==========================
STATE_DIR = os.path.join(os.path.dirname(__file__), "state")

# ==========================
# WhatsApp Sending Config
# ==========================
WHATSAPP_DELAY_SECONDS = 5



TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_FROM = os.getenv("TWILIO_FROM")

