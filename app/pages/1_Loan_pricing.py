import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # lets pages import app/common.py

import pandas as pd
import plotly.express as px
import streamlit as st

from common import models, pct
from lc_rates import config, features, finance

st.set_page_config(page_title="Loan pricing", page_icon="💳", layout="wide")
st.title("Loan pricing")
st.write("Describe a borrower. My machine estimates the chance they will not repay, and the interest rate that would fairly pay for that risk.")

logit, lgbm, meta = models()

with st.form("borrower"):
    a, b, c = st.columns(3)
    loan_amnt = a.number_input("Loan amount ($)", 1000, 40000, 10000, 500)
    term = a.selectbox("Term (months)", [36, 60])
    purpose = a.selectbox("Purpose", config.PURPOSES, index=0)
    annual_inc = b.number_input("Yearly income ($)", 10000, 500000, 60000, 1000)
    dti = b.slider("Debt-to-income (%)", 0.0, 60.0, 15.0, 0.5, help="Share of income already used to repay other debts")
    home = b.selectbox("Home", config.HOME_OWNERSHIP)
    fico = c.slider("Credit score (FICO)", 600, 850, 690, 5)
    emp = c.slider("Years in current job", 0, 10, 5)
    hist = c.slider("Credit history (years)", 1, 40, 15)
    d, e, f = st.columns(3)
    revol_util = d.slider("Credit-card usage (%)", 0, 120, 45)
    revol_bal = d.number_input("Credit-card balance ($)", 0, 200000, 12000, 500)
    delinq = e.number_input("Late payments, last 2 years", 0, 20, 0)
    inq = e.number_input("Credit checks, last 6 months", 0, 10, 1)
    pub_rec = f.number_input("Public records (bankruptcies etc.)", 0, 10, 0)
    open_acc = f.number_input("Open credit accounts", 0, 40, 10)
    total_acc = f.number_input("Total credit accounts ever", 1, 80, 25)
    with st.expander("Fair-rate assumptions (you can change these)"):
        rf = st.slider("Risk-free return (%)", 0.0, 6.0, config.RISK_FREE_RATE * 100, 0.25) / 100
        margin = st.slider("Extra return a lender should earn (%)", 0.0, 6.0, config.REQUIRED_MARGIN * 100, 0.25) / 100
    go = st.form_submit_button("Price this loan", type="primary")

person = features.applicant_frame(
    loan_amnt=loan_amnt, term_months=term, annual_inc=annual_inc, dti=dti, fico_mid=fico, emp_length_years=emp,
    revol_util=revol_util, revol_bal=revol_bal, delinq_2yrs=delinq, inq_last_6mths=inq, pub_rec=pub_rec,
    open_acc=open_acc, total_acc=total_acc, credit_history_years=hist, purpose=purpose, home_ownership=home,
)
X = features.build_features(person)
pd_lgbm = float(lgbm.predict_proba(X)[0, 1])
pd_logit = float(logit.predict_proba(X)[0, 1])

grade_pd = pd.Series(meta["grade_mean_model_pd"])
my_grade = (grade_pd - pd_lgbm).abs().idxmin()
lc_rate = meta["grade_mean_interest_rate"][my_grade]
fair = float(finance.fair_rate(pd_lgbm, term, meta["lgd"], rf, margin))
exp_loss = float(finance.expected_loss(pd_lgbm, meta["lgd"], loan_amnt))

m1, m2, m3, m4 = st.columns(4)
m1.metric("Chance of default", pct(pd_lgbm), f"logistic model: {pct(pd_logit)}", delta_color="off")
m2.metric("Grade my machine gives", my_grade)
m3.metric("Typical LendingClub rate for that grade", pct(lc_rate))
m4.metric("Fair rate (my estimate)", pct(fair))
st.write(f"**Expected loss on this loan:** ${exp_loss:,.0f} of the ${loan_amnt:,} lent "
         f"(= {pct(pd_lgbm)} chance of default × {pct(meta['lgd'], 0)} of the money lost when it happens).")

gap = lc_rate - fair
if gap > 0.01:
    st.info(f"A grade-{my_grade} borrower is typically charged about **{gap * 100:.1f} points more** than this simple fair rate. "
            "That gap is not all profit: the fair rate ignores interest lost on early defaults, so use it for comparing borrowers, not as an exact price.")
elif gap < -0.01:
    st.warning(f"A grade-{my_grade} borrower is typically charged about **{-gap * 100:.1f} points less** than the fair rate: lenders would be under-paid for this risk.")
else:
    st.success("The typical rate for this grade is close to the fair rate.")

contrib = lgbm.predict(X, pred_contrib=True)[0][:-1]
c = pd.DataFrame({"factor": X.columns, "push": contrib}).assign(abs_push=lambda d: d["push"].abs())
c = c.sort_values("abs_push", ascending=False).head(8).sort_values("push")
fig = px.bar(c, x="push", y="factor", orientation="h", color=c["push"] > 0,
             color_discrete_map={True: "#c53030", False: "#2f855a"}, title="What pushes this borrower's risk up (red) or down (green)")
fig.update_layout(showlegend=False, xaxis_title="effect on risk (log-odds)", yaxis_title="", height=380)
st.plotly_chart(fig, width="stretch")
st.caption("Grades are matched to the average risk the model assigned to each LendingClub grade on 2014-15 loans.")
