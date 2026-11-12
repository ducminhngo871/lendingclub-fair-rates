import numpy as np
import pandas as pd
import pytest

from lc_rates import config, data


def raw_row(**over) -> dict:
    row = dict(
        id="1", loan_amnt=10000, term=" 36 months", emp_length="10+ years", home_ownership="RENT", annual_inc=60000,
        purpose="credit_card", addr_state="CA", dti=15.0, delinq_2yrs=0, earliest_cr_line="Jan-2000", fico_range_low=690,
        fico_range_high=694, inq_last_6mths=1, open_acc=8, pub_rec=0, revol_bal=5000, revol_util=40.0, total_acc=20,
        issue_d="Jun-2014", application_type="Individual", grade="C", sub_grade="C2", int_rate=13.5, loan_status="Fully Paid",
        funded_amnt=10000, total_pymnt=11500.0, total_rec_prncp=10000.0, recoveries=0.0, last_pymnt_d="Jun-2017",
    )
    row.update(over)
    return row


def clean(*rows) -> pd.DataFrame:
    return data.clean_accepted(pd.DataFrame(list(rows)))


def test_parse_helpers():
    assert data.parse_emp_length(pd.Series(["< 1 year", "1 year", "7 years", "10+ years", None])).tolist()[:4] == [0, 1, 7, 10]
    assert np.isnan(data.parse_emp_length(pd.Series([None])).iloc[0])
    assert data.parse_term(pd.Series([" 36 months", " 60 months"])).tolist() == [36, 60]
    assert data.parse_month_year(pd.Series(["Dec-2015"])).iloc[0] == pd.Timestamp("2015-12-01")


def test_only_finished_loans_kept_and_default_flag():
    out = clean(raw_row(), raw_row(loan_status="Charged Off"), raw_row(loan_status="Current"), raw_row(loan_status="Late (31-120 days)"))
    assert sorted(out["defaulted"]) == [0, 1]


def test_joint_applications_dropped():
    assert len(clean(raw_row(), raw_row(application_type="Joint App"))) == 1


@pytest.mark.parametrize(
    "term,issue,kept",
    [(" 36 months", "Dec-2015", True), (" 36 months", "Jan-2016", False), (" 60 months", "Dec-2013", True), (" 60 months", "Jan-2014", False)],
)
def test_maturity_rule_boundaries(term, issue, kept):
    """A loan counts only if its last payment is due by Dec 2018 (the data cutoff)."""
    assert (len(clean(raw_row(term=term, issue_d=issue))) == 1) is kept


def test_months_paid_is_clipped_to_term():
    out = clean(raw_row(last_pymnt_d="Jan-2030"), raw_row(last_pymnt_d=None, loan_status="Charged Off"))
    assert out["months_paid"].between(1, 36).all()


def test_rare_home_ownership_collapses_to_other():
    out = clean(raw_row(home_ownership="ANY"), raw_row(home_ownership="OWN"))
    assert set(out["home_ownership"]) == {"OTHER", "OWN"}


def test_no_outcome_leak_columns_in_applicant_set():
    assert not set(config.APPLICANT_COLUMNS) & set(config.OUTCOME_COLUMNS)
    assert not set(config.APPLICANT_COLUMNS) & set(config.LC_VERDICT_COLUMNS)
    assert "installment" not in config.ACCEPTED_USECOLS


def test_time_split_never_trains_on_the_future():
    df = pd.DataFrame({"issue_year": [2008, 2012, 2013, 2014, 2015, 2016], "x": range(6)})
    train, test = data.split_train_test(df)
    assert train["issue_year"].max() <= config.TRAIN_END_YEAR < test["issue_year"].min()
    assert set(test["issue_year"]) == {2014, 2015}


def test_title_mapping():
    t = pd.Series(["Debt consolidation", "credit_card", "Business Loan", "Some free text", None])
    assert data.map_title_to_purpose(t).tolist() == ["debt_consolidation", "credit_card", "small_business", "other", "other"]
