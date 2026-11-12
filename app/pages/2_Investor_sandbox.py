import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # lets pages import app/common.py

import plotly.graph_objects as go
import streamlit as st

from common import pct, result, test_loans
from lc_rates import config, finance, model

st.set_page_config(page_title="Investor sandbox", page_icon="📈", layout="wide")
st.title("Investor sandbox")
st.write("Pretend you funded loans in 2014-15 using your own rule. The app shows what you would really have earned "
         "after the borrowers who defaulted, using the actual outcomes.")

df = test_loans()
baseline = finance.pool_irr(df)

RANKS = {
    "Highest predicted return (my return model)": ("pred_return", False),
    "Safest according to my default model": ("model_pd", True),
    "Highest interest rate": ("int_rate", False),
    "Best LendingClub sub-grade": ("sub_score", True),
}
df = df.assign(sub_score=model.sub_grade_to_score(df["sub_grade"].astype(str)).to_numpy())

c1, c2, c3 = st.columns(3)
grades = c1.multiselect("Grades you allow", config.GRADES, default=config.GRADES)
rank_name = c2.selectbox("Pick loans that are...", list(RANKS))
share = c3.slider("Fund the top ... % of those loans", 1, 100, 10)
within = st.checkbox("Rank within each grade (instead of across all loans)")

if not grades:
    st.warning("Select at least one grade.")
    st.stop()

col, low_is_good = RANKS[rank_name]
pool = df[df["grade"].astype(str).isin(grades)]
ranks = (pool.groupby("grade", observed=True)[col].rank(pct=True, method="first") if within
         else pool[col].rank(pct=True, method="first"))
chosen = pool[ranks <= share / 100] if low_is_good else pool[ranks > 1 - share / 100]

if len(chosen) < 500:
    st.warning("Fewer than 500 loans selected: results would be unreliable. Widen your rule.")
    st.stop()

ret = finance.pool_irr(chosen)
m = st.columns(4)
m[0].metric("Yearly return", pct(ret), f"{(ret - baseline) * 100:+.1f} pts vs funding every loan")
m[1].metric("Loans funded", f"{len(chosen):,}")
m[2].metric("Borrowers who defaulted", pct(chosen["defaulted"].mean()))
m[3].metric("Average interest rate", f"{chosen['int_rate'].mean():.1f}%")

if st.checkbox("Show 95% uncertainty range (takes a few seconds)"):
    lo, hi = finance.bootstrap_irr_ci(chosen, 60)
    st.write(f"Likely range for the yearly return: **{pct(lo)} to {pct(hi)}**")

st.divider()
st.subheader("The five strategies tested in the report")
s = result("investment_strategies.csv")
st.dataframe(
    s.assign(annual_return=s["annual_return"].map(pct), default_rate=s["default_rate"].map(pct),
             mean_interest_rate=s["mean_interest_rate"].map(pct),
             range_95=[f"{pct(a)} to {pct(b)}" for a, b in zip(s["ci95_low"], s["ci95_high"])])
    [["strategy", "loans", "annual_return", "range_95", "default_rate", "mean_interest_rate"]],
    hide_index=True, width="stretch",
)

sw = result("investment_share_sweep.csv")
fig = go.Figure()
fig.add_scatter(x=sw["share_of_loans_funded"] * 100, y=sw["test_2014_15_return"], name="Test loans 2014-15", mode="lines+markers")
fig.add_scatter(x=sw["share_of_loans_funded"] * 100, y=sw["validation_2013_return"], name="Held-out 2013 loans", mode="lines+markers")
fig.update_layout(title="The pickier the investor, the higher the return (return-model ranking)",
                  xaxis_title="% of loans funded", yaxis_title="yearly return", yaxis_tickformat=".0%", height=380)
st.plotly_chart(fig, width="stretch")
st.caption(
    "Return = the yearly interest rate at which the money lent and the money received are worth the same (IRR), "
    "assuming each loan's repayments arrive evenly until its last payment. Past results; fees and taxes are ignored; "
    "a pickier rule means fewer loans and less diversification."
)
