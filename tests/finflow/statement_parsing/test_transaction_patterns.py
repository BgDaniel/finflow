import re
import unittest

# Transaction regex
TRANSACTION_PATTERN_TEST = re.compile(
    r"(\d{2}\.\d{2}\.\d{4})\r?\n"                          # Booking date
    r"(\d{2}\.\d{2}\.\d{4})Lastschrift /\r?\nBelastung\r?\n"  # Value date / Charge
    r"([A-Z0-9]+)\r?\n"                                    # Transaction ID
    r"((?:[A-Z0-9]+/\d+ ?)+)"                              # Codes: numeric after /, optional space after code
    r"([A-Za-z][\s\S]*?)"                                  # Description: starts with letter, includes anything (lazy)
    r"(-?\d{1,3}(?:\.\d{3})*,\d{2})",                      # Amount: no space between description end and amount
    re.DOTALL
)


# Sample text
SAMPLE_TEXT = """04.12.2024
04.12.2024Lastschrift /
Belastung
7L2C1U7N2KRV
5LYN/35742D.T.NET Service OHG 402505/129801/EUR 48.40
End-to-End-Ref.:
150808
CORE /Mandatsref.:
402505
Gläubiger-ID:
DE92ZZZ00000085710-48,40
"""


class TestTransactionPattern(unittest.TestCase):
    def test_transaction_pattern_match(self):
        """Test that the regex correctly matches and extracts fields"""
        match = TRANSACTION_PATTERN_TEST.search(SAMPLE_TEXT)
        self.assertIsNotNone(match, "Pattern did not match the sample text.")

        groups = match.groups()
        self.assertEqual(groups[0], "04.12.2024")  # Booking Date
        self.assertEqual(groups[1], "04.12.2024")  # Value Date
        self.assertEqual(groups[2], "7L2C1U7N2KRV")  # Transaction ID
        self.assertEqual(groups[3], "5LYN/35742")  # Codes
        self.assertTrue(groups[4].startswith("D.T.NET Service"))  # Description starts correctly
        self.assertEqual(groups[5], "DE92ZZZ00000085710")  # Gläubiger-ID
        self.assertEqual(groups[6], "-48,40")  # Amount


if __name__ == "__main__":
    unittest.main()
