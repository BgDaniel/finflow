from enum import Enum


class TransactionType(Enum):
    """
    Supported transaction types found in bank statements.
    """
    DIRECT_DEBIT = "Lastschrift"
    CARD_TRANSACTION = "Kartenverfügung"
    TRANSFER = "Übertrag"