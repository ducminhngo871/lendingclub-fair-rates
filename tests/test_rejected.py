import numpy as np
import pandas as pd
import pytest

from lc_rates import rejected


def frame(**over):
    base = dict(year=[2010, 2010], state=["CA", None], purpose=["car", "weird"], risk_score=[700.0, np.nan], dti=[5.0, -3.0],
                amount=[4000.0, 30000.0], emp_years=[0.0, 12.0])
    base.update(over)
    return pd.DataFrame(base)


def test_bins_put_edge_values_in_the_right_group():
    b = rejected.add_bins(frame(risk_score=[659.9, 660.0], dti=[39.9, 40.0], amount=[4999.0, 5000.0]))
    assert b["risk_bin"].tolist() == ["640-659", "660-679"]
    assert b["dti_bin"].tolist() == ["30-40", "40+"]
    assert b["amount_bin"].tolist() == ["<5k", "5-10k"]


def test_missing_and_invalid_values_get_their_own_bin_not_dropped():
    b = rejected.add_bins(frame(dti=[-3.0, 400.0]))
    assert b["risk_bin"].tolist()[1] == "unknown"
    assert b["dti_bin"].tolist() == ["invalid (<0)", "invalid (<0)"]
    assert b["state"].tolist() == ["CA", "??"]
    assert b["purpose"].tolist() == ["car", "other"]


def test_approval_rate_is_accepted_over_all_applications():
    cube = pd.DataFrame({"year": [2010, 2010, 2011], "n_accepted": [10, 0, 5], "n_rejected": [90, 50, 5]})
    t = rejected.approval_rate(cube, "year").set_index("year")
    assert t.loc[2010, "approval_rate"] == pytest.approx(10 / 150)
    assert t.loc[2011, "approval_rate"] == pytest.approx(0.5)
