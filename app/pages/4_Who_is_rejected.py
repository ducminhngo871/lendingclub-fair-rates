import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # lets pages import app/common.py

import plotly.express as px
import streamlit as st

from common import approval_cube, pct
from lc_rates import rejected

st.set_page_config(page_title="Who is rejected?", page_icon="🚪", layout="wide")
st.title("Who is rejected?")
st.write("Out of about 29.9 million applications to LendingClub, only **7.6%** were approved. What separated them?")

cube = approval_cube()
years = sorted(cube["year"].unique())
c1, c2, c3 = st.columns(3)
lo, hi = c1.select_slider("Years", years, value=(2008, 2013))
purposes = c2.multiselect("Purpose", sorted(cube["purpose"].unique()), default=[])
states = c3.multiselect("State", sorted(cube["state"].unique()), default=[])

sel = cube[cube["year"].between(lo, hi)]
if purposes:
    sel = sel[sel["purpose"].isin(purposes)]
if states:
    sel = sel[sel["state"].isin(states)]
if sel.empty:
    st.warning("No applications match.")
    st.stop()

tot = sel[["n_accepted", "n_rejected"]].sum()
a, b, c = st.columns(3)
a.metric("Applications", f"{int(tot.sum()):,}")
b.metric("Approved", f"{int(tot.n_accepted):,}")
c.metric("Approval rate", pct(tot.n_accepted / tot.sum()))

order = {
    "risk_bin": ["<600", "600-639", "640-659", "660-679", "680-699", "700-719", "720-749", "750+", "unknown"],
    "dti_bin": ["invalid (<0)", "0-10", "10-20", "20-30", "30-40", "40+"],
    "amount_bin": ["<5k", "5-10k", "10-15k", "15-25k", "25k+"],
}
titles = {"risk_bin": "Approval rate by risk score", "dti_bin": "Approval rate by debt-to-income (%)",
          "amount_bin": "Approval rate by amount requested ($)"}
cols = st.columns(3)
for col, dim in zip(cols, order):
    t = rejected.approval_rate(sel, dim).set_index(dim).reindex(order[dim]).dropna(subset=["approval_rate"]).reset_index()
    fig = px.bar(t, x=dim, y="approval_rate", title=titles[dim], hover_data=["applications"])
    fig.update_layout(yaxis_tickformat=".0%", xaxis_title="", yaxis_title="", height=340)
    col.plotly_chart(fig, width="stretch")

st.subheader("What the data suggests")
st.markdown(
    """
- **Risk score ≈ 660 is a wall.** In 2008-13, almost no application below 660 was approved (0.2% for 640-659), and about a quarter or more were approved from 660 up.
- **Debt-to-income above 40% was never approved** in 2008-13, and approval falls sharply from 30%.
- These are **differences, not proof of cause**: the data cannot show *why* someone was rejected.
"""
)
st.caption(
    "Limits: rejected applications have no income field, so income cannot be compared. The risk-score scale changes "
    "after 2013 and is missing for much of 2015 and 2018, so use 2008-2013 for score thresholds. "
    "DTI values below 0 or above 100 are grouped as 'invalid'."
)
