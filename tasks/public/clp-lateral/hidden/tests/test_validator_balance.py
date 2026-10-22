import unittest

from _packer import PlacedItem, SKU
from _validator import validate_plan

SPEC = {"L": 200, "W": 200, "H": 200, "max_kg": 1000, "name": "test"}


def codes_for_long_item_at(y):
    placed = [PlacedItem("LONG", 1, 0, y, 0, 200, 50, 50, 300, "#000", False)]
    return {issue.code for issue in validate_plan(placed, [SKU("LONG", "LONG", 200, 50, 50, 300, 1)], SPEC)}


class LateralBalanceTest(unittest.TestCase):
    def test_long_item_centred_across_the_width_is_balanced(self):
        self.assertNotIn("lateral_weight_balance", codes_for_long_item_at(75))

    def test_long_item_against_one_side_wall_is_flagged(self):
        self.assertIn("lateral_weight_balance", codes_for_long_item_at(0))


if __name__ == "__main__":
    unittest.main()
