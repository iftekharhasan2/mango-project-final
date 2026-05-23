import os
import uuid
from flask import Flask, request, jsonify, render_template, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

# =========================
# CONFIG
# =========================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
BASE_URL   = os.getenv("BASE_URL", "http://localhost:5000")

# static_folder points to ../public so Flask can find files locally too.
# On Vercel, /static/* is served directly from the public/ CDN folder.
app = Flask(__name__, template_folder="../templates", static_folder="../public", static_url_path="/static")

# =========================
# DB — lazy init (required for Vercel serverless)
# =========================
_client = None
_orders = None

def get_orders():
    global _client, _orders
    if _orders is None:
        from pymongo import MongoClient
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _orders = _client["paystation_demo"]["orders"]
    return _orders

# =========================
# PRODUCTS (server-side truth)
# =========================
PRODUCTS = {
    "p1": {"name": "Wireless Earbuds", "price": 5,  "emoji": "🎧", "description": "High-quality wireless earbuds for immersive audio experience.", "image": "earbuds.jpg"},
    "p2": {"name": "Phone Case",       "price": 3,  "emoji": "📱", "description": "Durable phone case for protection.",                            "image": "phone-case.jpg"},
    "p3": {"name": "USB-C Cable",      "price": 18, "emoji": "🔌", "description": "Fast-charging USB-C cable.",                                    "image": "usb-cable.jpg"},
}

PRODUCTS2 = {
    "p1": {"name": "Chicken 5KG",  "price": 5,  "emoji": "🍗", "description": "Fresh chicken, 5KG pack.",  "image": "chicken-5kg.jpg"},
    "p2": {"name": "Chicken 10KG", "price": 3,  "emoji": "🍗", "description": "Fresh chicken, 10KG pack.", "image": "chicken-1kg.jpg"},
    "p3": {"name": "Chicken 15KG", "price": 18, "emoji": "🍗", "description": "Fresh chicken, 15KG pack.", "image": "chicken-5kg.jpg"},
}

ALL_PRODUCTS = {**PRODUCTS, **{"b" + k: v for k, v in PRODUCTS2.items()}}

# =========================
# PRICE ENGINE
# =========================
def calc(items):
    total = 0
    line_items = []
    for i in items:
        pid = i.get("id")
        qty = int(i.get("qty", 1))
        if pid not in ALL_PRODUCTS or qty < 1 or qty > 10:
            raise ValueError(f"Invalid product or quantity: {pid}")
        product = ALL_PRODUCTS[pid]
        subtotal = product["price"] * qty
        total += subtotal
        line_items.append({
            "id": pid,
            "name": product["name"],
            "price": product["price"],
            "qty": qty,
            "subtotal": subtotal
        })
    if total <= 0:
        raise ValueError("Cart is empty")
    return total, line_items

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return render_template("index.html", products=PRODUCTS, products2=PRODUCTS2)

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

@app.route("/success")
def success():
    invoice = request.args.get("invoice_number", "")
    return render_template("result.html", success=True, invoice=invoice, status="Success")

@app.route("/failed")
def failed():
    invoice = request.args.get("invoice_number", "")
    return render_template("result.html", success=False, invoice=invoice, status="Failed")

# =========================
# API: PLACE ORDER
# =========================
@app.route("/api/place-order", methods=["POST"])
def place_order():
    try:
        data    = request.get_json(force=True)
        name    = str(data.get("name", "")).strip()
        email   = "urboressentials@gmail.com"
        phone_raw = str(data.get("phone", "")).strip()
        # Normalize +8801XXXXXXXXX or 8801XXXXXXXXX -> 01XXXXXXXXX
        import re as _re
        phone = _re.sub(r'^(\+880|880)', '0', phone_raw)
        address = str(data.get("address", "")).strip()
        items   = data.get("items", [])

        if not all([name, phone, address]):
            return jsonify({"error": "All customer fields are required"}), 400
        if not items:
            return jsonify({"error": "Cart is empty"}), 400

        amount, line_items = calc(items)
        invoice = str(uuid.uuid4())

        order_doc = {
            "invoice": invoice,
            "items": line_items,
            "amount": amount,
            "status": "placed",
            "verified": False,
            "payment": "cash_on_delivery",
            "customer": {
                "name": name,
                "email": email,
                "phone": phone,
                "address": address
            }
        }
        get_orders().insert_one(order_doc)
        return jsonify({"invoice": invoice, "amount": amount, "status": "placed"})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception:
        return jsonify({"error": "Server error"}), 500

# =========================
# VERCEL ENTRYPOINT
# =========================
if __name__ == "__main__":
    app.run(debug=True)
