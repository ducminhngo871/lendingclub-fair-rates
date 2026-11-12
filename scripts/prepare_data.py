"""Step 1: clean the raw accepted-loans file and save data/processed/loans_clean.parquet."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lc_rates import config, data  # noqa: E402

if __name__ == "__main__":
    df = data.build_clean_dataset()
    print(f"Saved {len(df):,} finished, matured loans to {config.LOANS_CLEAN}")
    print(df.groupby("issue_year")["defaulted"].agg(["size", "mean"]).round(3).to_string())
