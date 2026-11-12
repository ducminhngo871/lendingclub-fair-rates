"""Money maths: realised returns, expected loss, fair interest rate, investing strategies."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from . import config


def realised_return(df: pd.DataFrame) -> pd.Series:
    """(cash received - cash lent) / cash lent, over the life of the loan.

    `total_pymnt` already includes recoveries after a charge-off. Platform fees
    and the investor's tax are ignored.
    """
    return (df["total_pymnt"] - df["funded_amnt"]) / df["funded_amnt"]


def pool_cashflows(df: pd.DataFrame, weights: np.ndarray | None = None) -> np.ndarray:
    """Monthly cash flow of a pool of loans: month 0 = money lent (negative), months 1.. = money received.

    The data has only the *total* repaid and the month of the last payment, so each loan's
    repayments are assumed to arrive in equal monthly amounts until that last payment.
    """
    w = np.ones(len(df)) if weights is None else np.asarray(weights, dtype=float)
    months = df["months_paid"].to_numpy().astype(int)
    per_month = df["total_pymnt"].to_numpy() / months * w
    horizon = int(df["term_months"].max())
    # each loan pays `per_month` in months 1..months: add at 1, remove after `months`
    ends = np.bincount(months + 1, weights=per_month, minlength=horizon + 2)[: horizon + 2]
    flow = np.cumsum(np.concatenate([[0.0, per_month.sum()], np.zeros(horizon)])[: horizon + 2] - ends)
    cf = flow[: horizon + 1].copy()
    cf[0] = -(df["funded_amnt"].to_numpy() * w).sum()
    return cf


def annual_irr(cashflows: np.ndarray) -> float:
    """Yearly internal rate of return of monthly cash flows: the interest rate at which
    the money lent and the money received are worth the same."""
    t = np.arange(len(cashflows))

    def npv(i: float) -> float:
        return float((cashflows / (1 + i) ** t).sum())

    lo, hi = -0.5, 1.0
    if npv(lo) * npv(hi) > 0:
        return float("nan")
    return float((1 + brentq(npv, lo, hi)) ** 12 - 1)


def pool_irr(df: pd.DataFrame, weights: np.ndarray | None = None) -> float:
    """Yearly return a lender earned on this group of loans, after defaults."""
    return annual_irr(pool_cashflows(df, weights))


def bootstrap_irr_ci(df: pd.DataFrame, n_boot: int = 200, seed: int = 0) -> tuple[float, float]:
    """95% range for pool_irr by resampling loans (Poisson bootstrap: fast on large groups)."""
    rng = np.random.default_rng(seed)
    draws = [pool_irr(df, rng.poisson(1.0, len(df))) for _ in range(n_boot)]
    lo, hi = np.nanpercentile(draws, [2.5, 97.5])
    return float(lo), float(hi)


def loss_given_default(df: pd.DataFrame) -> float:
    """Share of the *funded amount* not recovered, averaged over charged-off loans.

    Principal already repaid before the default counts as recovered.
    """
    co = df[df["defaulted"] == 1]
    recovered = (co["total_rec_prncp"] + co["recoveries"]) / co["funded_amnt"]
    return float(1 - recovered.clip(0, 1).mean())


def expected_loss(pd_: np.ndarray | pd.Series, lgd: float, exposure: float | np.ndarray = 1.0):
    """Expected loss = probability of default x loss given default x amount lent."""
    return np.asarray(pd_) * lgd * exposure


def fair_rate(
    pd_,
    term_months,
    lgd: float,
    risk_free: float = config.RISK_FREE_RATE,
    margin: float = config.REQUIRED_MARGIN,
    avg_balance_ratio: float = config.AVG_BALANCE_RATIO,
):
    """Interest rate (per year) that exactly pays for the borrower's risk.

        fair rate = risk-free + required margin + yearly expected loss

    Expected loss (as a share of the amount lent) is spread over the loan's life and
    divided by the average share of principal still outstanding, because interest is
    only charged on the balance that has not been repaid yet.
    """
    years = np.asarray(term_months, dtype=float) / 12
    yearly_loss = expected_loss(pd_, lgd) / (years * avg_balance_ratio)
    return risk_free + margin + yearly_loss


def pricing_gap(df: pd.DataFrame, fair: np.ndarray) -> pd.Series:
    """Actual rate minus fair rate, in rate points. Positive = borrower charged too much."""
    return df["int_rate"] / 100 - pd.Series(fair, index=df.index)


# --- Investing strategies -------------------------------------------------------
def _top_share(df: pd.DataFrame, col: str, share: float, ascending: bool, by: str | None = None) -> pd.Series:
    ranks = df.groupby(by)[col].rank(pct=True, method="first") if by else df[col].rank(pct=True, method="first")
    return ranks <= share if ascending else ranks > 1 - share


BEST_RETURN_SHARE = 0.10  # fixed in advance: a pool of ~44,000 loans stays diversified


def strategy_masks(
    test: pd.DataFrame, model_pd: np.ndarray, share: float = 0.2, pred_return: np.ndarray | None = None
) -> dict[str, pd.Series]:
    """The ways of picking loans compared in the project (the 5th needs a return model)."""
    t = test.assign(model_pd=model_pd)
    out = {
        "1. Fund every loan": pd.Series(True, index=t.index),
        "2. Only grade A and B": t["grade"].isin(["A", "B"]),
        f"3. Highest-rate {share:.0%} of loans": _top_share(t, "int_rate", share, ascending=False),
        f"4. Safest {share:.0%} per grade (my model)": _top_share(t, "model_pd", share, ascending=True, by="grade"),
    }
    if pred_return is not None:
        t["pred_return"] = pred_return
        out[f"5. Best {BEST_RETURN_SHARE:.0%} by predicted return"] = _top_share(t, "pred_return", BEST_RETURN_SHARE, ascending=False)
    return out


def summarise_strategy(df: pd.DataFrame, mask: pd.Series, n_boot: int = 100) -> dict[str, float]:
    sel = df[mask]
    lo, hi = bootstrap_irr_ci(sel, n_boot) if n_boot else (np.nan, np.nan)
    return {
        "loans": int(len(sel)),
        "annual_return": pool_irr(sel),
        "ci95_low": lo,
        "ci95_high": hi,
        "default_rate": float(sel["defaulted"].mean()),
        "mean_interest_rate": float(sel["int_rate"].mean() / 100),
        "loss_per_loan_std": float(realised_return(sel).std()),
    }


def compare_strategies(
    test: pd.DataFrame, model_pd: np.ndarray, share: float = 0.2, n_boot: int = 100, pred_return: np.ndarray | None = None
) -> pd.DataFrame:
    masks = strategy_masks(test, model_pd, share, pred_return)
    rows = [{"strategy": name, **summarise_strategy(test, m, n_boot)} for name, m in masks.items()]
    return pd.DataFrame(rows)


def grade_economics(df: pd.DataFrame, lgd: float | None = None) -> pd.DataFrame:
    """For each grade: does the interest earned pay for the money lost to defaults?"""
    lgd = loss_given_default(df) if lgd is None else lgd
    rows = []
    for grade, g in df.groupby("grade"):
        rows.append(
            {
                "grade": grade,
                "loans": len(g),
                "default_rate": g["defaulted"].mean(),
                "mean_interest_rate": g["int_rate"].mean() / 100,
                "realised_annual_return": pool_irr(g),
                "expected_loss_share": g["defaulted"].mean() * lgd,
            }
        )
    t = pd.DataFrame(rows)
    t["return_vs_risk_free"] = t["realised_annual_return"] - config.RISK_FREE_RATE
    return t
