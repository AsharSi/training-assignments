"""
test_tools.py - Tests each tool on its own, before attaching to agents.
Run with:  python -m unittest test_tools.py -v
"""

import unittest
from tools import search_products, calculate_order_total


class TestSearchProducts(unittest.TestCase):

    def test_search_by_category(self):
        r = search_products("Laptop")
        self.assertTrue(r["success"])
        self.assertEqual(r["count"], 2)
        self.assertEqual({p["id"] for p in r["results"]}, {"P101", "P102"})

    def test_search_by_name_partial_case_insensitive(self):
        r = search_products("novabook air")
        self.assertTrue(r["success"])
        self.assertEqual(r["results"][0]["id"], "P101")

    def test_result_contains_required_fields(self):
        p = search_products("NovaBook Air 14")["results"][0]
        for field in ("id", "price_inr", "stock", "rating"):
            self.assertIn(field, p)
        self.assertEqual(p["price_inr"], 52000)
        self.assertEqual(p["stock"], 8)
        self.assertEqual(p["rating"], 4.5)

    def test_no_match(self):
        r = search_products("Refrigerator")
        self.assertFalse(r["success"])
        self.assertEqual(r["count"], 0)
        self.assertIn("No products found", r["message"])

    def test_empty_and_invalid_query(self):
        for q in ("", "   ", None, 123):
            r = search_products(q)
            self.assertFalse(r["success"])
            self.assertEqual(r["results"], [])


class TestCalculateOrderTotal(unittest.TestCase):

    def test_valid_order(self):
        r = calculate_order_total("P101", 2)
        self.assertTrue(r["success"])
        self.assertEqual(r["unit_price_inr"], 52000)
        self.assertEqual(r["total_inr"], 104000)
        self.assertEqual(r["stock_remaining"], 6)

    def test_order_exact_stock(self):
        r = calculate_order_total("P101", 8)
        self.assertTrue(r["success"])
        self.assertEqual(r["stock_remaining"], 0)

    def test_case_insensitive_id_and_string_quantity(self):
        r = calculate_order_total("p105", "3")
        self.assertTrue(r["success"])
        self.assertEqual(r["total_inr"], 3499 * 3)

    def test_insufficient_stock(self):
        r = calculate_order_total("P102", 5)
        self.assertFalse(r["success"])
        self.assertIn("Insufficient stock", r["message"])
        self.assertEqual(r["stock_available"], 3)

    def test_out_of_stock(self):
        r = calculate_order_total("P104", 1)
        self.assertFalse(r["success"])
        self.assertIn("out of stock", r["message"])

    def test_invalid_quantities(self):
        for q in (0, -1, 2.5, "abc", "-2", None, True, [1]):
            r = calculate_order_total("P101", q)
            self.assertFalse(r["success"], f"quantity {q!r} should be rejected")
            self.assertIn("Invalid quantity", r["message"])

    def test_nonexistent_product(self):
        r = calculate_order_total("P999", 1)
        self.assertFalse(r["success"])
        self.assertIn("does not exist", r["message"])

    def test_invalid_product_id(self):
        for pid in ("", None, 101):
            r = calculate_order_total(pid, 1)
            self.assertFalse(r["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)