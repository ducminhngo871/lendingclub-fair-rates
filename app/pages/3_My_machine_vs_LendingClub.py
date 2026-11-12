import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # lets pages import app/common.py

import plotly.express as px
import streamlit as st

from common import pct, result

st.set_page_config(page_title="My machine vs LendingClub", page_icon="🤖", layout="wide")
st.title("My machine vs LendingClub")
st.write("Both predict who will default on 2014-15 loans. My models only ever saw loans from 2007-2013.")

auc = result("auc_comparison.csv")
fig = px.bar(auc.sort_values("auc"), x="auc", y="score", orientation="h",
             color=auc.sort_values("auc")["score"].str.contains("mine"),
             color_discrete_map={True: "#2b6cb0", False: "#a0aec0"}, range_x=[0.5, 0.7], text_auto=".3f")
fig.update_layout(showlegend=False, title="Ranking power (AUC, higher is better; 0.5 = coin flip)", yaxis_title="", height=330)
st.plotly_chart(fig, width="stretch")

inc = result("incremental_information.csv")
st.subheader("Does my machine know something LendingClub does not?")
st.dataframe(inc.assign(cv_auc=inc["cv_auc"].round(4)).rename(columns={"inputs": "Information used", "cv_auc": "AUC (cross-validated)"}),
             hide_index=True, width="stretch")
st.caption("If 'Both together' beats each alone, the two see different parts of the truth.")

t1, t2, t3 = st.tabs(["Calibration", "Where we disagree", "What drives risk"])
with t1:
    d = result("decile_table_lgbm.csv")
    fig = px.line(d, x="mean_predicted_pd", y="actual_default_rate", markers=True,
                  title="When the model says X%, how often does it happen?")
    fig.add_shape(type="line", x0=0, y0=0, x1=0.4, y1=0.4, line=dict(dash="dash", color="gray"))
    fig.update_layout(xaxis_tickformat=".0%", yaxis_tickformat=".0%", xaxis_title="Predicted default probability",
                      yaxis_title="Actual default rate", height=420)
    st.plotly_chart(fig, width="stretch")
    st.caption("Points above the dashed line mean the model was too optimistic. 2014-15 loans defaulted more than 2007-13 loans, "
               "so the model under-predicts a little overall. That is what predicting the future looks like.")
with t2:
    dis = result("disagreements.csv")
    st.dataframe(dis.assign(actual_default_rate=dis["actual_default_rate"].map(pct), mean_interest_rate=dis["mean_interest_rate"].map(pct),
                            mean_model_pd=dis["mean_model_pd"].map(pct)),
                 hide_index=True, width="stretch")
    st.write("'Safe' = in the safest 30% of loans by that scorer, 'risky' = riskiest 30%. "
             "Where we disagree, **the actual default rate shows who was closer to right**.")
with t3:
    sh = result("shap_importance.csv").head(12).sort_values("mean_abs_shap")
    fig = px.bar(sh, x="mean_abs_shap", y="feature", orientation="h", hover_data=["direction"],
                 title="Biggest drivers of default risk (mean |SHAP|)")
    fig.update_layout(yaxis_title="", xaxis_title="average impact on risk", height=420)
    st.plotly_chart(fig, width="stretch")
