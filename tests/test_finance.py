import numpy as np
import pandas as pd
import pytest

from lc_rates import finance


def test_expected_loss_matches_the_project_brief_example():
    # lend 10,000; 10% chance of default; lose 60% of the money when it happens -> expect to lose 600
    assert finance.expected_loss(0.10, 0.60, 10_000) == pytest.approx(600)


def test_realised_return_includes_recoveries_already_in_total_payment():
    df = pd.DataFrame({"funded_amnt": [1000.0, 1000.0], "total_pymnt": [1100.0, 400.0]})
    assert finance.realised_return(df).tolist() == pytest.approx([0.10, -0.60])


def test_loss_given_default_counts_repaid_principal_and_recoveries():
    df = pd.DataFrame({"defaulted": [1, 1, 0], "funded_amnt": [1000.0] * 3, "total_rec_prncp": [400.0, 0.0, 1000.0], "recoveries": [100.0, 0.0, 0.0]})
    assert finance.loss_given_default(df) == pytest.approx(1 - (0.5 + 0.0) / 2)


def test_fair_rate_rises_with_risk_and_with_required_margin():
    low, high = finance.fair_rate(0.05, 36, 0.55), finance.fair_rate(0.30, 36, 0.55)
    assert high > low
    assert finance.fair_rate(0.1, 36, 0.55, margin=0.05) > finance.fair_rate(0.1, 36, 0.55, margin=0.0)
    assert finance.fair_rate(0.0, 36, 0.55, risk_free=0.02, margin=0.02) == pytest.approx(0.04)


def test_pool_irr_exact_on_a_one_month_loan():
    one = pd.DataFrame({"term_months": [12], "months_paid": [1], "total_pymnt": [112.0], "funded_amnt": [100.0]})
    assert finance.pool_irr(one) == pytest.approx(1.12**12 - 1)


def test_pool_irr_is_negative_when_money_is_lost_and_zero_at_breakeven():
    lost = pd.DataFrame({"term_months": [36], "months_paid": [10], "total_pymnt": [600.0], "funded_amnt": [1000.0]})
    even = pd.DataFrame({"term_months": [36], "months_paid": [36], "total_pymnt": [1000.0], "funded_amnt": [1000.0]})
    assert finance.pool_irr(lost) < 0
    assert finance.pool_irr(even) == pytest.approx(0.0, abs=1e-9)


def test_pool_cashflow_lends_once_and_receives_total_payment():
    df = pd.DataFrame({"term_months": [36, 36], "months_paid": [3, 36], "total_pymnt": [300.0, 1200.0], "funded_amnt": [1000.0, 1000.0]})
    cf = finance.pool_cashflows(df)
    assert cf[0] == -2000 and cf.sum() == pytest.approx(-2000 + 1500)


def make_loans(n=2000, seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    grade = rng.choice(list("ABCDE"), n)
    risk = pd.Series(grade).map(dict(zip("ABCDE", [0.05, 0.1, 0.15, 0.2, 0.3]))).to_numpy()
    d = (rng.random(n) < risk).astype(int)
    return pd.DataFrame({"grade": grade, "int_rate": 7 + 3 * pd.Series(grade).map(dict(zip("ABCDE", range(5)))).to_numpy(),
                         "defaulted": d, "funded_amnt": 1000.0, "total_pymnt": np.where(d, 400.0, 1150.0),
                         "term_months": 36, "months_paid": np.where(d, 12, 30)})


def test_strategies_pick_the_right_loans():
    df = make_loans()
    pd_ = df["grade"].map(dict(zip("ABCDE", [0.05, 0.1, 0.15, 0.2, 0.3]))).to_numpy() + np.random.default_rng(1).random(len(df)) * 0.01
    masks = finance.strategy_masks(df, pd_, share=0.2, pred_return=-pd_)
    assert masks["1. Fund every loan"].all()
    assert set(df[masks["2. Only grade A and B"]]["grade"]) == {"A", "B"}
    per_grade = df[masks["4. Safest 20% per grade (my model)"]].groupby("grade").size() / df.groupby("grade").size()
    assert per_grade.between(0.15, 0.25).all()
    assert len(masks) == 5


def test_safer_pool_earns_more_in_a_world_where_risk_is_priced_wrong():
    df = make_loans()
    s = finance.summarise_strategy(df, df["grade"] == "A", n_boot=0)
    t = finance.summarise_strategy(df, df["grade"] == "E", n_boot=0)
    assert s["default_rate"] < t["default_rate"] and s["annual_return"] > t["annual_return"]
