"""Home page. Run with:  streamlit run app/streamlit_app.py"""

import streamlit as st

from common import pct, result

st.set_page_config(page_title="Is LendingClub fair?", page_icon="💳", layout="wide")

st.title("Does LendingClub charge fair interest?")
st.write(
    "I used about **2 million real loans** (LendingClub, USA, 2007-2018) to test whether borrowers "
    "were charged interest that matches their real risk of not paying back. I built my own "
    "borrower-scoring machine, compared it with LendingClub's A-G grades, worked out a 'fair' rate, "
    "and tested investing strategies on loans my models had never seen (2014-15)."
)

auc = result("auc_comparison.csv").set_index("score")["auc"]
strat = result("investment_strategies.csv")
inc = result("incremental_information.csv").set_index("inputs")["cv_auc"]

c1, c2, c3 = st.columns(3)
c1.metric("My best model's ranking power (AUC)", f"{auc['LightGBM (mine)']:.3f}",
          f"{auc['LightGBM (mine)'] - auc['LendingClub sub-grade A1-G5']:+.3f} vs LendingClub sub-grade", delta_color="off")
c2.metric("My model + LendingClub together (AUC)", f"{inc['Both together']:.3f}",
          f"{inc['Both together'] - inc['LendingClub sub-grade only']:+.3f} vs LendingClub alone")
best, base = strat.iloc[-1], strat.iloc[0]
c3.metric("Best strategy, yearly return", pct(best["annual_return"]),
          f"{(best['annual_return'] - base['annual_return']) * 100:+.1f} pts vs funding every loan")

st.markdown(
    """
**Explore the four pages in the sidebar:**

1. **Loan pricing** - type in a borrower and see their default risk, the grade my machine gives, and a fair interest rate.
2. **Investor sandbox** - pick loans with your own rules and see what that would really have earned.
3. **My machine vs LendingClub** - who predicts defaults better, and where they disagree.
4. **Who is rejected?** - what separates the 7.6% of applications that were approved from the rest.

*AUC measures how well a score separates people who repay from people who default (0.5 = coin flip, 1.0 = perfect).
Everything is measured on loans issued in 2014-15 that were finished by the end of 2018; models were trained
only on loans from 2007-2013.*
"""
)
st.caption("Educational project, not financial advice. Data: LendingClub public dataset (Kaggle).")
