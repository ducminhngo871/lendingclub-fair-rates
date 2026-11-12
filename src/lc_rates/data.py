"""Reading and cleaning the LendingClub files."""

from __future__ import annotations

import pandas as pd

from . import config


def parse_emp_length(s: pd.Series) -> pd.Series:
    """'< 1 year' -> 0, '3 years' -> 3, '10+ years' -> 10, missing -> NaN."""
    s = s.astype("string").str.strip()
    out = s.str.extract(r"(\d+)", expand=False).astype("Float64")
    out = out.mask((s == "< 1 year").fillna(False), 0.0)  # missing stays missing, not 0
    return out.astype("float64")


def parse_month_year(s: pd.Series) -> pd.Series:
    """'Dec-2015' -> Timestamp('2015-12-01')."""
    return pd.to_datetime(s, format="%b-%Y", errors="coerce")


def parse_term(s: pd.Series) -> pd.Series:
    """' 36 months' -> 36."""
    return pd.to_numeric(s.astype("string").str.extract(r"(\d+)", expand=False), errors="coerce")


def month_index(ts: pd.Series) -> pd.Series:
    """Months since year 0, so 'issue + term <= cutoff' is plain integer maths."""
    return ts.dt.year * 12 + ts.dt.month


def load_accepted_raw(path=None, nrows: int | None = None) -> pd.DataFrame:
    return pd.read_csv(
        path or config.ACCEPTED_RAW, usecols=config.ACCEPTED_USECOLS, nrows=nrows, low_memory=False
    )


def clean_accepted(raw: pd.DataFrame) -> pd.DataFrame:
    """Turn the raw accepted-loans table into the analysis table.

    Keeps only finished, fully matured, single-applicant loans and adds the
    `defaulted` flag (1 = Charged Off). See config.py for why each rule exists.
    """
    df = raw.copy()
    df = df[df["loan_status"].isin(config.FINISHED_STATUSES)]
    df = df[df["application_type"] == "Individual"]

    df["defaulted"] = df["loan_status"].map(config.FINISHED_STATUSES).astype("int8")
    df["term_months"] = parse_term(df["term"])
    df["issue_date"] = parse_month_year(df["issue_d"])
    df["earliest_cr_date"] = parse_month_year(df["earliest_cr_line"])
    df["emp_length_years"] = parse_emp_length(df["emp_length"])
    df["issue_year"] = df["issue_date"].dt.year
    # How many months of payments the loan actually made (used to time its cash flows).
    # Loans that never paid anything have no date; give them 1 month.
    paid = month_index(parse_month_year(df["last_pymnt_d"])) - month_index(df["issue_date"])
    df["months_paid"] = paid.clip(lower=1, upper=df["term_months"]).fillna(1)

    cutoff = config.DATA_CUTOFF_YEAR * 12 + config.DATA_CUTOFF_MONTH
    matured = month_index(df["issue_date"]) + df["term_months"] <= cutoff
    df = df[matured]

    # Collapse the three rare home-ownership labels into OTHER
    df["home_ownership"] = df["home_ownership"].where(df["home_ownership"].isin(config.HOME_OWNERSHIP[:3]), "OTHER")
    df["fico_mid"] = (df["fico_range_low"] + df["fico_range_high"]) / 2
    df["credit_history_years"] = (df["issue_date"] - df["earliest_cr_date"]).dt.days / 365.25

    keep = [
        "id", "issue_date", "issue_year", "term_months", "loan_amnt", "annual_inc", "dti",
        "fico_mid", "emp_length_years", "home_ownership", "purpose", "addr_state",
        "delinq_2yrs", "inq_last_6mths", "open_acc", "pub_rec", "revol_bal", "revol_util",
        "total_acc", "credit_history_years",
        *config.LC_VERDICT_COLUMNS,
        "funded_amnt", "total_pymnt", "total_rec_prncp", "recoveries", "months_paid", "defaulted",
    ]
    out = df[keep].reset_index(drop=True)
    out["id"] = pd.to_numeric(out["id"], errors="coerce")
    return out


def build_clean_dataset(nrows: int | None = None) -> pd.DataFrame:
    """Read the raw file, clean it, and save a compact Parquet copy."""
    df = clean_accepted(load_accepted_raw(nrows=nrows))
    if nrows is None:
        config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(config.LOANS_CLEAN, index=False)
    return df


def load_clean() -> pd.DataFrame:
    if not config.LOANS_CLEAN.exists():
        raise FileNotFoundError(
            f"{config.LOANS_CLEAN} not found. Run `python scripts/download_data.py` then `python scripts/prepare_data.py`."
        )
    return pd.read_parquet(config.LOANS_CLEAN)


def split_train_test(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Chronological split: old loans to learn from, newer loans to be judged on."""
    train = df[df["issue_year"] <= config.TRAIN_END_YEAR]
    test = df[df["issue_year"].isin(config.TEST_YEARS)]
    return train.reset_index(drop=True), test.reset_index(drop=True)


# --- Rejected applications -----------------------------------------------------
_TITLE_ALIASES = {
    "debt consolidation": "debt_consolidation",
    "credit card refinancing": "credit_card",
    "credit card": "credit_card",
    "home improvement": "home_improvement",
    "business loan": "small_business",
    "business": "small_business",
    "major purchase": "major_purchase",
    "car financing": "car",
    "car": "car",
    "medical expenses": "medical",
    "moving and relocation": "moving",
    "vacation": "vacation",
    "home buying": "house",
}


def map_title_to_purpose(title: pd.Series) -> pd.Series:
    """Rejected applications carry a free-text 'Loan Title'. Map the common ones to
    the same purpose codes the accepted loans use; everything else becomes 'other'."""
    t = title.astype("string").str.strip().str.lower()
    mapped = t.replace(_TITLE_ALIASES)
    return mapped.where(mapped.isin(config.PURPOSES), "other").astype("string")
