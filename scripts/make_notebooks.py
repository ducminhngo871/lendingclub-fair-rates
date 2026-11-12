"""Builds the three walk-through notebooks in notebooks/ (then run them: see docs/MENTOR_GUIDE.md)."""

from pathlib import Path

import nbformat as nbf

OUT = Path(__file__).resolve().parents[1] / "notebooks"
SETUP = 'import sys\nsys.path.insert(0, "../src")\nimport pandas as pd\nimport numpy as np\nimport plotly.express as px\nfrom lc_rates import config, data, features, finance, model\npd.options.display.float_format = "{:,.4f}".format'


def md(s):
    return nbf.v4.new_markdown_cell(s.strip())


def code(s):
    return nbf.v4.new_code_cell(s.strip())


def save(name, cells):
    nb = nbf.v4.new_notebook()
    nb.cells = cells
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nbf.write(nb, OUT / name)


# ----------------------------------------------------------------------------------------------
save("01_explore_data.ipynb", [
    md("""# 1. Exploring the loans (weeks 2-4)
**Question:** which borrowers fail to repay, and does LendingClub's interest rate follow that risk?

Each chart below answers one small question. For each, write one sentence of your own *before* reading the comment under it."""),
    code(SETUP),
    md("## The clean table\nOnly **finished** loans (Fully Paid or Charged Off) that have had **time to finish**. Look at the columns: which ones are known when a person applies, and which only appear after the loan has run?"),
    code("df = data.load_clean()\nprint(df.shape)\ndf.head()"),
    code("df.describe().T[['count', 'mean', 'min', 'max']]"),
    md("## Default rate by LendingClub grade"),
    code("""g = df.groupby('grade').agg(loans=('defaulted', 'size'), default_rate=('defaulted', 'mean'), interest_rate=('int_rate', 'mean')).reset_index()
fig = px.bar(g, x='grade', y='default_rate', text=g['default_rate'].map('{:.1%}'.format), title='Share of loans that defaulted, by grade')
fig.update_layout(yaxis_tickformat='.0%')
fig.show()
g"""),
    md("Default rises steadily from A to G, so the grade carries real information. The next question is whether the interest rate rises *enough*."),
    code("""df['fico_band'] = pd.cut(df['fico_mid'], [0, 680, 700, 720, 740, 760, 900], right=False, labels=['<680', '680-699', '700-719', '720-739', '740-759', '760+'])
df['income_quartile'] = pd.qcut(df['annual_inc'], 4, labels=['Q1 lowest', 'Q2', 'Q3', 'Q4 highest'])
for col in ['fico_band', 'income_quartile', 'purpose']:
    t = df.groupby(col, observed=True)['defaulted'].mean().reset_index()
    px.bar(t, x=col, y='defaulted', title=f'Default rate by {col}').update_layout(yaxis_tickformat='.0%').show()"""),
    md("""## The maturity trap
Many loans in the data are still being repaid ("Current"). Whatever you do with them distorts the default rate. Compare three ways of measuring it, by the year the loan was issued."""),
    code("""raw = pd.read_csv(config.ACCEPTED_RAW, usecols=['loan_status', 'issue_d']).dropna()
raw['year'] = raw['issue_d'].str[-4:].astype(int)
everyone = raw.assign(d=raw['loan_status'] == 'Charged Off').groupby('year')['d'].mean()
done = raw[raw['loan_status'].isin(['Fully Paid', 'Charged Off'])]
finished = done.assign(d=done['loan_status'] == 'Charged Off').groupby('year')['d'].mean()
matured = df.groupby('issue_year')['defaulted'].mean()
trap = pd.concat({'A. every loan, Current counted as fine': everyone, 'B. finished loans, no maturity rule': finished,
                  'C. only loans old enough to be finished (ours)': matured}, axis=1)
trap.index.name = 'year'
px.line(trap.reset_index().melt('year', var_name='method', value_name='default_rate'), x='year', y='default_rate', color='method', markers=True,
        title='Default rate by issue year, three ways').update_layout(yaxis_tickformat='.0%', legend_title='').show()
trap.round(3).T"""),
    md("""* **A** makes 2017-18 look very safe (1.8% in 2018) only because those loans have had no time to default.
* **B** throws away the "Current" loans, but loans that go bad are resolved early while healthy ones are still running, so the finished pool is full of defaults: 2016 looks like 23%. It also mixes 36- and 60-month loans, and 60-month loans default more.
* **C** keeps only loans whose last payment was due by the end of 2018. This is the only fair comparison. That is why the 2014-15 test set contains 36-month loans only.

Neither mistake raises an error: the code runs and the chart looks plausible. This is the kind of mistake that makes a good 'what I got wrong' paragraph in an essay."""),
    md("### Your turn\n1. Which purpose has the highest default rate? Does it surprise you?\n2. Is the 60-month default rate higher than the 36-month one? Why might that be?\n3. Pick any two columns and find a relationship we did not chart."),
])

