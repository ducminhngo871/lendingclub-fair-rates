import numpy as np
import pandas as pd
import pytest

from lc_rates import features, model
from test_data import clean, raw_row


def synthetic(n=1500, seed=0) -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        fico = int(rng.integers(660, 800))
        rows.append(raw_row(fico_range_low=fico, fico_range_high=fico + 4, dti=float(rng.uniform(0, 40)),
                            annual_inc=float(rng.uniform(25000, 150000)), purpose=str(rng.choice(["car", "credit_card", "other"]))))
    df = clean(*rows)
    risk = 1 / (1 + np.exp((df["fico_mid"] - 700) / 15 - df["dti"] / 20))
    return df, (rng.random(len(df)) < risk).astype(int)


def test_logistic_gives_probabilities_and_beats_a_coin_flip():
    df, y = synthetic()
    X = features.build_features(df)
    pipe = model.make_logistic().fit(X, y)
    p = model.predict_pd(pipe, X)
    assert ((p >= 0) & (p <= 1)).all()
    assert model.probability_quality(y, p)["auc"] > 0.6


def test_lightgbm_trains_with_early_stopping():
    df, y = synthetic()
    X = features.build_features(df)
    half = len(X) // 2
    m = model.train_lgbm(X[:half], y[:half], X[half:], y[half:], params={"n_estimators": 50, "min_child_samples": 20})
    p = model.predict_pd(m, X)
    assert p.shape == (len(X),) and p.std() > 0


def test_grade_scores_are_ordered_safest_first():
    assert model.grade_to_score(pd.Series(["A", "G"])).tolist() == [0, 6]
    assert model.sub_grade_to_score(pd.Series(["A1", "A5", "B1", "G5"])).tolist() == [0, 4, 5, 34]


def test_decile_table_is_balanced_and_monotone_for_a_good_score():
    rng = np.random.default_rng(0)
    p = rng.random(5000)
    y = (rng.random(5000) < p).astype(int)
    t = model.decile_table(y, p)
    assert len(t) == 10 and t["loans"].nunique() == 1
    assert t["actual_default_rate"].is_monotonic_increasing


def test_disagreement_groups_are_disjoint_and_labelled():
    rng = np.random.default_rng(0)
    n = 4000
    test = pd.DataFrame({"sub_grade": rng.choice(["A1", "C3", "E5", "G1"], n), "int_rate": rng.uniform(6, 25, n),
                         "defaulted": rng.integers(0, 2, n)})
    t = model.disagreement_table(test, rng.random(n))
    assert len(t) == 4 and (t["loans"] > 0).all()
    assert t["loans"].sum() <= n


def test_probability_quality_flags_miscalibration():
    y = np.array([0, 0, 0, 1])
    assert model.probability_quality(y, np.full(4, 0.9))["mean_predicted"] == pytest.approx(0.9)
