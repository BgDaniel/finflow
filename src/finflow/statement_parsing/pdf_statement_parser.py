import os
import datetime as dt
from pathlib import Path
from typing import List, Optional
import logging

import pandas as pd
from PyPDF2 import PdfReader

from src.finflow.statement_parsing.transaction_patterns import TRANSACTION_PATTERNS
from src.finflow.statement_parsing.transaction_types import TransactionType


DATA_FOLDER_ENV: str = "DATA_FOLDER"


class PDFTransactionParser:
    """
    Parser for bank statement PDF files.

    The parser reads PDF files from a source directory, extracts transactions
    using predefined regular-expression patterns, and returns the results as
    pandas DataFrames.

    Attributes
    ----------
    source_folder : Path
        Absolute path to the folder containing PDF files.
    transactions : pd.DataFrame
        Combined DataFrame of all parsed transactions.
    logger : logging.Logger
        Logger instance used for parser messages.
    """

    # -------------------------------
    # Column name constants
    # -------------------------------
    COL_BOOKING_DATE: str = "Booking Date"
    COL_VALUE_DATE: str = "Value Date"
    COL_TRANSACTION_ID: str = "Transaction ID"
    COL_CODE: str = "Code"
    COL_DESCRIPTION: str = "Description"
    COL_AMOUNT: str = "Amount"

    def __init__(self, source_folder: str, log_level: int = logging.INFO) -> None:
        """
        Initialize the PDF transaction parser.

        Parameters
        ----------
        source_folder : str
            Relative path (to DATA_FOLDER) of the directory containing PDF files.
        log_level : int, optional
            Logging level for the internal logger (default: logging.INFO).

        Raises
        ------
        ValueError
            If the environment variable DATA_FOLDER is not set.
        """
        base_folder = os.getenv(DATA_FOLDER_ENV)
        if not base_folder:
            raise ValueError(f"Environment variable {DATA_FOLDER_ENV} is not set")

        base_path: Path = Path(base_folder).expanduser().resolve()
        self.source_folder: Path = (base_path / source_folder).resolve()

        self.transactions: pd.DataFrame = pd.DataFrame()

        # Configure logger
        self.logger: logging.Logger = logging.getLogger("TransactionParser")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                "%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.setLevel(log_level)

    @staticmethod
    def parse_amount(amount_str: str) -> Optional[float]:
        """
        Convert a German-formatted amount string to float.

        Examples
        --------
        '-1.234,56' -> -1234.56

        Parameters
        ----------
        amount_str : str
            Amount string using '.' as thousands separator and ',' as decimal separator.

        Returns
        -------
        Optional[float]
            Parsed amount as float, or None if conversion fails.
        """
        try:
            return float(amount_str.replace(".", "").replace(",", "."))
        except ValueError:
            return None

    @staticmethod
    def parse_date(date_str: str) -> Optional[dt.date]:
        """
        Convert a date string in DD.MM.YYYY format to a datetime.date object.

        Parameters
        ----------
        date_str : str
            Date string in the format DD.MM.YYYY.

        Returns
        -------
        Optional[datetime.date]
            Parsed date, or None if conversion fails.
        """
        try:
            return dt.datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            return None

    def parse_pdf(
        self,
        pdf_path: str,
        transaction_type: Optional[TransactionType] = TransactionType.DIRECT_DEBIT,
    ) -> pd.DataFrame:
        """
        Parse a single PDF file and extract transactions.

        Parameters
        ----------
        pdf_path : str
            Path to the PDF file.
        transaction_type : Optional[TransactionType], optional
            If provided, only transactions of this type are parsed.
            If None, all supported transaction types are parsed.

        Returns
        -------
        pd.DataFrame
            DataFrame containing parsed transactions from the PDF.
        """
        reader = PdfReader(pdf_path)
        transaction_list: List[dict] = []

        for page_index, page in enumerate(reader.pages):
            text: Optional[str] = page.extract_text()
            if not text:
                self.logger.warning(
                    f"Page {page_index + 1} in {os.path.basename(pdf_path)} "
                    "has no extractable text."
                )
                continue

            if transaction_type is not None:
                pattern_items = [
                    (transaction_type, p)
                    for p in TRANSACTION_PATTERNS.get(transaction_type, [])
                ]
            else:
                pattern_items = [
                    (tx_type, p)
                    for tx_type, patterns in TRANSACTION_PATTERNS.items()
                    for p in patterns
                ]

            for _, pattern in pattern_items:
                for match in pattern.findall(text):
                    (
                        booking_date,
                        value_date,
                        transaction_id,
                        code,
                        description,
                        amount_str,
                    ) = match

                    transaction_list.append(
                        {
                            self.COL_BOOKING_DATE: self.parse_date(booking_date),
                            self.COL_VALUE_DATE: self.parse_date(value_date),
                            self.COL_TRANSACTION_ID: transaction_id,
                            self.COL_CODE: code,
                            self.COL_DESCRIPTION: description.strip(),
                            self.COL_AMOUNT: self.parse_amount(amount_str),
                        }
                    )

        df: pd.DataFrame = pd.DataFrame(transaction_list)

        self.logger.info(
            f"Parsed {len(df)} transactions from {os.path.basename(pdf_path)}"
        )

        return df

    def parse_pdfs(
        self,
        transaction_type: Optional[TransactionType] = TransactionType.DIRECT_DEBIT,
        output_csv: Optional[Path] = None,
    ) -> pd.DataFrame:
        """
        Parse all PDF files in the source folder and combine the results.

        Parameters
        ----------
        transaction_type : Optional[TransactionType], optional
            If provided, only transactions of this type are parsed.
            If None, all supported transaction types are parsed.
        output_csv : Optional[Path], optional
            If provided, the combined DataFrame is written to this CSV file.

        Returns
        -------
        pd.DataFrame
            Combined DataFrame of all parsed transactions.
        """
        all_dfs: List[pd.DataFrame] = []

        for filename in os.listdir(self.source_folder):
            if filename.lower().endswith(".pdf"):
                pdf_path = os.path.join(self.source_folder, filename)
                df_pdf = self.parse_pdf(pdf_path, transaction_type=transaction_type)
                if not df_pdf.empty:
                    all_dfs.append(df_pdf)

        if all_dfs:
            self.transactions = pd.concat(all_dfs, ignore_index=True)
            self.transactions.sort_values(by=self.COL_BOOKING_DATE, inplace=True)
        else:
            self.transactions = pd.DataFrame()

        self.logger.info(f"Total transactions parsed: {len(self.transactions)}")

        if output_csv is not None:
            output_csv = Path(output_csv).expanduser().resolve()
            output_csv.parent.mkdir(parents=True, exist_ok=True)
            self.transactions.to_csv(output_csv, index=False)
            self.logger.info(f"Saved transactions to {output_csv}")

        return self.transactions


# -------------------------------
# Main section
# -------------------------------
if __name__ == "__main__":
    parser = PDFTransactionParser(source_folder="financial_reports")
    transactions = parser.parse_pdfs(output_csv="transactions.csv")
