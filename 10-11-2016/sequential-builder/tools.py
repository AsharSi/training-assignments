"""
tools.py - Product search and order-total tools for agent use.

Both tools return plain dicts so an agent framework can serialise them
to JSON directly. Every response has a "success" flag and a "message".
"""

import json
import os

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "products.json")


def _load_products(data_file=DATA_FILE):
    """Read the product list from JSON. Raises a clear error if the file is missing or malformed."""
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            products = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Product data file not found: {data_file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Product data file is not valid JSON: {e}")
    if not isinstance(products, list):
        raise ValueError("Product data must be a JSON list of product objects.")
    return products


def _format_product(p):
    return {
        "id": p["id"],
        "name": p["name"],
        "category": p["category"],
        "price_inr": p["price_inr"],
        "stock": p["stock"],
        "rating": p["rating"],
    }


# ---------------------------------------------------------------------------
# Tool 1
# ---------------------------------------------------------------------------
def search_products(query, data_file=DATA_FILE):
    """
    Search products by name or category (case-insensitive, partial match).

    Args:
        query (str): A product name or category, e.g. "novabook" or "laptop".

    Returns:
        dict with keys:
            success (bool), message (str), count (int), results (list of products)
            Each product includes id, name, category, price_inr, stock, rating.
    """
    if not isinstance(query, str) or not query.strip():
        return {
            "success": False,
            "message": "Please provide a non-empty product name or category to search.",
            "count": 0,
            "results": [],
        }

    term = query.strip().lower()
    products = _load_products(data_file)

    matches = [
        _format_product(p)
        for p in products
        if term in p.get("name", "").lower() or term in p.get("category", "").lower()
    ]

    if not matches:
        return {
            "success": False,
            "message": f"No products found matching '{query.strip()}'.",
            "count": 0,
            "results": [],
        }

    return {
        "success": True,
        "message": f"Found {len(matches)} product(s) matching '{query.strip()}'.",
        "count": len(matches),
        "results": matches,
    }


# ---------------------------------------------------------------------------
# Tool 2
# ---------------------------------------------------------------------------
def calculate_order_total(product_id, quantity, data_file=DATA_FILE):
    """
    Calculate the total cost of ordering a product, checking stock.

    Args:
        product_id (str): Product ID, e.g. "P101" (case-insensitive).
        quantity (int): Number of units requested; must be a positive whole number.

    Returns:
        dict with keys:
            success (bool), message (str), and on success:
            product_id, product_name, unit_price_inr, quantity, total_inr, stock_remaining
    """
    # Validate product_id
    if not isinstance(product_id, str) or not product_id.strip():
        return {"success": False, "message": "Please provide a valid product ID."}

    # Validate quantity: positive int only (bool is a subclass of int, so exclude it).
    # Accept whole-number strings like "3" since agents often pass strings.
    if isinstance(quantity, bool):
        return {"success": False, "message": "Invalid quantity: must be a positive whole number."}
    if isinstance(quantity, str) and quantity.strip().isdigit():
        quantity = int(quantity.strip())
    if isinstance(quantity, float) and quantity.is_integer():
        quantity = int(quantity)
    if not isinstance(quantity, int):
        return {"success": False, "message": "Invalid quantity: must be a positive whole number."}
    if quantity <= 0:
        return {"success": False, "message": "Invalid quantity: must be greater than zero."}

    pid = product_id.strip().upper()
    products = _load_products(data_file)
    product = next((p for p in products if p["id"].upper() == pid), None)

    if product is None:
        return {"success": False, "message": f"Product with ID '{product_id.strip()}' does not exist."}

    stock = product["stock"]
    if stock == 0:
        return {
            "success": False,
            "message": f"'{product['name']}' ({product['id']}) is out of stock.",
            "product_id": product["id"],
            "stock_available": 0,
        }
    if quantity > stock:
        return {
            "success": False,
            "message": (
                f"Insufficient stock for '{product['name']}' ({product['id']}): "
                f"requested {quantity}, only {stock} available."
            ),
            "product_id": product["id"],
            "stock_available": stock,
        }

    unit_price = product["price_inr"]
    total = unit_price * quantity
    return {
        "success": True,
        "message": (
            f"{quantity} x {product['name']} at ₹{unit_price:,} each = ₹{total:,}."
        ),
        "product_id": product["id"],
        "product_name": product["name"],
        "unit_price_inr": unit_price,
        "quantity": quantity,
        "total_inr": total,
        "stock_remaining": stock - quantity,
    }