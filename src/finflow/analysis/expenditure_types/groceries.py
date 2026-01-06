from src.finflow.analysis.visualization.plot_times_series import plot_time_series
from src.finflow.data_handler.data_loader import DataLoader


if __name__ == "__main__":
    groceries_keywords = ["REWE", "WIENER FEINBACKEREI", "SCHECK-IN CENTER Alnature"]
    filtered_data = DataLoader().load(keywords=groceries_keywords)

    plot_time_series(
        filtered_data,
        category="Groceries",
        freq="M",
    )
