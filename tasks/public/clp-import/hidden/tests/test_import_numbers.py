import unittest

import app


def parse_tsv(text):
    data = app._parse_manifest_file_bytes("manifest.csv", text.encode("utf-8"))
    return {sku["model"]: sku for sku in data["skus"]}


class ImportNumberTest(unittest.TestCase):
    def test_thousands_separators_are_ignored(self):
        skus = parse_tsv("型号\t长\t宽\t高\t重\t箱\nSKU-A\t120\t80\t60\t1,200\t10\nSKU-B\t50\t40\t30\t25\t1,000\n")
        self.assertEqual(1200.0, skus["SKU-A"]["weight"])
        self.assertEqual(1000, skus["SKU-B"]["qty"])

    def test_fullwidth_thousands_separator_is_ignored(self):
        skus = parse_tsv("型号\t长\t宽\t高\t重\t箱\nSKU-C\t100\t90\t70\t１，５００\t5\n")
        self.assertEqual(1500.0, skus["SKU-C"]["weight"])


if __name__ == "__main__":
    unittest.main()
