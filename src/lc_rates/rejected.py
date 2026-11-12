"""Approved vs rejected applications.

The rejected file has 27.6M rows, so it is read in chunks and squashed into small
count tables ("cubes") of how many applications fell into each bin. Approval rate in
any bin is then accepted / (accepted + rejected).

Caveats the analysis must carry:
  * The rejected file has NO income column, so income cannot be compared.
  * `Risk_Score` is missing for much of 2015 and 2018, and its scale changes around
    2013 (values up to 990), so score thresholds are only reliable for 2008-2013.
  * `Debt-To-Income Ratio` is negative or absurd for some rows; those go in an
    'invalid' bin rather than being silently dropped.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config, data

RISK_EDGES = [-np.inf, 600, 640, 660, 680, 700, 720, 750, np.inf]
RISK_LABELS = ["<600", "600-639", "640-659", "660-679", "680-699", "700-719", "720-749", "750+"]
DTI_EDGES = [-np.inf, 0, 10, 20, 30, 40, np.inf]
DTI_LABELS = ["invalid (<0)", "0-10", "10-20", "20-30", "30-40", "40+"]
AMOUNT_EDGES = [-np.inf, 5000, 10000, 15000, 25000, np.inf]
AMOUNT_LABELS = ["<5k", "5-10k", "10-15k", "15-25k", "25k+"]
EMP_EDGES = [-np.inf, 1, 5, 10, np.inf]
EMP_LABELS = ["<1 yr", "1-4 yrs", "5-9 yrs", "10+ yrs"]
PURPOSE_GROUPS = ["debt_consolidation", "credit_card", "home_improvement", "small_business", "car", "other"]

MAIN_DIMS = ["year", "state", "purpose", "risk_bin", "dti_bin", "amount_bin"]
PROFILE_DIMS = ["year", "risk_bin", "dti_bin", "amount_bin", "emp_bin"]


def _cut(x: pd.Series, edges, labels, right=False, missing="unknown") -> pd.Series:
    out = pd.cut(x, edges, labels=labels, right=right).astype("string")
    return out.fillna(missing)


def add_bins(df: pd.DataFrame) -> pd.DataFrame:
    """Expects columns year, state, purpose, risk_score, dti, amount, emp_years."""
    out = df.copy()
    out["risk_bin"] = _cut(out["risk_score"], RISK_EDGES, RISK_LABELS)
    out["dti_bin"] = _cut(out["dti"], DTI_EDGES, DTI_LABELS)
    out.loc[out["dti"] > 100, "dti_bin"] = "invalid (<0)"  # absurd values are treated as invalid too
    out["amount_bin"] = _cut(out["amount"], AMOUNT_EDGES, AMOUNT_LABELS)
    out["emp_bin"] = _cut(out["emp_years"], EMP_EDGES, EMP_LABELS)
    out["purpose"] = out["purpose"].where(out["purpose"].isin(PURPOSE_GROUPS), "other")
    out["state"] = out["state"].fillna("??")
    return out


def standardise_rejected(chunk: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": pd.to_numeric(chunk["Application Date"].str[:4], errors="coerce"),
            "state": chunk["State"],
            "purpose": data.map_title_to_purpose(chunk["Loan Title"]),
            "risk_score": chunk["Risk_Score"],
            "dti": pd.to_numeric(chunk["Debt-To-Income Ratio"].astype("string").str.rstrip("%"), errors="coerce"),
            "amount": chunk["Amount Requested"],
            "emp_years": data.parse_emp_length(chunk["Employment Length"]),
        }
    ).dropna(subset=["year"])


def standardise_accepted(raw: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": data.parse_month_year(raw["issue_d"]).dt.year,
            "state": raw["addr_state"],
            "purpose": raw["purpose"],
            "risk_score": (raw["fico_range_low"] + raw["fico_range_high"]) / 2,
            "dti": raw["dti"],
            "amount": raw["loan_amnt"],
            "emp_years": data.parse_emp_length(raw["emp_length"]),
        }
    ).dropna(subset=["year"])


def _count(df: pd.DataFrame, dims: list[str], name: str) -> pd.DataFrame:
    return df.groupby(dims, observed=True).size().rename(name).reset_index()


def _merge_counts(parts: list[pd.DataFrame], dims: list[str], name: str) -> pd.DataFrame:
    return pd.concat(parts).groupby(dims, observed=True)[name].sum().reset_index()


def build_cubes(chunksize: int = 2_000_000, max_chunks: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (main cube, profile cube) with columns n_accepted and n_rejected."""
    cols = ["Application Date", "State", "Loan Title", "Risk_Score", "Debt-To-Income Ratio", "Amount Requested", "Employment Length"]
    rej_main, rej_prof = [], []
    for i, chunk in enumerate(pd.read_csv(config.REJECTED_RAW, usecols=cols, chunksize=chunksize)):
        if max_chunks is not None and i >= max_chunks:
            break
        b = add_bins(standardise_rejected(chunk))
        b["year"] = b["year"].astype(int)
        rej_main.append(_count(b, MAIN_DIMS, "n_rejected"))
        rej_prof.append(_count(b, PROFILE_DIMS, "n_rejected"))

    acc_cols = ["issue_d", "addr_state", "purpose", "fico_range_low", "fico_range_high", "dti", "loan_amnt", "emp_length"]
    acc = add_bins(standardise_accepted(pd.read_csv(config.ACCEPTED_RAW, usecols=acc_cols, low_memory=False)))
    acc["year"] = acc["year"].astype(int)

    out = []
    for dims, rej in ((MAIN_DIMS, rej_main), (PROFILE_DIMS, rej_prof)):
        r = _merge_counts(rej, dims, "n_rejected")
        a = _count(acc, dims, "n_accepted")
        m = a.merge(r, on=dims, how="outer").fillna({"n_accepted": 0, "n_rejected": 0})
        m[["n_accepted", "n_rejected"]] = m[["n_accepted", "n_rejected"]].astype("int64")
        for c in dims:
            if c != "year":
                m[c] = m[c].astype("category")
        out.append(m)
    return out[0], out[1]


def approval_rate(cube: pd.DataFrame, by: str | list[str]) -> pd.DataFrame:
    t = cube.groupby(by, observed=True)[["n_accepted", "n_rejected"]].sum()
    t["applications"] = t["n_accepted"] + t["n_rejected"]
    t["approval_rate"] = t["n_accepted"] / t["applications"]
    return t.reset_index()
