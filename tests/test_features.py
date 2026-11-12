import numpy as np
import pandas as pd

from lc_rates import config, features
from test_data import clean, raw_row


def table() -> pd.DataFrame:
    return clean(raw_row(), raw_row(annual_inc=0, dti=999, revol_util=500, purpose="car"))


def test_features_never_contain_lendingclub_verdict_or_outcomes():
    banned = set(config.LC_VERDICT_COLUMNS) | set(config.OUTCOME_COLUMNS) | {"installment", "defaulted", "months_paid"}
    assert not banned & set(features.FEATURE_COLUMNS)
    assert not any("int_rate" in c or "grade" in c for c in features.FEATURE_COLUMNS)


def test_build_features_shape_and_clipping():
    X = features.build_features(table())
    assert list(X.columns) == features.FEATURE_COLUMNS
    assert X["dti"].max() <= 60 and X["revol_util"].max() <= 150
    assert np.isfinite(X["log_annual_inc"]).all()  # zero income must not give -inf
    assert X["loan_to_income"].max() <= 2


def test_categories_fixed_so_training_and_app_agree():
    X = features.build_features(table())
    assert list(X["purpose"].cat.categories) == config.PURPOSES
    assert list(X["home_ownership"].cat.categories) == config.HOME_OWNERSHIP


def test_applicant_frame_requires_every_field():
    import pytest

    with pytest.raises(ValueError):
        features.applicant_frame(loan_amnt=1000)
