from typing import List
import os
from pathlib import Path

import pandas as pd

from src.finflow.constants import DATA_FOLDER_ENV
from src.finflow.statement_parsing.pdf_statement_parser import PDFTransactionParser


class DataLoader:
    """
    Load transaction data from disk and optionally filter by keywords.
    """

    def __init__(self, file_name: str = "transactions.csv"):
        """
        Parameters
        ----------
        file_name : str
            CSV file name containing transaction data.
        """
        self.file_name = file_name

        base_folder = os.getenv(DATA_FOLDER_ENV)
        if not base_folder:
            raise ValueError(f"Environment variable {DATA_FOLDER_ENV} is not set")

        self.base_path: Path = Path(base_folder).expanduser().resolve()
        self.file_path: Path = self.base_path / self.file_name

    def load(self, keywords: List[str] = []) -> pd.DataFrame:
        """
        Load transactions from CSV and optionally filter by description keywords.

        Parameters
        ----------
        keywords : List[str], optional
            List of keywords used to filter the transaction descriptions.
            If empty, no filtering is applied.

        Returns
        -------
        pd.DataFrame
            Transaction data indexed by booking date.
        """
        df = pd.read_csv(self.file_path, index_col=False)

        df[PDFTransactionParser.COL_BOOKING_DATE] = pd.to_datetime(
            df[PDFTransactionParser.COL_BOOKING_DATE]
        )
        df = df.set_index(PDFTransactionParser.COL_BOOKING_DATE)

        if keywords:
            pattern = "|".join(keywords)
            df = df[
                df[PDFTransactionParser.COL_DESCRIPTION].str.contains(pattern, na=False)
            ]

        return df
