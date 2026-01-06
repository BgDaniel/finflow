import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from src.finflow.statement_parsing.pdf_statement_parser import PDFTransactionParser


# ---------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------


def euro_formatter(x, pos):
    """Format axis ticks as Euro currency."""
    return f"€{x:,.0f}"


def frequency_label(freq: str) -> str:
    """
    Convert a pandas resampling frequency code into a human-readable label.
    """
    freq_map = {
        "D": "Daily",
        "W": "Weekly",
        "M": "Monthly",
        "Q": "Quarterly",
        "Y": "Yearly",
        "A": "Yearly",
    }

    base_freq = "".join(filter(str.isalpha, freq.upper()))
    return freq_map.get(base_freq, f"Every {freq}")


# ---------------------------------------------------------------------
# Plotting function
# ---------------------------------------------------------------------


def plot_time_series(
    df: pd.DataFrame,
    category: str,
    freq: str = "M",
    rolling_window: int = 4,
) -> None:
    """
    Plot aggregated expenditure time series for a given spending category.

    Creates three vertically stacked plots:
    1. Total expenditure per period with rolling mean
    2. Period-over-period change
    3. Cumulative expenditure over time

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame indexed by datetime.
    category : str
        Spending category name (e.g. "Groceries").
    freq : str, optional
        Resampling frequency (default "M").
    rolling_window : int, optional
        Rolling mean window size.

    Returns
    -------
    None
    """
    freq_name = frequency_label(freq)

    ts = df[PDFTransactionParser.COL_AMOUNT].abs().resample(freq).sum()
    ts_change = ts.diff()
    ts_rolling = ts.rolling(window=rolling_window, min_periods=1).mean()
    ts_cumsum = ts.cumsum()

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12))
    formatter = FuncFormatter(euro_formatter)

    # ---- Top plot: totals + rolling mean ----
    ax1.plot(ts.index, ts.values, marker="o", color="blue", label="Total |Amount|")
    ax1.plot(
        ts_rolling.index,
        ts_rolling.values,
        color="red",
        linestyle="--",
        label=f"{rolling_window}-period Rolling Mean",
    )
    ax1.yaxis.set_major_formatter(formatter)
    ax1.set_title("Total Expenditure per Period")
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_ylim((0.0, 1.1 * ts.max()))

    # ---- Middle plot: change ----
    colors = ["green" if x >= 0 else "red" for x in ts_change.values]
    ax2.bar(ts_change.index, ts_change.values, color=colors, alpha=0.7, width=6)
    ax2.set_title(f"{freq_name} Change")
    ax2.grid(True, alpha=0.3)

    # ---- Bottom plot: cumulative ----
    ax3.plot(
        ts_cumsum.index,
        ts_cumsum.values,
        color="orange",
        marker="o",
    )
    ax3.set_xlabel("Date")
    ax3.yaxis.set_major_formatter(formatter)
    ax3.set_title("Cumulative Expenditure Over Time")
    ax3.grid(True, alpha=0.3)

    # ---- Overall title ----
    fig.suptitle(
        f"{category} Expenditure Analysis — {freq_name}",
        fontsize=16,
        fontweight="bold",
    )

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()