# ----------------------------------------------------------------------------------------------
save("02_build_the_scoring_machine.ipynb", [
    md("""# 2. Building the scoring machine (weeks 5-7)
We train two models on **2007-2013** loans and judge them on **2014-15** loans, then compare with LendingClub's grade."""),
    code(SETUP),
    code("""from sklearn.metrics import roc_auc_score
df = data.load_clean()
train, test = data.split_train_test(df)
print(f'train {len(train):,} loans ({train.issue_year.min()}-{train.issue_year.max()}), test {len(test):,} loans ({test.issue_year.min()}-{test.issue_year.max()})')"""),
    md("## Step 1: the inputs\nThe model may only use what is known **at the moment of application**. It must never see the grade, the interest rate, or anything about repayment. Check that our feature list obeys this."),
    code("""X_train, X_test = features.build_features(train), features.build_features(test)
y_train, y_test = train['defaulted'].to_numpy(), test['defaulted'].to_numpy()
print(features.FEATURE_COLUMNS)
banned = set(config.LC_VERDICT_COLUMNS) | set(config.OUTCOME_COLUMNS) | {'installment'}
assert not banned & set(features.FEATURE_COLUMNS)
X_train.head()"""),
    md("`installment` is a trap: it is calculated *from the interest rate*, so it would sneak LendingClub's own price into our 'independent' model."),
    md("## Model 1: logistic regression (explainable)"),
    code("""logit = model.make_logistic().fit(X_train, y_train)
p_logit = model.predict_pd(logit, X_test)
print('AUC', round(roc_auc_score(y_test, p_logit), 4))
model.logistic_coefficients(logit).head(12)"""),
    md("A coefficient above 0 pushes risk up; below 0 pushes it down. Numeric inputs are standardised, so coefficients are comparable."),
    md("## Model 2: LightGBM (stronger)\nTraining takes about a minute, so we load the one saved by `scripts/train.py`."),
    code("""logit, lgbm, meta = model.load_models()
p_lgbm = model.predict_pd(lgbm, X_test)
print('trees used:', meta['best_iteration'])
model.probability_quality(y_test, p_lgbm)"""),
    md("## Step 3: against LendingClub\nAUC asks: pick one borrower who defaulted and one who did not; how often does the score rank the defaulter as riskier? 0.5 is a coin flip."),
    code("""scores = {
    'Logistic (mine)': p_logit, 'LightGBM (mine)': p_lgbm,
    'LendingClub grade': model.grade_to_score(test['grade']).to_numpy(),
    'LendingClub sub-grade': model.sub_grade_to_score(test['sub_grade']).to_numpy(),
    'LendingClub interest rate': test['int_rate'].to_numpy(),
}
auc = model.score_summary(y_test, scores)
px.bar(auc.sort_values('auc'), x='auc', y='score', orientation='h', range_x=[0.5, 0.7], text_auto='.3f').show()
auc"""),
    md("LendingClub's finer sub-grade edges out my model: it sees credit-bureau details my 15 inputs do not. But is that the end of the story?"),
    code("""res = pd.read_csv(config.RESULTS_DIR / 'incremental_information.csv')
res"""),
    md("Using **both** beats either alone: my machine knows something LendingClub's grade does not. Where exactly do they disagree?"),
    code("model.disagreement_table(test, p_lgbm)"),
    md("## Is the probability itself right? (calibration)"),
    code("""d = model.decile_table(y_test, p_lgbm)
fig = px.line(d, x='mean_predicted_pd', y='actual_default_rate', markers=True, title='Predicted vs actual default rate')
fig.add_shape(type='line', x0=0, y0=0, x1=0.4, y1=0.4, line=dict(dash='dash'))
fig.update_layout(xaxis_tickformat='.0%', yaxis_tickformat='.0%').show()
d"""),
    md("## Why did it say that? (SHAP)"),
    code("""imp, values, Xs = model.shap_importance(lgbm, X_test, sample=5000)
px.bar(imp.head(12).sort_values('mean_abs_shap'), x='mean_abs_shap', y='feature', orientation='h').show()
imp.head(8)"""),
    md("### Your turn\n1. Add one more feature (for example `mort_acc` from the raw file) and see whether AUC improves. Remember to check it is known at application time.\n2. What happens to AUC if you *wrongly* add `int_rate` as an input? Explain why that would be cheating.\n3. The model under-predicts default overall. Why might 2014-15 differ from 2007-13?"),
])

