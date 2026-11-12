# Does LendingClub charge fair interest?

A data project on **2.26 million real loans** (LendingClub, USA, 2007-2018): does the interest rate match each
borrower's risk? It builds a borrower-scoring model, compares it with LendingClub's A-G grades, works out a "fair"
rate, tests investing strategies on loans the models never saw, and looks at the 27.6 million applications that were
rejected. Everything ends in an interactive web app.

* **Report:** [`report/report.md`](report/report.md) (English, every finding has a number)
* **Live web app:** https://lendingclub-fair-rates-xf37oc9po9tl399n2mnyah.streamlit.app/ (or run locally: `streamlit run app/streamlit_app.py`)
* **Related project:** [Stock price prediction app](https://stockpriceprediction-ducngo.streamlit.app/)
* **Mentors:** [`docs/MENTOR_GUIDE.md`](docs/MENTOR_GUIDE.md) maps the 14 weeks to the code and lists the traps
* **Original brief (Vietnamese):** [`docs/project_brief_vi.md`](docs/project_brief_vi.md)

## Headline results (loans issued 2014-15, models trained on 2007-2013 only)

| Question | Answer |
| --- | --- |
| Can my model rank default risk like LendingClub? | AUC **0.662** vs 0.661 (grade A-G) and 0.671 (sub-grade A1-G5) |
| Does it add anything? | Using both together reaches **0.684**, better than either alone |
| Does interest cover the losses? | Lenders earned 6.3-7.5% a year on grades A-D but only 4.4% on E and F |
| Best investing rule? | Picking the best 10% by predicted return: **9.1% a year vs 6.8%** for funding every loan |
| Worst investing rule? | Chasing the highest interest rates: 6.3% |
| Who was rejected? | Almost nobody below a risk score of 660 or above 40% debt-to-income was approved |

AUC measures how well a score separates people who repay from people who default (0.5 = coin flip). Return is the yearly
internal rate of return of the pooled cash flows. See the report for assumptions and limits.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
bash scripts/run_all.sh            # download, clean, train, analyse, test (about 15 minutes)
streamlit run app/streamlit_app.py
```

You need a free [Kaggle API token](https://www.kaggle.com/settings) saved as `~/.kaggle/access_token` (or the
`KAGGLE_API_TOKEN` variable). The raw data (about 650 MB compressed) and the token are never committed.

The repository already contains the trained models (`models/`), result tables and figures (`results/`) and the small
files the app reads (`app/data/`), so **you can run the app and tests without downloading anything**.

On a Mac without Homebrew, `import lightgbm` may fail with *libomp.dylib not found*; run `brew install libomp`.

## What is where

```
src/lc_rates/        data.py (cleaning)  features.py  model.py  finance.py  rejected.py  config.py
scripts/             download_data, prepare_data, train, build_rejected, analyze, build_app_data, run_all.sh
app/                 streamlit_app.py + pages/ (4 pages) + common.py + data/
notebooks/           01 explore, 02 build the scoring machine, 03 fair rates / investing / rejections
models/              trained logistic, LightGBM, return model
results/             tables (.csv) and figures/ (.png) used in the report
report/ docs/        research report, mentor guide, original brief
tests/               40 automatic checks, including opening every app page
```

## The four app pages

1. **Loan pricing:** enter a borrower; see default risk, the grade my model gives, and a fair rate.
2. **Investor sandbox:** choose your own rule for picking loans; see the return it would really have earned.
3. **My machine vs LendingClub:** AUC, calibration, where the two disagree, what drives risk.
4. **Who is rejected?:** approval rates by risk score, debt-to-income, amount, state and year.

## Method in five lines

1. Keep only loans that finished *and* had time to finish (Dec 2018 cutoff), so unfinished loans cannot make recent years look safe.
2. Predict default from 15 facts known at application. Never use grade, rate, `installment` or anything that happens after the loan starts.
3. Split by time: learn from 2007-2013, judge on 2014-2015.
4. Expected loss = chance of default × share lost when it happens × amount lent. Fair rate = risk-free + margin + yearly expected loss, checked against what lenders really earned.
5. Measure investing by the IRR of real cash flows, and judge selection rules on a held-out year as well as the test years.

## Checks

```bash
pytest -q          # 40 tests: cleaning rules, no data leakage, finance maths, models, every app page
ruff check .
```

## Deploy the app (Streamlit Community Cloud)

1. Push this folder to GitHub (the `.gitignore` already keeps raw data and tokens out).
2. On [share.streamlit.io](https://share.streamlit.io) choose the repository and set the main file to `app/streamlit_app.py`.
3. Paste the public link at the top of this README (done: see the live link above).

## Limits

LendingClub's sub-grade ranks risk slightly better than this model on its own. The rejected-applications file has no
income column and its risk score changes scale after 2013, so conclusions there are about *differences*, not causes.
Strategy returns come from one period and ignore fees and taxes. Educational project, not financial advice.

Data: LendingClub public dataset on [Kaggle](https://www.kaggle.com/wordsforthewise/lending-club).
