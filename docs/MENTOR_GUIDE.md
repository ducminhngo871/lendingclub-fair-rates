# Mentor guide

This repository is the **reference solution** to the 14-week project in `docs/project_brief_vi.md`
("Does the bank charge fair interest?"). Use it as an answer key, a source of checkpoints, and a map of
where the traps are. Do not hand it to the student on day one: the learning is in building it.

## How the pieces fit

```
data/raw  --prepare_data.py-->  data/processed/loans_clean.parquet
                                      |
        train.py  (logistic, LightGBM, return model)  --> models/
        build_rejected.py (27.6M rejected + all accepted -> small count tables)
        analyze.py (every table + figure)            --> results/
        build_app_data.py                             --> app/data/
                                      |
                        streamlit run app/streamlit_app.py
```

`scripts/run_all.sh` runs everything (about 15 minutes after the 650 MB download).

| Folder | What is in it | Student writes it in |
| --- | --- | --- |
| `src/lc_rates/data.py` | cleaning rules, time split | weeks 2, 5 |
| `src/lc_rates/features.py` | model inputs | week 5 |
| `src/lc_rates/model.py` | logistic, LightGBM, AUC, calibration, SHAP | weeks 5-7 |
| `src/lc_rates/finance.py` | returns, expected loss, fair rate, strategies | weeks 4, 8, 9 |
| `src/lc_rates/rejected.py` | approved vs rejected | week 9 |
| `notebooks/` | three walk-throughs with "Your turn" questions | weeks 3-9 |
| `app/` | the 4-page Streamlit app | weeks 10-12 |
| `tests/` | 40 automatic checks | week 12 |
| `report/report.md` | the research report | weeks 13-14 |

## Week by week

| Week | Student does | Look at | Checkpoint question to ask |
| --- | --- | --- | --- |
| 1 | VS Code, Python, Git, first repo | `README.md`, `.gitignore` | Why must the Kaggle key and the raw data stay out of GitHub? |
| 2 | Load, filter, save Parquet | `data.py`, `scripts/prepare_data.py` | How many loans are left after each filter, and why drop each group? |
| 3 | Charts of default rate | `notebooks/01_explore_data.ipynb` | What does the dashed line mean? Which factor separates best? |
| 4 | Returns by grade | `finance.realised_return`, `grade_economics` | Why is a 25% interest rate not a 25% return? |
| 5 | Features, time split, logistic | `features.py`, notebook 02 | Why train on 2007-13 and test on 2014-15 instead of a random split? |
| 6 | LightGBM | `model.train_lgbm` | What does early stopping prevent? Why validate on a *later* year? |
| 7 | AUC, calibration, SHAP | notebook 02, `results/` | Is my model better than LendingClub's grade? Where do we disagree, and who was right? |
| 8 | Expected loss, fair rate | `finance.fair_rate`, notebook 03 | What happens to the fair rate if the required margin changes? |
| 9 | Strategies, rejected applicants | `finance.compare_strategies`, `rejected.py` | Why should you decide your rule *before* looking at test results? |
| 10-12 | Streamlit app, tests, deploy | `app/`, `tests/` | Could someone with no coding background use page 1 unaided? |
| 13-14 | Report, README, 2-minute video | `report/report.md` | Does every finding carry one concrete number? |

Weeks 6, 9 and 12 are the heaviest. If the student is behind, the brief allows stretching to 16 weeks.

## The traps (the best teaching material in the project)

1. **Unfinished loans (right-censoring).** Loans still being repaid are not defaulted *yet*. Counting them as fine makes
   2018 look like a 1.8% default year; dropping them but ignoring maturity makes 2016 look like 23%, because bad loans
   resolve early while good ones are still running. `data.clean_accepted` keeps a loan only if its last payment was due
   by Dec 2018. Notebook 01 plots all three views side by side.
2. **Looking into the future (leakage).** `total_pymnt`, `recoveries`, `last_pymnt_d` exist only after the loan ran.
   Using them to predict default is accidental cheating. They are kept only to *measure* outcomes.
3. **Using LendingClub's answer as an input.** `grade`, `sub_grade`, `int_rate` are the benchmark, not features.
   `installment` is a hidden version of the rate (it is computed from it), so it is excluded too. A test enforces this.
4. **Random split instead of a time split.** A random split lets the model peek at the future. The data is split by
   issue year, and the test years only contain 36-month loans because 60-month loans from 2014-15 have not matured.
5. **A value that silently became zero.** In an early run of this reference solution, a missing "years at job"
   was turned into **0 years** by a one-line pandas bug. A unit test caught it. Ask the student to find a case where a
   missing value could be mistaken for a real one; it makes a good "mistakes I made" paragraph.
6. **Interest rate is not return.** Borrowers repay principal every month, so a lender's money is not tied up for the
   whole term. The project measures return as the IRR of the pooled cash flows (`finance.pool_irr`), not profit divided by
   amount lent, which would understate returns.
7. **Tuning on the test set.** The investing sweep reports a held-out year *and* the test years, and the 10% pool size was
   fixed beforehand. A rule picked because it looked best on the test years is not evidence of skill.
8. **The rejected file is a different dataset.** It has no income. Its risk score has a different scale after 2013 and is
   missing for much of 2015 and 2018. Debt-to-income is negative or absurd for some rows. Only claim *differences*, never
   *causes*.
9. **The fair-rate formula is a simplification.** It spreads expected loss evenly over the loan; real defaults come
   early and also cost the interest that would have followed. The report therefore shows three fair-rate views and says
   which one to trust. Good students will find the mismatch themselves.

## Setup notes

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

* **Mac without Homebrew:** `import lightgbm` can fail with "libomp.dylib not found". Fix: `brew install libomp`.
* **Kaggle token:** Kaggle -> Settings -> API -> *Create New Token*. Save it as `~/.kaggle/access_token` or set
  `KAGGLE_API_TOKEN`. `scripts/download_data.py` does the rest.
* **8 GB laptop:** all scripts read only the columns they need. Reading the rejected file takes a few minutes and uses
  chunks; it does not need much memory.
* To rebuild the notebooks: `python scripts/make_notebooks.py`, then run them with
  `jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb`.

## Mapping to the completion checklist

| Checklist item | Where it is satisfied |
| --- | --- |
| Only finished, matured loans | `data.clean_accepted`, `tests/test_data.py` |
| No look-ahead columns in the model | `features.py`, `tests/test_features.py` |
| Every chart has title, units and a sentence | `results/figures/`, `report/report.md` |
| Time-based split | `data.split_train_test`, `scripts/train.py` |
| Table: my machine vs A-G | `results/auc_comparison.csv`, app page 3 |
| 5 strongest risk factors explained | `results/shap_importance.csv` |
| 4 pages, public link | `app/`; deploy `app/streamlit_app.py` on Streamlit Community Cloud |
| Automatic tests, app runs | `tests/` (includes opening every page) |
| English report with "mistakes" section | `report/report.md` |
| README with run instructions | `README.md` |

## Honest limits to tell the student

* LendingClub's sub-grade ranks default risk slightly **better** than the student's model, because it sees more
  credit-bureau detail. Combining both is better than either. Do not hide this: it is the real finding.
* The strategy results come from one period (2014-15) and ignore fees, taxes and the fact that good loans may have been
  filled by other investors first. They show what the data says, not what would happen next.
* The model under-predicts default a little because 2014-15 borrowers defaulted more than 2007-13 borrowers. That is
  what "predicting the future" looks like.
