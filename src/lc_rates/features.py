"""Turn the clean table (or a single applicant typed into the app) into model inputs.

The same function is used for training and for the app, so a borrower scored on the
web page is scored exactly the way the training data was.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

NUMERIC_FEATURES = [
    "loan_amnt", "term_months", "log_annual_inc", "dti", "fico_mid", "emp_length_years",
    "revol_util", "log_revol_bal", "delinq_2yrs", "inq_last_6mths", "pub_rec",
    "open_acc", "total_acc", "credit_history_years", "loan_to_income",
]
CATEGORICAL_FEATURES = ["purpose", "home_ownership"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Raw columns an applicant must supply (also the fields on the app's form)
RAW_INPUTS = [
    "loan_amnt", "term_months", "annual_inc", "dti", "fico_mid", "emp_length_years",
    "revol_util", "revol_bal", "delinq_2yrs", "inq_last_6mths", "pub_rec",
    "open_acc", "total_acc", "credit_history_years", "purpose", "home_ownership",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return the model input table. Never touches grade, interest rate or outcomes."""
    out = pd.DataFrame(index=df.index)
    income = df["annual_inc"].clip(lower=1)
    out["loan_amnt"] = df["loan_amnt"]
    out["term_months"] = df["term_months"]
    out["log_annual_inc"] = np.log(income)
    out["dti"] = df["dti"].clip(0, 60)
    out["fico_mid"] = df["fico_mid"]
    out["emp_length_years"] = df["emp_length_years"]
    out["revol_util"] = df["revol_util"].clip(0, 150)
    out["log_revol_bal"] = np.log1p(df["revol_bal"].clip(lower=0))
    out["delinq_2yrs"] = df["delinq_2yrs"]
    out["inq_last_6mths"] = df["inq_last_6mths"]
    out["pub_rec"] = df["pub_rec"]
    out["open_acc"] = df["open_acc"]
    out["total_acc"] = df["total_acc"]
    out["credit_history_years"] = df["credit_history_years"]
    # Loan size relative to income, built WITHOUT the interest rate: the monthly
    # `installment` column would leak LendingClub's price into the model.
    out["loan_to_income"] = (df["loan_amnt"] / income).clip(upper=2)

    out["purpose"] = pd.Categorical(df["purpose"], categories=config.PURPOSES)
    out["home_ownership"] = pd.Categorical(df["home_ownership"], categories=config.HOME_OWNERSHIP)
    return out[FEATURE_COLUMNS].astype({c: "float64" for c in NUMERIC_FEATURES})


def applicant_frame(**fields) -> pd.DataFrame:
    """One-row frame from keyword fields, e.g. from the Streamlit form."""
    missing = [c for c in RAW_INPUTS if c not in fields]
    if missing:
        raise ValueError(f"missing applicant fields: {missing}")
    return pd.DataFrame([{c: fields[c] for c in RAW_INPUTS}])
