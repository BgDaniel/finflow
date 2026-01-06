# Regex pattern to parse transactions
import re

from src.finflow.statement_parsing.transaction_types import TransactionType

TRANSACTION_PATTERNS = {
    TransactionType.DIRECT_DEBIT: [
        re.compile(
            r"(\d{2}\.\d{2}\.\d{4})\r?\n"  # Booking date
            r"(\d{2}\.\d{2}\.\d{4})Lastschrift /\r?\nBelastung\r?\n"  # Value date / Charge
            r"([A-Z0-9]+)\r?\n"  # Transaction ID
            r"((?:[A-Z0-9]+/\d+ ?)+)"  # Codes: numeric after /, optional space after code
            r"([A-Za-z][\s\S]*?)"  # Description: starts with letter, includes anything (lazy)
            r"(-?\d{1,3}(?:\.\d{3})*,\d{2})",  # Amount: no space between description end and amount
            re.DOTALL
        )#,
    ],
    TransactionType.TRANSFER: [
        re.compile(
            r"(\d{2}\.\d{2}\.\d{4})\n"  # Booking date
            r"(\d{2}\.\d{2}\.\d{4})Übertrag /\nÜberweisung\n"  # Value date / Charge
            r"([A-Z0-9]+)\n"  # Transaction ID
            r"((?:[A-Z0-9]+/\d+ ?)+)"   # Codes (numeric after /)
            r"(\s*[\s\S]+?)\nGläubiger-ID:\nDE\d{2}ZZZ\d{11}"  # Description (multi-line)
            r"(-?\d{1,3}(?:\.\d{3})*,\d{2})",  # Amount
            re.DOTALL,
        )
    ],
}


