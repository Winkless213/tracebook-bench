import unittest

from _packer import PlacedItem, SKU
from _validator import validate_plan

SPEC = {"L": 200, "W": 200, "H": 300, "max_kg": 1000, "name": "test"}


def box(model, z, weight):
    return PlacedItem(model, 1, 0, 0, z, 100, 100, 50, weight, "#000", False)


class StackedTopLoadTest(unittest.TestCase):
    def test_load_from_every_layer_above_reaches_the_bottom_box(self):
        issues = validate_plan(
            [box("BASE", 0, 20), box("MID", 50, 60), box("TOP", 100, 60)],
            [
                SKU("BASE", "BASE", 100, 100, 50, 20, 1, max_top_load_kg=100),
                SKU("MID", "MID", 100, 100, 50, 60, 1),
                SKU("TOP", "TOP", 100, 100, 50, 60, 1),
            ],
            SPEC,
        )
        exceeded = [i for i in issues if i.code == "top_load_exceeded"]
        self.assertEqual(["BASE"], [i.item for i in exceeded])
        self.assertIn("120", exceeded[0].message)

    def test_stack_within_every_limit_passes(self):
        issues = validate_plan(
            [box("BASE", 0, 20), box("MID", 50, 60), box("TOP", 100, 30)],
            [
                SKU("BASE", "BASE", 100, 100, 50, 20, 1, max_top_load_kg=100),
                SKU("MID", "MID", 100, 100, 50, 60, 1, max_top_load_kg=40),
                SKU("TOP", "TOP", 100, 100, 50, 30, 1),
            ],
            SPEC,
        )
        self.assertEqual([], [i for i in issues if i.code == "top_load_exceeded"])


if __name__ == "__main__":
    unittest.main()
