import unittest

from _packer import PlacedItem, SKU
from _validator import validate_plan


class SegmentWeightTest(unittest.TestCase):
    def test_item_spanning_two_segments_counts_where_its_centre_lies(self):
        spec = {"L": 600, "W": 200, "H": 200, "max_kg": 5000, "name": "test"}
        placed = [
            PlacedItem("A", 1, 80, 0, 0, 60, 100, 50, 150, "#000", False),
            PlacedItem("B", 1, 110, 100, 0, 60, 100, 50, 100, "#000", False),
        ]
        skus = [SKU("A", "A", 60, 100, 50, 150, 1), SKU("B", "B", 60, 100, 50, 100, 1)]
        issues = validate_plan(placed, skus, spec, max_segment_weight_kg=200)
        overweight = [i for i in issues if i.code == "segment_overweight"]
        self.assertEqual(1, len(overweight))
        self.assertIn("第 2 段", overweight[0].message)
        self.assertIn("250", overweight[0].message)


if __name__ == "__main__":
    unittest.main()