# ----------------------------------------------------------------------------------------------
save("03_fair_rates_investing_rejections.ipynb", [
    md("""# 3. Fair rates, investing, and the people who were turned away (weeks 8-9)"""),
    code(SETUP),
    code("df = data.load_clean()\ntrain, test = data.split_train_test(df)\nlogit, lgbm, meta = model.load_models()\np = model.predict_pd(lgbm, features.build_features(test))\nlgd = meta['lgd']\nprint('Loss given default:', round(lgd, 3))"),
    md("""## Expected loss
`expected loss = chance of default × share lost when it happens × amount lent`

Example from the brief: lend $10,000, 10% chance of default, 60% lost → expected loss **$600**."""),
    code("finance.expected_loss(0.10, 0.60, 10_000)"),
    md("## Does each grade's interest pay for its losses?\nThe last column is what lenders **actually earned per year** (IRR of the real cash flows) after defaults."),
    code("finance.grade_economics(test, lgd)"),
    md("""## The fair rate
`fair rate = risk-free rate + required margin + yearly expected loss`

This is a simplified teaching formula. Change the assumptions and watch the answer move: that sensitivity is part of the finding."""),
    code("""t = test.assign(model_pd=p)
t['fair_rate'] = finance.fair_rate(t['model_pd'], t['term_months'], lgd)
t['gap'] = t['int_rate'] / 100 - t['fair_rate']
by_grade = t.groupby('grade').agg(charged=('int_rate', lambda s: s.mean() / 100), fair=('fair_rate', 'mean'), gap=('gap', 'mean')).reset_index()
px.bar(by_grade.melt('grade', ['charged', 'fair']), x='grade', y='value', color='variable', barmode='group').update_layout(yaxis_tickformat='.0%').show()
by_grade"""),
    md("The model-based fair rate **understates risk for the riskiest grades**, because the model's probabilities are squeezed toward the middle. The report also checks it against what lenders really earned. Compare:"),
    code("pd.read_csv(config.RESULTS_DIR / 'fair_rate_gaps.csv').query(\"segment == 'grade'\")[['value', 'mean_interest_rate', 'mean_fair_rate', 'fair_rate_from_realised_return', 'realised_annual_return']]"),
    md("## Investing: five strategies on loans nobody had seen"),
    code("""ret_model = model.load_return_model()
pred = ret_model.predict(model.return_features(test))
s = finance.compare_strategies(test, p, share=0.2, n_boot=20, pred_return=pred)
s[['strategy', 'loans', 'annual_return', 'ci95_low', 'ci95_high', 'default_rate', 'mean_interest_rate']]"""),
    md("### Design your own rule\nChange the mask below and see if you can beat the table. Be honest: tuning a rule on the same loans you judge it on is how people fool themselves. Decide your rule first, test it once."),
    code("""mask = (test['grade'].isin(['B', 'C'])) & (test['dti'] < 15)   # <- edit me
sel = test[mask]
print(len(sel), 'loans | return', round(finance.pool_irr(sel), 4), '| default rate', round(sel['defaulted'].mean(), 3))"""),
    md("""## The people who were turned away
Only 7.6% of applications were approved. Counts are pre-computed in `app/data/approval_cube.parquet`."""),
    code("""from lc_rates import rejected
cube = pd.read_parquet(config.APP_DATA_DIR / 'approval_cube.parquet')
early = cube[cube['year'].between(2008, 2013)]
rejected.approval_rate(early, 'risk_bin')"""),
    code("rejected.approval_rate(early, 'dti_bin')"),
    md("There is a wall at a risk score of 660 and another at a debt-to-income of 40%. **Careful:** this shows a difference, not why LendingClub decided. Also check what is missing: the rejected file has no income column, and the score scale changes after 2013."),
    md("### Your turn\n1. Which states have the lowest approval rates? Is that a fairness problem or a mix of applicants?\n2. Why do applications with debt-to-income of 0-10% have a *lower* approval rate than 10-20%? (Hint: look at how many have no risk score.)"),
])
print("wrote", *(p.name for p in sorted(OUT.glob("*.ipynb"))))
